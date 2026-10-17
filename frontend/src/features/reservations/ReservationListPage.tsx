import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Card, EmptyState, ErrorMessage, LoadingState, Pagination } from "../../components/ui";
import { formatDate } from "../../lib/format";
import { dangerButton, errorMessage } from "../../lib/ui";
import { RESERVATION_STATUS_LABELS, type ReservationStatus } from "../members/api";
import { useCancelReservation, useReservations, type Reservation } from "./api";

const PAGE_SIZE = 20;

const TABS: { value: ReservationStatus; label: string; empty: string }[] = [
  { value: "ready", label: "Hazır bekleyenler", empty: "Teslim alınmayı bekleyen kitap yok." },
  { value: "waiting", label: "Kuyruk", empty: "Kuyrukta bekleyen rezervasyon yok." },
  { value: "fulfilled", label: "Teslim edilen", empty: "Kayıt yok." },
  { value: "expired", label: "Süresi dolan", empty: "Kayıt yok." },
  { value: "cancelled", label: "İptal edilen", empty: "Kayıt yok." },
];

export function ReservationListPage() {
  const [params, setParams] = useSearchParams();
  const tab = (params.get("sekme") as ReservationStatus | null) ?? "ready";
  const page = Number(params.get("sayfa") ?? 1);
  const reservations = useReservations({ status: tab, page, size: PAGE_SIZE });
  const [message, setMessage] = useState<string | null>(null);
  const active = tab === "ready" || tab === "waiting";
  const current = TABS.find((t) => t.value === tab) ?? TABS[0];

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-brand">Rezervasyonlar</h1>
      <p className="text-sm text-ink/70">
        Yeni rezervasyon, müsait nüshası olmayan kitabın detay sayfasından yapılır.
      </p>

      <div role="tablist" className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t.value}
            type="button"
            role="tab"
            aria-selected={tab === t.value}
            onClick={() => {
              setMessage(null);
              setParams({ sekme: t.value });
            }}
            className={`rounded px-4 py-2 text-sm ${
              tab === t.value
                ? "bg-leaf text-white"
                : "border border-sage text-brand hover:bg-sage/30"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {message && (
        <p role="alert" className="rounded bg-danger/10 px-3 py-2 text-sm text-danger">
          {message}
        </p>
      )}

      <Card>
        <ErrorMessage error={reservations.error} />
        {reservations.isPending ? (
          <LoadingState />
        ) : reservations.data && reservations.data.items.length === 0 ? (
          <EmptyState>{current.empty}</EmptyState>
        ) : reservations.data ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-sage text-brand">
                  <tr>
                    <th className="py-2 pr-4">Kitap</th>
                    <th className="py-2 pr-4">Üye</th>
                    <th className="py-2 pr-4">Tarih</th>
                    {tab === "waiting" && <th className="py-2 pr-4">Sıra</th>}
                    {tab === "ready" && <th className="py-2 pr-4">Ayrılan nüsha</th>}
                    {tab === "ready" && <th className="py-2 pr-4">Son gün</th>}
                    {!active && <th className="py-2 pr-4">Durum</th>}
                    {active && <th className="py-2" />}
                  </tr>
                </thead>
                <tbody>
                  {reservations.data.items.map((r) => (
                    <ReservationRow key={r.id} reservation={r} tab={tab} onError={setMessage} />
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={reservations.data.page}
              size={reservations.data.size}
              total={reservations.data.total}
              onChange={(p) => setParams({ sekme: tab, sayfa: String(p) })}
            />
          </>
        ) : null}
      </Card>
    </div>
  );
}

function ReservationRow({
  reservation: r,
  tab,
  onError,
}: {
  reservation: Reservation;
  tab: ReservationStatus;
  onError: (message: string) => void;
}) {
  const cancel = useCancelReservation();
  const active = tab === "ready" || tab === "waiting";

  function handleCancel() {
    if (!window.confirm(`${r.member_name} adına "${r.book_title}" rezervasyonu iptal edilsin mi?`))
      return;
    cancel.mutate(r.id, { onError: (error) => onError(errorMessage(error)) });
  }

  return (
    <tr className="border-b border-sage/40">
      <td className="py-2 pr-4">
        <Link to={`/kitaplar/${r.book_id}`} className="text-brand">
          {r.book_title}
        </Link>
      </td>
      <td className="py-2 pr-4">
        <Link to={`/uyeler/${r.member_id}`} className="text-brand">
          {r.member_name}
        </Link>
        <div className="font-mono text-xs text-ink/70">{r.member_no}</div>
      </td>
      <td className="py-2 pr-4">{formatDate(r.created_at)}</td>
      {tab === "waiting" && <td className="py-2 pr-4">{r.queue_position}</td>}
      {tab === "ready" && <td className="py-2 pr-4 font-mono">{r.assigned_barcode ?? "—"}</td>}
      {tab === "ready" && <td className="py-2 pr-4">{formatDate(r.expires_at)}</td>}
      {!active && <td className="py-2 pr-4">{RESERVATION_STATUS_LABELS[r.status]}</td>}
      {active && (
        <td className="py-2 text-right">
          <button
            type="button"
            className={dangerButton}
            disabled={cancel.isPending}
            onClick={handleCancel}
          >
            İptal
          </button>
        </td>
      )}
    </tr>
  );
}
