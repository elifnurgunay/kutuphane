import { useState } from "react";
import type { FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { Card, EmptyState, ErrorMessage, LoadingState, Pagination } from "../../components/ui";
import { errorMessage, inputClass, primaryButton, secondaryButton } from "../../lib/ui";
import { useBooks, useCategories, type BookSummary } from "../books/api";
import { useMyReservations, useReserveBook } from "./api";

const PAGE_SIZE = 20;

export function CatalogPage() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? undefined;
  const category = params.get("kategori") ? Number(params.get("kategori")) : undefined;
  const page = Number(params.get("sayfa") ?? 1);
  const [search, setSearch] = useState(q ?? "");
  const books = useBooks({ q, category, page, size: PAGE_SIZE });
  const categories = useCategories();
  const reservations = useMyReservations();
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const reservedBookIds = new Set(
    reservations.data
      ?.filter((r) => r.status === "waiting" || r.status === "ready")
      .map((r) => r.book_id),
  );

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
      <h1 className="text-xl font-semibold text-brand">Katalog</h1>
      <Card>
        <form onSubmit={handleSearch} className="grid gap-3 md:grid-cols-[2fr_1fr_auto]">
          <input
            type="search"
            placeholder="Başlık, yazar veya ISBN ara"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={inputClass}
          />
          <select
            value={category ?? ""}
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
          <button type="submit" className={primaryButton}>
            Ara
          </button>
        </form>
      </Card>

      {message && (
        <p
          role={message.ok ? "status" : "alert"}
          className={`rounded px-3 py-2 text-sm ${message.ok ? "bg-leaf/10 text-leaf" : "bg-danger/10 text-danger"}`}
        >
          {message.text}
        </p>
      )}

      <Card>
        <ErrorMessage error={books.error} />
        {books.isPending ? (
          <LoadingState />
        ) : books.data && books.data.items.length === 0 ? (
          <EmptyState>Aramanıza uyan kitap bulunamadı.</EmptyState>
        ) : books.data ? (
          <>
            <ul className="divide-y divide-sage/40">
              {books.data.items.map((book) => (
                <CatalogItem
                  key={book.id}
                  book={book}
                  alreadyReserved={reservedBookIds.has(book.id)}
                  onMessage={setMessage}
                />
              ))}
            </ul>
            <Pagination
              page={books.data.page}
              size={books.data.size}
              total={books.data.total}
              onChange={(p) => update({ sayfa: String(p) })}
            />
          </>
        ) : null}
      </Card>
    </div>
  );
}

function CatalogItem({
  book,
  alreadyReserved,
  onMessage,
}: {
  book: BookSummary;
  alreadyReserved: boolean;
  onMessage: (message: { ok: boolean; text: string }) => void;
}) {
  const reserve = useReserveBook();
  const available = book.available_count > 0;

  return (
    <li className="flex flex-wrap items-center justify-between gap-3 py-3">
      <div>
        <p className="font-medium">{book.title}</p>
        <p className="text-sm text-ink/70">
          {book.authors.map((a) => a.full_name).join(", ")}
          {book.publish_year ? ` · ${book.publish_year}` : ""}
          {book.publisher ? ` · ${book.publisher.name}` : ""}
        </p>
      </div>
      <div className="flex items-center gap-3">
        {available ? (
          <span className="rounded bg-leaf px-2 py-0.5 text-xs text-white">
            Müsait ({book.available_count})
          </span>
        ) : (
          <span className="rounded border border-sage bg-cream px-2 py-0.5 text-xs text-brand">
            Şu an ödünçte
          </span>
        )}
        {!available &&
          (alreadyReserved ? (
            <span className="text-sm text-leaf">Rezervasyonunuz var</span>
          ) : (
            <button
              type="button"
              className={secondaryButton}
              disabled={reserve.isPending}
              onClick={() =>
                reserve.mutate(book.id, {
                  onSuccess: (r) =>
                    onMessage({
                      ok: true,
                      text: `"${book.title}" için rezervasyon yapıldı. Sıranız: ${r.queue_position}.`,
                    }),
                  onError: (error) => onMessage({ ok: false, text: errorMessage(error) }),
                })
              }
            >
              Rezerve et
            </button>
          ))}
      </div>
    </li>
  );
}
