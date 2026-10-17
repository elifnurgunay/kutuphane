import { useState } from "react";
import { useConfirm } from "../../lib/confirm";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Card, EmptyState, ErrorMessage, Field, LoadingState } from "../../components/ui";
import { formatDate } from "../../lib/format";
import {
  dangerButton,
  inputClass,
  outlineButton,
  primaryButton,
  secondaryButton,
} from "../../lib/ui";
import {
  COPY_STATUS_LABELS,
  MANUAL_COPY_STATUSES,
  useAddCopy,
  useBook,
  useCopies,
  useDeleteBook,
  useUpdateCopy,
  type Copy,
  type ManualCopyStatus,
} from "./api";
import { BookReservationsSection } from "../reservations/BookReservationsSection";
import { CopyStatusBadge } from "./CopyStatusBadge";

const LOCKED_STATUSES = ["loaned", "reserved"];

export function BookDetailPage() {
  const bookId = Number(useParams().id);
  const navigate = useNavigate();
  const book = useBook(bookId);
  const deleteBook = useDeleteBook();
  const confirm = useConfirm();

  if (book.isPending) return <LoadingState />;
  if (book.error) return <ErrorMessage error={book.error} />;
  const data = book.data;

  async function handleDelete() {
    const ok = await confirm({
      title: "Kitap silinsin mi?",
      message: `"${data.title}" ve tüm nüshaları kalıcı olarak silinecek.`,
      confirmLabel: "Sil",
      tone: "danger",
    });
    if (!ok) return;
    await deleteBook.mutateAsync(bookId);
    navigate("/kitaplar", { replace: true });
  }

  const details: [string, string | number | null][] = [
    ["ISBN", data.isbn],
    ["Yazar", data.authors.map((a) => a.full_name).join(", ")],
    ["Yayınevi", data.publisher?.name ?? null],
    ["Yayın yılı", data.publish_year],
    ["Sayfa sayısı", data.page_count],
    ["Dil", data.language],
    ["Kategoriler", data.categories.map((c) => c.name).join(", ")],
    ["Kayıt tarihi", formatDate(data.created_at)],
  ];

  return (
    <div className="space-y-4">
      <Link to="/kitaplar" className="text-sm text-leaf">
        ← Kitaplar
      </Link>
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold text-brand">{data.title}</h1>
            {data.subtitle && <p className="text-ink/70">{data.subtitle}</p>}
          </div>
          <div className="flex gap-2">
            <Link to={`/kitaplar/${bookId}/duzenle`} className={outlineButton}>
              Düzenle
            </Link>
            <button
              type="button"
              className={dangerButton}
              onClick={() => void handleDelete().catch(() => undefined)}
              disabled={deleteBook.isPending}
            >
              Sil
            </button>
          </div>
        </div>
        <div className="mt-3">
          <ErrorMessage error={deleteBook.error} />
        </div>
        <dl className="mt-4 grid gap-x-6 gap-y-2 sm:grid-cols-2">
          {details.map(([label, value]) => (
            <div key={label} className="flex gap-2">
              <dt className="w-32 shrink-0 text-sm text-ink/70">{label}</dt>
              <dd>{value || "—"}</dd>
            </div>
          ))}
        </dl>
        {data.description && <p className="mt-4 whitespace-pre-line">{data.description}</p>}
      </Card>

      <CopiesSection bookId={bookId} />
      <BookReservationsSection bookId={bookId} canReserve={data.available_count === 0} />
    </div>
  );
}

function CopiesSection({ bookId }: { bookId: number }) {
  const copies = useCopies(bookId);
  const addCopy = useAddCopy(bookId);
  const [shelf, setShelf] = useState("");
  const [acquiredAt, setAcquiredAt] = useState("");

  async function handleAdd(event: FormEvent) {
    event.preventDefault();
    await addCopy.mutateAsync({
      shelf_location: shelf.trim() || null,
      acquired_at: acquiredAt || null,
      notes: null,
    });
    setShelf("");
    setAcquiredAt("");
  }

  return (
    <Card>
      <h2 className="text-lg font-semibold text-brand">Nüshalar</h2>

      {copies.isPending ? (
        <LoadingState />
      ) : copies.error ? (
        <ErrorMessage error={copies.error} />
      ) : copies.data.length === 0 ? (
        <EmptyState>Bu kitabın henüz nüshası yok.</EmptyState>
      ) : (
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-sage text-brand">
              <tr>
                <th className="py-2 pr-4">Barkod</th>
                <th className="py-2 pr-4">Raf</th>
                <th className="py-2 pr-4">Durum</th>
                <th className="py-2 pr-4">Edinme</th>
                <th className="py-2 pr-4">Not</th>
                <th className="py-2" />
              </tr>
            </thead>
            <tbody>
              {copies.data.map((copy) => (
                <CopyRow key={copy.id} bookId={bookId} copy={copy} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      <form onSubmit={(e) => void handleAdd(e).catch(() => undefined)} className="mt-4 space-y-3">
        <h3 className="font-medium">Nüsha ekle</h3>
        <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
          <Field label="Raf konumu">
            <input
              value={shelf}
              onChange={(e) => setShelf(e.target.value)}
              placeholder="A-03-2"
              className={inputClass}
            />
          </Field>
          <Field label="Edinme tarihi">
            <input
              type="date"
              value={acquiredAt}
              onChange={(e) => setAcquiredAt(e.target.value)}
              className={inputClass}
            />
          </Field>
          <button type="submit" className={secondaryButton} disabled={addCopy.isPending}>
            Ekle (barkod otomatik)
          </button>
        </div>
        <ErrorMessage error={addCopy.error} />
      </form>
    </Card>
  );
}

function CopyRow({ bookId, copy }: { bookId: number; copy: Copy }) {
  const updateCopy = useUpdateCopy(bookId);
  const [editing, setEditing] = useState(false);
  const [shelf, setShelf] = useState(copy.shelf_location ?? "");
  const [notes, setNotes] = useState(copy.notes ?? "");
  const [status, setStatus] = useState<ManualCopyStatus | "">(
    LOCKED_STATUSES.includes(copy.status) ? "" : (copy.status as ManualCopyStatus),
  );
  const locked = LOCKED_STATUSES.includes(copy.status);

  async function handleSave() {
    await updateCopy.mutateAsync({
      id: copy.id,
      input: {
        shelf_location: shelf.trim() || null,
        notes: notes.trim() || null,
        acquired_at: copy.acquired_at,
        ...(status ? { status } : {}),
      },
    });
    setEditing(false);
  }

  if (!editing) {
    return (
      <tr className="border-b border-sage/40">
        <td className="py-2 pr-4 font-mono">{copy.barcode}</td>
        <td className="py-2 pr-4">{copy.shelf_location ?? "—"}</td>
        <td className="py-2 pr-4">
          <CopyStatusBadge status={copy.status} />
        </td>
        <td className="py-2 pr-4">{formatDate(copy.acquired_at)}</td>
        <td className="py-2 pr-4">{copy.notes ?? "—"}</td>
        <td className="py-2 text-right">
          <button type="button" className={outlineButton} onClick={() => setEditing(true)}>
            Düzenle
          </button>
        </td>
      </tr>
    );
  }

  return (
    <tr className="border-b border-sage/40 bg-sage/10">
      <td className="py-2 pr-4 font-mono">{copy.barcode}</td>
      <td className="py-2 pr-4">
        <input value={shelf} onChange={(e) => setShelf(e.target.value)} className={inputClass} />
      </td>
      <td className="py-2 pr-4">
        {locked ? (
          <span title="Ödünç/rezervasyon işlemleri yönetir">
            <CopyStatusBadge status={copy.status} />
          </span>
        ) : (
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as ManualCopyStatus)}
            className={inputClass}
          >
            {MANUAL_COPY_STATUSES.map((s) => (
              <option key={s} value={s}>
                {COPY_STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        )}
      </td>
      <td className="py-2 pr-4">{formatDate(copy.acquired_at)}</td>
      <td className="py-2 pr-4">
        <input value={notes} onChange={(e) => setNotes(e.target.value)} className={inputClass} />
      </td>
      <td className="space-y-1 py-2 text-right">
        <div className="flex justify-end gap-2">
          <button
            type="button"
            className={primaryButton}
            disabled={updateCopy.isPending}
            onClick={() => void handleSave().catch(() => undefined)}
          >
            Kaydet
          </button>
          <button type="button" className={outlineButton} onClick={() => setEditing(false)}>
            Vazgeç
          </button>
        </div>
        <ErrorMessage error={updateCopy.error} />
      </td>
    </tr>
  );
}
