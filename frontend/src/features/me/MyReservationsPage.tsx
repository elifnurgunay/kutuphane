import { useState } from "react";
import { Card, EmptyState, ErrorMessage, LoadingState } from "../../components/ui";
import { formatDate } from "../../lib/format";
import { dangerButton, errorMessage } from "../../lib/ui";
import { RESERVATION_STATUS_LABELS } from "../members/api";
import { useCancelMyReservation, useMyReservations } from "./api";

const ACTIVE = ["waiting", "ready"];

export function MyReservationsPage() {
  const reservations = useMyReservations();
  const cancel = useCancelMyReservation();
  const [error, setError] = useState<string | null>(null);

  if (reservations.isPending) return <LoadingState />;
  if (reservations.error) return <ErrorMessage error={reservations.error} />;
  const active = reservations.data.filter((r) => ACTIVE.includes(r.status));
  const past = reservations.data.filter((r) => !ACTIVE.includes(r.status));

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-brand">Rezervasyonlarım</h1>
      {error && (
        <p role="alert" className="rounded bg-danger/10 px-3 py-2 text-sm text-danger">
          {error}
        </p>
      )}
      <Card>
        <h2 className="text-lg font-semibold text-brand">Aktif</h2>
        {active.length === 0 ? (
          <EmptyState>
            Aktif rezervasyonunuz yok. Katalogdan ödünçteki kitapları rezerve edebilirsiniz.
          </EmptyState>
        ) : (
          <ul className="mt-2 divide-y divide-sage/40">
            {active.map((r) => (
              <li key={r.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div>
                  <p className="font-medium">{r.book_title}</p>
                  {r.status === "ready" ? (
                    <p className="text-sm text-leaf">
                      Kitabınız hazır! {formatDate(r.expires_at)} tarihine kadar kütüphaneden teslim
                      alın.
                    </p>
                  ) : (
                    <p className="text-sm text-ink/70">
                      Sıranız: {r.queue_position} · {formatDate(r.created_at)}
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  className={dangerButton}
                  disabled={cancel.isPending}
                  onClick={() => {
                    if (!window.confirm(`"${r.book_title}" rezervasyonunuz iptal edilsin mi?`))
                      return;
                    setError(null);
                    cancel.mutate(r.id, { onError: (e) => setError(errorMessage(e)) });
                  }}
                >
                  İptal et
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>
      <Card>
        <h2 className="text-lg font-semibold text-brand">Geçmiş</h2>
        {past.length === 0 ? (
          <EmptyState>Geçmiş rezervasyon yok.</EmptyState>
        ) : (
          <ul className="mt-2 divide-y divide-sage/40 text-sm">
            {past.map((r) => (
              <li key={r.id} className="flex justify-between py-2">
                <span>{r.book_title}</span>
                <span className="text-ink/70">
                  {RESERVATION_STATUS_LABELS[r.status]} · {formatDate(r.created_at)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
