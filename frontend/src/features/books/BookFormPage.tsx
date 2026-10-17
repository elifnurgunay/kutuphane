import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Card, ErrorMessage, Field, LoadingState } from "../../components/ui";
import { inputClass, outlineButton, primaryButton } from "../../lib/ui";
import {
  useAuthors,
  useBook,
  useCategories,
  useCreateAuthor,
  useCreatePublisher,
  usePublishers,
  useSaveBook,
  type BookDetail,
  type BookInput,
} from "./api";

interface FormState {
  isbn: string;
  title: string;
  subtitle: string;
  publisherId: string;
  publishYear: string;
  pageCount: string;
  language: string;
  description: string;
  authorIds: number[];
  categoryIds: number[];
}

function initialState(book?: BookDetail): FormState {
  return {
    isbn: book?.isbn ?? "",
    title: book?.title ?? "",
    subtitle: book?.subtitle ?? "",
    publisherId: book?.publisher ? String(book.publisher.id) : "",
    publishYear: book?.publish_year ? String(book.publish_year) : "",
    pageCount: book?.page_count ? String(book.page_count) : "",
    language: book?.language ?? "Türkçe",
    description: book?.description ?? "",
    authorIds: book?.authors.map((a) => a.id) ?? [],
    categoryIds: book?.categories.map((c) => c.id) ?? [],
  };
}

function orNull(value: string): string | null {
  return value.trim() || null;
}

function numberOrNull(value: string): number | null {
  return value.trim() ? Number(value) : null;
}

export function BookFormPage() {
  const { id } = useParams();
  const bookId = id ? Number(id) : undefined;
  const book = useBook(bookId);

  if (bookId && book.isPending) return <LoadingState />;
  if (bookId && book.error) return <ErrorMessage error={book.error} />;
  return <BookForm key={bookId ?? "new"} bookId={bookId} book={book.data} />;
}

function BookForm({ bookId, book }: { bookId?: number; book?: BookDetail }) {
  const navigate = useNavigate();
  const [form, setForm] = useState(() => initialState(book));
  const [validation, setValidation] = useState<string | null>(null);
  const saveBook = useSaveBook(bookId);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (form.authorIds.length === 0 || form.categoryIds.length === 0) {
      setValidation("En az bir yazar ve bir kategori seçin.");
      return;
    }
    setValidation(null);
    const input: BookInput = {
      isbn: orNull(form.isbn),
      title: form.title.trim(),
      subtitle: orNull(form.subtitle),
      publisher_id: form.publisherId ? Number(form.publisherId) : null,
      publish_year: numberOrNull(form.publishYear),
      page_count: numberOrNull(form.pageCount),
      language: orNull(form.language),
      description: orNull(form.description),
      cover_url: book?.cover_url ?? null,
      author_ids: form.authorIds,
      category_ids: form.categoryIds,
    };
    const saved = await saveBook.mutateAsync(input);
    navigate(`/kitaplar/${saved.id}`, { replace: true });
  }

  return (
    <div className="space-y-4">
      <Link to={bookId ? `/kitaplar/${bookId}` : "/kitaplar"} className="text-sm text-leaf">
        ← Geri
      </Link>
      <Card>
        <h1 className="text-xl font-semibold text-brand">
          {bookId ? "Kitabı düzenle" : "Yeni kitap"}
        </h1>
        <form
          onSubmit={(e) => void handleSubmit(e).catch(() => undefined)}
          className="mt-4 space-y-4"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Başlık *">
              <input
                required
                value={form.title}
                onChange={(e) => set("title", e.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="Alt başlık">
              <input
                value={form.subtitle}
                onChange={(e) => set("subtitle", e.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="ISBN">
              <input
                value={form.isbn}
                onChange={(e) => set("isbn", e.target.value)}
                placeholder="978-975-07-1938-7"
                className={inputClass}
              />
            </Field>
            <PublisherField
              value={form.publisherId}
              onChange={(value) => set("publisherId", value)}
            />
            <Field label="Yayın yılı">
              <input
                type="number"
                value={form.publishYear}
                onChange={(e) => set("publishYear", e.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="Sayfa sayısı">
              <input
                type="number"
                min={1}
                value={form.pageCount}
                onChange={(e) => set("pageCount", e.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="Dil">
              <input
                value={form.language}
                onChange={(e) => set("language", e.target.value)}
                className={inputClass}
              />
            </Field>
          </div>

          <AuthorPicker selected={form.authorIds} onChange={(ids) => set("authorIds", ids)} />
          <CategoryPicker selected={form.categoryIds} onChange={(ids) => set("categoryIds", ids)} />

          <Field label="Açıklama">
            <textarea
              rows={4}
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
              className={inputClass}
            />
          </Field>

          {validation && (
            <p role="alert" className="rounded bg-danger/10 px-3 py-2 text-sm text-danger">
              {validation}
            </p>
          )}
          <ErrorMessage error={saveBook.error} />
          <button type="submit" className={primaryButton} disabled={saveBook.isPending}>
            {saveBook.isPending ? "Kaydediliyor…" : "Kaydet"}
          </button>
        </form>
      </Card>
    </div>
  );
}

function PublisherField({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const publishers = usePublishers();
  const createPublisher = useCreatePublisher();
  const [newName, setNewName] = useState("");

  async function handleCreate() {
    if (!newName.trim()) return;
    const publisher = await createPublisher.mutateAsync(newName.trim());
    onChange(String(publisher.id));
    setNewName("");
  }

  return (
    <div className="space-y-2">
      <Field label="Yayınevi">
        <select value={value} onChange={(e) => onChange(e.target.value)} className={inputClass}>
          <option value="">Seçilmedi</option>
          {publishers.data?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </Field>
      <div className="flex gap-2">
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="Listede yoksa yeni yayınevi"
          className={inputClass}
        />
        <button
          type="button"
          className={outlineButton}
          disabled={createPublisher.isPending}
          onClick={() => void handleCreate().catch(() => undefined)}
        >
          Ekle
        </button>
      </div>
      <ErrorMessage error={createPublisher.error} />
    </div>
  );
}

function AuthorPicker({
  selected,
  onChange,
}: {
  selected: number[];
  onChange: (ids: number[]) => void;
}) {
  const authors = useAuthors();
  const createAuthor = useCreateAuthor();
  const [filter, setFilter] = useState("");

  const byId = new Map(authors.data?.map((a) => [a.id, a]));
  const term = filter.trim().toLocaleLowerCase("tr");
  const matches = term
    ? (authors.data ?? [])
        .filter((a) => !selected.includes(a.id))
        .filter((a) => a.full_name.toLocaleLowerCase("tr").includes(term))
        .slice(0, 8)
    : [];

  async function handleCreate() {
    const author = await createAuthor.mutateAsync(filter.trim());
    onChange([...selected, author.id]);
    setFilter("");
  }

  return (
    <div className="space-y-2">
      <span className="text-sm font-medium">Yazarlar *</span>
      <div className="flex flex-wrap gap-2">
        {selected.map((id) => (
          <span key={id} className="flex items-center gap-1 rounded bg-sage px-2 py-1 text-sm">
            {byId.get(id)?.full_name ?? `#${id}`}
            <button
              type="button"
              aria-label="Kaldır"
              onClick={() => onChange(selected.filter((x) => x !== id))}
              className="text-brand"
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <input
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Yazar ara…"
        className={inputClass}
      />
      {term && (
        <ul className="rounded border border-sage bg-surface">
          {matches.map((a) => (
            <li key={a.id}>
              <button
                type="button"
                className="w-full px-3 py-1.5 text-left hover:bg-sage/30"
                onClick={() => {
                  onChange([...selected, a.id]);
                  setFilter("");
                }}
              >
                {a.full_name}
              </button>
            </li>
          ))}
          <li>
            <button
              type="button"
              className="w-full px-3 py-1.5 text-left text-leaf hover:bg-sage/30"
              disabled={createAuthor.isPending}
              onClick={() => void handleCreate().catch(() => undefined)}
            >
              + "{filter.trim()}" adıyla yeni yazar ekle
            </button>
          </li>
        </ul>
      )}
      <ErrorMessage error={createAuthor.error} />
    </div>
  );
}

function CategoryPicker({
  selected,
  onChange,
}: {
  selected: number[];
  onChange: (ids: number[]) => void;
}) {
  const categories = useCategories();
  const toggle = (id: number) =>
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);

  return (
    <fieldset className="space-y-2">
      <legend className="text-sm font-medium">Kategoriler *</legend>
      <div className="flex flex-wrap gap-x-4 gap-y-2">
        {categories.data?.map((c) => (
          <label key={c.id} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              className="accent-leaf"
              checked={selected.includes(c.id)}
              onChange={() => toggle(c.id)}
            />
            {c.name}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
