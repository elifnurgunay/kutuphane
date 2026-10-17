import { useState } from "react";
import type { FormEvent } from "react";
import { EmptyState, LoadingState } from "../../components/ui";
import { inputClass, outlineButton } from "../../lib/ui";
import { useBooks, useCopies, type BookSummary } from "../books/api";
import { CopyStatusBadge } from "../books/CopyStatusBadge";

const RESULT_LIMIT = 5;

/** Barkodu bilinmeyen kitap için: adla ara, nüshaya tıklayınca okutulmuş gibi işle. */
export function BarcodeFinder({ onPick }: { onPick: (barcode: string) => void }) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [query, setQuery] = useState("");
  const books = useBooks({ q: query, size: RESULT_LIMIT }, open && query !== "");

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    setQuery(text.trim());
  }

  if (!open) {
    return (
      <button
        type="button"
        className="text-sm text-leaf hover:underline"
        onClick={() => setOpen(true)}
      >
        Barkodu bilmiyor musunuz? Kitap adıyla bulun
      </button>
    );
  }

  return (
    <div className="space-y-3 rounded-lg border border-sage/70 bg-cream/40 p-3">
      <form onSubmit={handleSearch} className="flex flex-wrap gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Kitap adı, yazar veya ISBN"
          aria-label="Kitap ara"
          className={`${inputClass} flex-1`}
        />
        <button type="submit" className={outlineButton}>
          Ara
        </button>
        <button type="button" className={outlineButton} onClick={() => setOpen(false)}>
          Kapat
        </button>
      </form>
      {query &&
        (books.isPending ? (
          <LoadingState />
        ) : books.data && books.data.items.length === 0 ? (
          <EmptyState>Kitap bulunamadı.</EmptyState>
        ) : (
          <ul className="divide-y divide-sage/40">
            {books.data?.items.map((book) => (
              <BookCopies key={book.id} book={book} onPick={onPick} />
            ))}
          </ul>
        ))}
    </div>
  );
}

function BookCopies({ book, onPick }: { book: BookSummary; onPick: (barcode: string) => void }) {
  const copies = useCopies(book.id);
  return (
    <li className="py-2">
      <p className="text-sm font-medium">
        {book.title}{" "}
        <span className="font-normal text-ink/60">
          · {book.authors.map((a) => a.full_name).join(", ")}
        </span>
      </p>
      <div className="mt-1 flex flex-wrap gap-2">
        {copies.data?.map((copy) => (
          <button
            key={copy.id}
            type="button"
            onClick={() => onPick(copy.barcode)}
            title="Bu nüshayı okut"
            className="flex items-center gap-2 rounded-lg border border-sage bg-surface px-2 py-1 font-mono text-xs hover:bg-sage/25"
          >
            {copy.barcode}
            <CopyStatusBadge status={copy.status} />
          </button>
        ))}
      </div>
    </li>
  );
}
