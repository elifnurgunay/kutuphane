import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { Card, EmptyState, ErrorMessage, Field, LoadingState } from "../../components/ui";
import { formatDate } from "../../lib/format";
import { errorMessage, inputClass, secondaryButton } from "../../lib/ui";
import { RESERVATION_STATUS_LABELS } from "../members/api";
import { findMemberByNo } from "../loans/api";
import { useCreateReservation, useReservations } from "./api";

const ACTIVE = ["waiting", "ready"];

/** Kitap detayındaki rezervasyon kuyruğu ve yeni rezervasyon formu. */
export function BookReservationsSection({
  bookId,
  canReserve,
}: {
  bookId: number;
  canReserve: boolean;
}) {
  const reservations = useReservations({ book_id: bookId, size: 100 });
  const create = useCreateReservation();
  const [memberNo, setMemberNo] = useState("");
  const [error, setError] = useState<string | null>(null);

  const queue = reservations.data?.items.filter((r) => ACTIVE.includes(r.status)) ?? [];

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const member = await findMemberByNo(memberNo);
      if (!member) {
        setError(`${memberNo.trim().toUpperCase()} numaralı üye bulunamadı.`);
        return;
      }
      await create.mutateAsync({ book_id: bookId, member_id: member.id });
      setMemberNo("");
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <Card>
      <h2 className="text-lg font-semibold text-brand">Rezervasyon kuyruğu</h2>
      {reservations.isPending ? (
        <LoadingState />
      ) : reservations.error ? (
        <ErrorMessage error={reservations.error} />
      ) : queue.length === 0 ? (
        <EmptyState>Bekleyen rezervasyon yok.</EmptyState>
      ) : (
        <ol className="mt-2 divide-y divide-sage/40 text-sm">
          {queue.map((r) => (
            <li key={r.id} className="flex flex-wrap justify-between gap-2 py-2">
              <span>
                {r.status === "waiting" ? `${r.queue_position}. ` : ""}
                <Link to={`/uyeler/${r.member_id}`} className="text-brand">
                  {r.member_name}
                </Link>{" "}
                <span className="font-mono text-xs text-ink/70">{r.member_no}</span>
              </span>
              <span>
                {RESERVATION_STATUS_LABELS[r.status]}
                {r.status === "ready"
                  ? ` · ${r.assigned_barcode} · son gün ${formatDate(r.expires_at)}`
                  : ` · ${formatDate(r.created_at)}`}
              </span>
            </li>
          ))}
        </ol>
      )}

      {canReserve ? (
        <form
          onSubmit={(e) => void handleSubmit(e)}
          className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end"
        >
          <Field label="Üye numarası">
            <input
              value={memberNo}
              onChange={(e) => setMemberNo(e.target.value)}
              placeholder="UYE-000001"
              required
              className={inputClass}
            />
          </Field>
          <button type="submit" className={secondaryButton} disabled={create.isPending}>
            Rezerve et
          </button>
          {error && (
            <p
              role="alert"
              className="rounded bg-danger/10 px-3 py-2 text-sm text-danger sm:col-span-2"
            >
              {error}
            </p>
          )}
        </form>
      ) : (
        <p className="mt-3 text-sm text-ink/70">
          Müsait nüsha olduğu için rezervasyon yapılamaz; kitap doğrudan ödünç verilebilir.
        </p>
      )}
    </Card>
  );
}
