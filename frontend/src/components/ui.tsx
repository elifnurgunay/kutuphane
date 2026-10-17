import { Inbox, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";
import { errorMessage, outlineButton } from "../lib/ui";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <section
      className={`rounded-xl border border-sage/70 bg-surface p-4 shadow-sm sm:p-6 ${className}`}
    >
      {children}
    </section>
  );
}

export function LoadingState() {
  return (
    <p className="flex items-center justify-center gap-2 py-8 text-ink/70" role="status">
      <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden />
      Yükleniyor…
    </p>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 py-8 text-center text-ink/60">
      <Inbox className="h-6 w-6 text-sage" aria-hidden />
      <p>{children}</p>
    </div>
  );
}

export function ErrorMessage({ error }: { error: unknown }) {
  if (!error) return null;
  return (
    <p role="alert" className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">
      {errorMessage(error)}
    </p>
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block space-y-1">
      <span className="text-sm font-medium text-ink/90">{label}</span>
      {children}
    </label>
  );
}

export function Pagination({
  page,
  size,
  total,
  onChange,
}: {
  page: number;
  size: number;
  total: number;
  onChange: (page: number) => void;
}) {
  const pageCount = Math.max(1, Math.ceil(total / size));
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 pt-4 text-sm">
      <span className="text-ink/70">Toplam {total} kayıt</span>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className={outlineButton}
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          Önceki
        </button>
        <span>
          Sayfa {page} / {pageCount}
        </span>
        <button
          type="button"
          className={outlineButton}
          disabled={page >= pageCount}
          onClick={() => onChange(page + 1)}
        >
          Sonraki
        </button>
      </div>
    </div>
  );
}
