import { useState } from "react";
import { useConfirm } from "../../lib/confirm";
import { Link, useSearchParams } from "react-router-dom";
import { Card, EmptyState, ErrorMessage, LoadingState, Pagination } from "../../components/ui";
import { formatDate, formatMoney, todayIso } from "../../lib/format";
import { dangerButton, outlineButton, primaryButton } from "../../lib/ui";
import { LoanStatusBadge } from "../members/badges";
import { dueState } from "../members/dueState";
import {
  useLoans,
  useMarkLost,
  useRenewLoan,
  useReturnLoan,
  type Loan,
  type LoanFilter,
} from "./api";

const PAGE_SIZE = 20;

const TABS: { value: LoanFilter; label: string }[] = [
  { value: "active", label: "Aktif" },
  { value: "overdue", label: "Gecikmiş" },
  { value: "returned", label: "Geçmiş" },
  { value: "lost", label: "Kayıp" },
];

const EMPTY_TEXT: Record<LoanFilter, string> = {
  open: "Açık ödünç yok.",
  active: "Aktif ödünç yok.",
  overdue: "Gecikmiş ödünç yok.",
  returned: "İade edilmiş ödünç yok.",
  lost: "Kayıp olarak işaretlenmiş ödünç yok.",
};

export function LoanListPage() {
  const [params, setParams] = useSearchParams();
  const tab = (params.get("sekme") as LoanFilter | null) ?? "active";
  const page = Number(params.get("sayfa") ?? 1);
  const loans = useLoans({ status: tab, page, size: PAGE_SIZE });
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  function go(changes: Record<string, string>) {
    setMessage(null);
    setParams({ sekme: tab, ...changes });
  }

  const open = tab === "active" || tab === "overdue";

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-brand">Ödünçler</h1>

      <div role="tablist" className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t.value}
            type="button"
            role="tab"
            aria-selected={tab === t.value}
            onClick={() => go({ sekme: t.value })}
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
        <p
          role={message.ok ? "status" : "alert"}
          className={`rounded px-3 py-2 text-sm ${message.ok ? "bg-leaf/10 text-leaf" : "bg-danger/10 text-danger"}`}
        >
          {message.text}
        </p>
      )}

      <Card>
        <ErrorMessage error={loans.error} />
        {loans.isPending ? (
          <LoadingState />
        ) : loans.data && loans.data.items.length === 0 ? (
          <EmptyState>{EMPTY_TEXT[tab]}</EmptyState>
        ) : loans.data ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-sage text-brand">
                  <tr>
                    <th className="py-2 pr-4">Kitap</th>
                    <th className="py-2 pr-4">Üye</th>
                    <th className="py-2 pr-4">Alış</th>
                    <th className="py-2 pr-4">Son teslim</th>
                    {!open && <th className="py-2 pr-4">İade</th>}
                    <th className="py-2 pr-4">Durum</th>
                    {open && <th className="py-2" />}
                  </tr>
                </thead>
                <tbody>
                  {loans.data.items.map((loan) => (
                    <LoanRow key={loan.id} loan={loan} open={open} onMessage={setMessage} />
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={loans.data.page}
              size={loans.data.size}
              total={loans.data.total}
              onChange={(p) => go({ sayfa: String(p) })}
            />
          </>
        ) : null}
      </Card>
    </div>
  );
}

function LoanRow({
  loan,
  open,
  onMessage,
}: {
  loan: Loan;
  open: boolean;
  onMessage: (message: { ok: boolean; text: string }) => void;
}) {
  const returnLoan = useReturnLoan();
  const renewLoan = useRenewLoan();
  const markLost = useMarkLost();
  const confirm = useConfirm();
  const busy = returnLoan.isPending || renewLoan.isPending || markLost.isPending;

  async function run(action: () => Promise<string>) {
    try {
      onMessage({ ok: true, text: await action() });
    } catch (error) {
      onMessage({ ok: false, text: error instanceof Error ? error.message : "Hata oluştu." });
    }
  }

  return (
    <tr className="border-b border-sage/40">
      <td className="py-2 pr-4">
        <Link to={`/kitaplar/${loan.book_id}`} className="text-brand">
          {loan.book_title}
        </Link>
        <div className="font-mono text-xs text-ink/70">{loan.barcode}</div>
      </td>
      <td className="py-2 pr-4">
        <Link to={`/uyeler/${loan.member_id}`} className="text-brand">
          {loan.member_name}
        </Link>
        <div className="font-mono text-xs text-ink/70">{loan.member_no}</div>
      </td>
      <td className="py-2 pr-4">{formatDate(loan.loan_date)}</td>
      <td className="py-2 pr-4">{formatDate(loan.due_date)}</td>
      {!open && <td className="py-2 pr-4">{formatDate(loan.return_date)}</td>}
      <td className="py-2 pr-4">
        <LoanStatusBadge
          status={loan.status}
          due={open ? dueState(loan.due_date, todayIso()) : undefined}
        />
      </td>
      {open && (
        <td className="py-2">
          <div className="flex justify-end gap-2">
            <button
              type="button"
              className={outlineButton}
              disabled={busy}
              onClick={() =>
                void run(async () => {
                  const renewed = await renewLoan.mutateAsync(loan.id);
                  return `Süre uzatıldı: ${renewed.book_title}, yeni son teslim ${formatDate(renewed.due_date)}.`;
                })
              }
            >
              Uzat
            </button>
            <button
              type="button"
              className={primaryButton}
              disabled={busy}
              onClick={() =>
                void run(async () => {
                  const result = await returnLoan.mutateAsync({ id: loan.id });
                  const fine = result.fines.reduce((sum, f) => sum + Number(f.amount), 0);
                  return fine > 0
                    ? `İade alındı. Gecikme cezası: ${formatMoney(fine)}.`
                    : "İade alındı.";
                })
              }
            >
              İade al
            </button>
            <button
              type="button"
              className={dangerButton}
              disabled={busy}
              onClick={async () => {
                const ok = await confirm({
                  title: "Kayıp olarak işaretlensin mi?",
                  message: `"${loan.book_title}" kayıp sayılacak ve ${loan.member_name} adına kayıp cezası yazılacak.`,
                  confirmLabel: "Kayıp işaretle",
                  tone: "danger",
                });
                if (!ok) return;
                void run(async () => {
                  const { fine } = await markLost.mutateAsync(loan.id);
                  return `Kayıp olarak işaretlendi. Ceza: ${formatMoney(fine.amount)}.`;
                });
              }}
            >
              Kayıp
            </button>
          </div>
        </td>
      )}
    </tr>
  );
}
