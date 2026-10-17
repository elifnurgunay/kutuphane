import { useState } from "react";
import { useConfirm } from "../../lib/confirm";
import { Link, useParams } from "react-router-dom";
import { Card, EmptyState, ErrorMessage, LoadingState } from "../../components/ui";
import { formatDate, formatMoney, todayIso } from "../../lib/format";
import { dangerButton, outlineButton, secondaryButton } from "../../lib/ui";
import {
  FINE_REASON_LABELS,
  FINE_STATUS_LABELS,
  MEMBER_TYPE_LABELS,
  RESERVATION_STATUS_LABELS,
  useMember,
  useMemberFines,
  useMemberLoans,
  useMemberReservations,
  useSetMemberStatus,
  type MemberLoan,
} from "./api";
import { LoanStatusBadge, MemberStatusBadge } from "./badges";
import { dueState } from "./dueState";

const OPEN_LOAN_STATUSES = ["active", "overdue"];

export function MemberDetailPage() {
  const memberId = Number(useParams().id);
  const member = useMember(memberId);
  const setStatus = useSetMemberStatus(memberId);
  const confirm = useConfirm();

  if (member.isPending) return <LoadingState />;
  if (member.error) return <ErrorMessage error={member.error} />;
  const data = member.data;

  async function changeStatus(action: "suspend" | "activate") {
    const suspend = action === "suspend";
    const ok = await confirm({
      title: suspend ? "Üye askıya alınsın mı?" : "Üye aktifleştirilsin mi?",
      message: suspend
        ? `${data.full_name} askıdayken kitap alamaz.`
        : `${data.full_name} yeniden kitap alabilecek.`,
      confirmLabel: suspend ? "Askıya al" : "Aktifleştir",
      tone: suspend ? "danger" : "default",
    });
    if (ok) setStatus.mutate(action);
  }

  const details: [string, string][] = [
    ["Üye no", data.member_no],
    ["E-posta", data.email],
    ["Telefon", data.phone ?? "—"],
    ["Adres", data.address ?? "—"],
    ["Üye tipi", MEMBER_TYPE_LABELS[data.member_type]],
    ["Üyelik", `${formatDate(data.membership_start)} – ${formatDate(data.membership_end)}`],
    ["Elindeki kitap", String(data.active_loan_count)],
    ["Ödenmemiş ceza", formatMoney(data.unpaid_fine_total)],
  ];

  return (
    <div className="space-y-4">
      <Link to="/uyeler" className="text-sm text-leaf">
        ← Üyeler
      </Link>
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-brand">{data.full_name}</h1>
            <MemberStatusBadge status={data.status} />
          </div>
          <div className="flex gap-2">
            <Link to={`/uyeler/${memberId}/duzenle`} className={outlineButton}>
              Düzenle
            </Link>
            {data.status === "active" ? (
              <button
                type="button"
                className={dangerButton}
                disabled={setStatus.isPending}
                onClick={() => void changeStatus("suspend")}
              >
                Askıya al
              </button>
            ) : (
              <button
                type="button"
                className={secondaryButton}
                disabled={setStatus.isPending}
                onClick={() => void changeStatus("activate")}
              >
                Aktifleştir
              </button>
            )}
          </div>
        </div>
        <div className="mt-3">
          <ErrorMessage error={setStatus.error} />
        </div>
        <dl className="mt-4 grid gap-x-6 gap-y-2 sm:grid-cols-2">
          {details.map(([label, value]) => (
            <div key={label} className="flex gap-2">
              <dt className="w-32 shrink-0 text-sm text-ink/70">{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      </Card>

      <LoansSection memberId={memberId} />
      <FinesSection memberId={memberId} />
      <ReservationsSection memberId={memberId} />
    </div>
  );
}

function LoanTable({ loans, today }: { loans: MemberLoan[]; today: string }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-sage text-brand">
          <tr>
            <th className="py-2 pr-4">Kitap</th>
            <th className="py-2 pr-4">Barkod</th>
            <th className="py-2 pr-4">Alış</th>
            <th className="py-2 pr-4">Son teslim</th>
            <th className="py-2 pr-4">İade</th>
            <th className="py-2">Durum</th>
          </tr>
        </thead>
        <tbody>
          {loans.map((loan) => {
            const open = OPEN_LOAN_STATUSES.includes(loan.status);
            return (
              <tr key={loan.id} className="border-b border-sage/40">
                <td className="py-2 pr-4">
                  <Link to={`/kitaplar/${loan.book_id}`} className="text-brand">
                    {loan.book_title}
                  </Link>
                </td>
                <td className="py-2 pr-4 font-mono">{loan.barcode}</td>
                <td className="py-2 pr-4">{formatDate(loan.loan_date)}</td>
                <td className="py-2 pr-4">{formatDate(loan.due_date)}</td>
                <td className="py-2 pr-4">{formatDate(loan.return_date)}</td>
                <td className="py-2">
                  <LoanStatusBadge
                    status={loan.status}
                    due={open ? dueState(loan.due_date, today) : undefined}
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function LoansSection({ memberId }: { memberId: number }) {
  const loans = useMemberLoans(memberId);
  const [showHistory, setShowHistory] = useState(false);
  const today = todayIso();

  if (loans.isPending) return <LoadingState />;
  if (loans.error) return <ErrorMessage error={loans.error} />;
  const open = loans.data.filter((l) => OPEN_LOAN_STATUSES.includes(l.status));
  const history = loans.data.filter((l) => !OPEN_LOAN_STATUSES.includes(l.status));

  return (
    <Card>
      <h2 className="text-lg font-semibold text-brand">Aktif ödünçler</h2>
      {open.length === 0 ? (
        <EmptyState>Üyenin elinde kitap yok.</EmptyState>
      ) : (
        <LoanTable loans={open} today={today} />
      )}

      <div className="mt-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-brand">Geçmiş ({history.length})</h2>
        {history.length > 0 && (
          <button type="button" className={outlineButton} onClick={() => setShowHistory((v) => !v)}>
            {showHistory ? "Gizle" : "Göster"}
          </button>
        )}
      </div>
      {history.length === 0 ? (
        <EmptyState>Geçmiş ödünç kaydı yok.</EmptyState>
      ) : (
        showHistory && <LoanTable loans={history} today={today} />
      )}
    </Card>
  );
}

function FinesSection({ memberId }: { memberId: number }) {
  const fines = useMemberFines(memberId);
  return (
    <Card>
      <h2 className="text-lg font-semibold text-brand">Cezalar</h2>
      {fines.isPending ? (
        <LoadingState />
      ) : fines.error ? (
        <ErrorMessage error={fines.error} />
      ) : fines.data.length === 0 ? (
        <EmptyState>Ceza kaydı yok.</EmptyState>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-sage text-brand">
              <tr>
                <th className="py-2 pr-4">Tarih</th>
                <th className="py-2 pr-4">Sebep</th>
                <th className="py-2 pr-4">Tutar</th>
                <th className="py-2">Durum</th>
              </tr>
            </thead>
            <tbody>
              {fines.data.map((fine) => (
                <tr key={fine.id} className="border-b border-sage/40">
                  <td className="py-2 pr-4">{formatDate(fine.created_at)}</td>
                  <td className="py-2 pr-4">{FINE_REASON_LABELS[fine.reason]}</td>
                  <td className="py-2 pr-4">{formatMoney(fine.amount)}</td>
                  <td className="py-2">{FINE_STATUS_LABELS[fine.status]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

function ReservationsSection({ memberId }: { memberId: number }) {
  const reservations = useMemberReservations(memberId);
  return (
    <Card>
      <h2 className="text-lg font-semibold text-brand">Rezervasyonlar</h2>
      {reservations.isPending ? (
        <LoadingState />
      ) : reservations.error ? (
        <ErrorMessage error={reservations.error} />
      ) : reservations.data.length === 0 ? (
        <EmptyState>Rezervasyon kaydı yok.</EmptyState>
      ) : (
        <ul className="divide-y divide-sage/40 text-sm">
          {reservations.data.map((r) => (
            <li key={r.id} className="flex justify-between py-2">
              <Link to={`/kitaplar/${r.book_id}`} className="text-brand">
                {r.book_title}
              </Link>
              <span>
                {RESERVATION_STATUS_LABELS[r.status]} · {formatDate(r.created_at)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
