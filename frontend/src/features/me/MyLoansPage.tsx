import { useState } from "react";
import { Card, EmptyState, ErrorMessage, LoadingState } from "../../components/ui";
import { formatDate, formatMoney, todayIso } from "../../lib/format";
import { errorMessage, outlineButton } from "../../lib/ui";
import { LoanStatusBadge } from "../members/badges";
import { dueState } from "../members/dueState";
import { daysLeft, useMyLoans, useMyProfile, useRenewMyLoan } from "./api";

const OPEN = ["active", "overdue"];

function remainingText(days: number): string {
  if (days > 0) return `${days} gün kaldı`;
  if (days === 0) return "Bugün son gün";
  return `${-days} gün gecikti`;
}

export function MyLoansPage() {
  const profile = useMyProfile();
  const loans = useMyLoans();
  const renew = useRenewMyLoan();
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const today = todayIso();

  if (loans.isPending) return <LoadingState />;
  if (loans.error) return <ErrorMessage error={loans.error} />;
  const open = loans.data.filter((l) => OPEN.includes(l.status));
  const history = loans.data.filter((l) => !OPEN.includes(l.status));
  const unpaid = Number(profile.data?.unpaid_fine_total ?? 0);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-brand">Ödünçlerim</h1>

      {unpaid > 0 && (
        <p className="rounded bg-warning/15 px-3 py-2 text-sm text-ink">
          Ödenmemiş cezanız var: {formatMoney(unpaid)}. Ödeme kütüphane bankosunda yapılır.
        </p>
      )}
      {message && (
        <p
          role={message.ok ? "status" : "alert"}
          className={`rounded px-3 py-2 text-sm ${message.ok ? "bg-leaf/10 text-leaf" : "bg-danger/10 text-danger"}`}
        >
          {message.text}
        </p>
      )}

      <Card>
        <h2 className="text-lg font-semibold text-brand">Elimdeki kitaplar</h2>
        {open.length === 0 ? (
          <EmptyState>Şu anda ödünç aldığınız kitap yok.</EmptyState>
        ) : (
          <ul className="mt-2 divide-y divide-sage/40">
            {open.map((loan) => {
              const days = daysLeft(loan.due_date, today);
              return (
                <li
                  key={loan.id}
                  className="flex flex-wrap items-center justify-between gap-3 py-3"
                >
                  <div>
                    <p className="font-medium">{loan.book_title}</p>
                    <p className="text-sm text-ink/70">
                      Son teslim {formatDate(loan.due_date)} · {remainingText(days)}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <LoanStatusBadge status={loan.status} due={dueState(loan.due_date, today)} />
                    <button
                      type="button"
                      className={outlineButton}
                      disabled={renew.isPending}
                      onClick={() =>
                        renew.mutate(loan.id, {
                          onSuccess: (renewed) =>
                            setMessage({
                              ok: true,
                              text: `Süre uzatıldı. Yeni son teslim: ${formatDate(renewed.due_date)}`,
                            }),
                          onError: (error) => setMessage({ ok: false, text: errorMessage(error) }),
                        })
                      }
                    >
                      Süreyi uzat
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </Card>

      <Card>
        <h2 className="text-lg font-semibold text-brand">Geçmiş</h2>
        {history.length === 0 ? (
          <EmptyState>Geçmiş ödünç kaydınız yok.</EmptyState>
        ) : (
          <ul className="mt-2 divide-y divide-sage/40 text-sm">
            {history.map((loan) => (
              <li key={loan.id} className="flex flex-wrap justify-between gap-2 py-2">
                <span>{loan.book_title}</span>
                <span className="text-ink/70">
                  {formatDate(loan.loan_date)} – {formatDate(loan.return_date)}{" "}
                  <LoanStatusBadge status={loan.status} />
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
