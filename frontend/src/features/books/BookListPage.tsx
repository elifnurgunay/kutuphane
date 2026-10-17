import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Card, EmptyState, ErrorMessage, LoadingState, Pagination } from "../../components/ui";
import { inputClass, primaryButton } from "../../lib/ui";
import { useBooks, useCategories, type BookQuery } from "./api";

const PAGE_SIZE = 20;

const SORT_OPTIONS = [
  { value: "title", label: "Başlık (A-Z)" },
  { value: "-title", label: "Başlık (Z-A)" },
  { value: "-publish_year", label: "Yayın yılı (yeni)" },
  { value: "publish_year", label: "Yayın yılı (eski)" },
  { value: "-created_at", label: "Eklenme (yeni)" },
];

function readQuery(params: URLSearchParams): BookQuery {
  return {
    q: params.get("q") ?? undefined,
    category: params.get("kategori") ? Number(params.get("kategori")) : undefined,
    available: params.get("musait") === "1" ? true : undefined,
    sort: params.get("sirala") ?? "title",
    page: Number(params.get("sayfa") ?? 1),
    size: PAGE_SIZE,
  };
}

export function BookListPage() {
  const [params, setParams] = useSearchParams();
  const query = readQuery(params);
  const [search, setSearch] = useState(query.q ?? "");
  const books = useBooks(query);
  const categories = useCategories();

  function update(changes: Record<string, string | undefined>) {
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    if (!("sayfa" in changes)) next.delete("sayfa");
    setParams(next);
  }

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    update({ q: search.trim() || undefined });
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-semibold text-brand">Kitaplar</h1>
        <Link to="/kitaplar/yeni" className={primaryButton}>
          Yeni kitap
        </Link>
      </div>

      <Card>
        <form onSubmit={handleSearch} className="grid gap-3 md:grid-cols-[2fr_1fr_1fr_auto]">
          <input
            type="search"
            placeholder="Başlık, yazar veya ISBN ara"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={inputClass}
          />
          <select
            value={query.category ?? ""}
            onChange={(e) => update({ kategori: e.target.value || undefined })}
            className={inputClass}
            aria-label="Kategori"
          >
            <option value="">Tüm kategoriler</option>
            {categories.data?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <select
            value={query.sort}
            onChange={(e) => update({ sirala: e.target.value })}
            className={inputClass}
            aria-label="Sıralama"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <button type="submit" className={primaryButton}>
            Ara
          </button>
        </form>
        <label className="mt-3 flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={query.available === true}
            onChange={(e) => update({ musait: e.target.checked ? "1" : undefined })}
            className="accent-leaf"
          />
          Yalnızca müsait nüshası olanlar
        </label>
      </Card>

      <Card>
        <ErrorMessage error={books.error} />
        {books.isPending ? (
          <LoadingState />
        ) : books.data && books.data.items.length === 0 ? (
          <EmptyState>Aramanıza uyan kitap bulunamadı.</EmptyState>
        ) : books.data ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-sage text-brand">
                  <tr>
                    <th className="py-2 pr-4">Başlık</th>
                    <th className="py-2 pr-4">Yazar</th>
                    <th className="py-2 pr-4">Yayınevi</th>
                    <th className="py-2 pr-4">Yıl</th>
                    <th className="py-2">Müsait / Nüsha</th>
                  </tr>
                </thead>
                <tbody>
                  {books.data.items.map((book) => (
                    <tr key={book.id} className="border-b border-sage/40 hover:bg-sage/20">
                      <td className="py-2 pr-4">
                        <Link to={`/kitaplar/${book.id}`} className="font-medium text-brand">
                          {book.title}
                        </Link>
                      </td>
                      <td className="py-2 pr-4">
                        {book.authors.map((a) => a.full_name).join(", ")}
                      </td>
                      <td className="py-2 pr-4">{book.publisher?.name ?? "—"}</td>
                      <td className="py-2 pr-4">{book.publish_year ?? "—"}</td>
                      <td className="py-2">
                        <span
                          className={`rounded px-2 py-0.5 text-xs ${
                            book.available_count > 0
                              ? "bg-leaf text-white"
                              : "bg-cream text-brand border border-sage"
                          }`}
                        >
                          {book.available_count} / {book.copy_count}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={books.data.page}
              size={books.data.size}
              total={books.data.total}
              onChange={(page) => update({ sayfa: String(page) })}
            />
          </>
        ) : null}
      </Card>
    </div>
  );
}
