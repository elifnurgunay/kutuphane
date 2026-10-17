import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { Card, EmptyState, LoadingState } from "../../components/ui";
import { formatDate, formatMoney, todayIso } from "../../lib/format";
import {
  errorMessage,
  inputClass,
  outlineButton,
  primaryButton,
  secondaryButton,
} from "../../lib/ui";
import { MEMBER_TYPE_LABELS, type MemberSummary } from "../members/api";
import { LoanStatusBadge, MemberStatusBadge } from "../members/badges";
import { dueState } from "../members/dueState";
import {
  findCopy,
  findMemberByNo,
  findOpenLoan,
  useEligibility,
  useIssueLoan,
  useLoans,
  useRenewLoan,
  useReturnLoan,
  type CopyWithBook,
  type Loan,
  type ReturnResponse,
} from "./api";
import { BarcodeFinder } from "./BarcodeFinder";
import { classifyScan } from "./scan";

type Pending =
  { kind: "issue"; copy: CopyWithBook } | { kind: "return"; copy: CopyWithBook; loan: Loan };

type Notice = { tone: "success" | "error" | "info"; lines: string[] };

const NOTICE_CLASSES: Record<Notice["tone"], string> = {
  success: "border-leaf bg-leaf/10 text-leaf",
  error: "border-danger bg-danger/10 text-danger",
  info: "border-sage bg-sage/20 text-brand",
};

function returnNotice(result: ReturnResponse): Notice {
  const lines = [`"${result.loan.book_title}" iade alındı.`];
  for (const fine of result.fines) {
    const label = fine.reason === "overdue" ? "Gecikme cezası" : "Hasar cezası";
    lines.push(`${label}: ${formatMoney(fine.amount)}`);
  }
  if (result.reserved_for) {
    lines.push(
      `Bu nüsha ${result.reserved_for.member_name} (${result.reserved_for.member_no}) için ayrıldı; rafa koymayın.`,
    );
  }
  return { tone: "success", lines };
}

export function QuickTransactionPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [scan, setScan] = useState("");
  const [busy, setBusy] = useState(false);
  const [member, setMember] = useState<MemberSummary | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [damaged, setDamaged] = useState(false);
  const [damageFine, setDamageFine] = useState("");

  const issueLoan = useIssueLoan();
  const returnLoan = useReturnLoan();

  const refocus = () => setTimeout(() => inputRef.current?.focus(), 0);
  const fail = (error: unknown) => setNotice({ tone: "error", lines: [errorMessage(error)] });

  function handleScan(event: FormEvent) {
    event.preventDefault();
    void processScan(scan);
  }

  async function processScan(raw: string) {
    const value = raw.trim();
    const kind = classifyScan(value);
    if (kind === "empty") return;
    setScan("");
    setBusy(true);
    setNotice(null);
    try {
      if (kind === "member") {
        const found = await findMemberByNo(value);
        if (!found) {
          setNotice({ tone: "error", lines: [`${value.toUpperCase()} numaralı üye bulunamadı.`] });
          return;
        }
        setMember(found);
        setPending(null);
        return;
      }
      const copy = await findCopy(value);
      const openLoan = await findOpenLoan(copy.barcode);
      setDamaged(false);
      setDamageFine("");
      if (openLoan) {
        setPending({ kind: "return", copy, loan: openLoan });
      } else if (member) {
        setPending({ kind: "issue", copy });
      } else {
        setPending(null);
        setNotice({
          tone: "info",
          lines: [
            `"${copy.book.title}" ödünçte değil. Ödünç vermek için önce üye numarası okutun.`,
          ],
        });
      }
    } catch (error) {
      fail(error);
    } finally {
      setBusy(false);
      refocus();
    }
  }

  async function confirmPending() {
    if (!pending) return;
    try {
      if (pending.kind === "issue" && member) {
        const loan = await issueLoan.mutateAsync({
          member_id: member.id,
          barcode: pending.copy.barcode,
        });
        setNotice({
          tone: "success",
          lines: [`"${loan.book_title}" ödünç verildi. Son teslim: ${formatDate(loan.due_date)}`],
        });
      } else if (pending.kind === "return") {
        const result = await returnLoan.mutateAsync({
          id: pending.loan.id,
          input: { damaged, damage_fine: damaged && damageFine ? damageFine : null },
        });
        setNotice(returnNotice(result));
      }
      setPending(null);
    } catch (error) {
      fail(error);
    } finally {
      refocus();
    }
  }

  const working = busy || issueLoan.isPending || returnLoan.isPending;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-brand">Hızlı İşlem</h1>

      <Card>
        <form onSubmit={handleScan} className="flex flex-wrap gap-3">
          <input
            ref={inputRef}
            autoFocus
            value={scan}
            onChange={(e) => setScan(e.target.value)}
            placeholder="Üye numarası veya kitap barkodu okutun"
            aria-label="Üye numarası veya barkod"
            className={`${inputClass} flex-1 font-mono text-lg`}
          />
          <button type="submit" className={primaryButton} disabled={working}>
            Okut
          </button>
          {member && (
            <button
              type="button"
              className={outlineButton}
              onClick={() => {
                setMember(null);
                setPending(null);
                setNotice(null);
                refocus();
              }}
            >
              Üyeyi temizle
            </button>
          )}
        </form>
        {notice && (
          <div
            role={notice.tone === "error" ? "alert" : "status"}
            className={`mt-3 rounded border px-3 py-2 text-sm ${NOTICE_CLASSES[notice.tone]}`}
          >
            {notice.lines.map((line) => (
              <p key={line}>{line}</p>
            ))}
          </div>
        )}
        <div className="mt-3">
          <BarcodeFinder onPick={(barcode) => void processScan(barcode)} />
        </div>
      </Card>

      {pending && (
        <Card className="border-2 border-leaf">
          <h2 className="text-lg font-semibold text-brand">
            {pending.kind === "issue" ? "Ödünç ver" : "İade al"}
          </h2>
          <p className="mt-1">
            <span className="font-medium">{pending.copy.book.title}</span>{" "}
            <span className="font-mono text-sm text-ink/70">{pending.copy.barcode}</span>
          </p>
          {pending.kind === "return" ? (
            <>
              <p className="text-sm">
                {pending.loan.member_name} ({pending.loan.member_no}) · Son teslim{" "}
                {formatDate(pending.loan.due_date)}{" "}
                <LoanStatusBadge
                  status={pending.loan.status}
                  due={dueState(pending.loan.due_date, todayIso())}
                />
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    className="accent-leaf"
                    checked={damaged}
                    onChange={(e) => setDamaged(e.target.checked)}
                  />
                  Hasarlı iade
                </label>
                {damaged && (
                  <input
                    type="number"
                    min={0}
                    step="0.01"
                    placeholder="Hasar cezası (₺, opsiyonel)"
                    value={damageFine}
                    onChange={(e) => setDamageFine(e.target.value)}
                    className={`${inputClass} max-w-56`}
                  />
                )}
              </div>
            </>
          ) : (
            member && (
              <p className="text-sm">
                {member.full_name} ({member.member_no}) adına
              </p>
            )
          )}
          <div className="mt-4 flex gap-2">
            <button
              type="button"
              className={pending.kind === "issue" ? secondaryButton : primaryButton}
              disabled={working}
              onClick={() => void confirmPending()}
            >
              {pending.kind === "issue" ? "Ödünç ver" : "İade al"}
            </button>
            <button
              type="button"
              className={outlineButton}
              onClick={() => {
                setPending(null);
                refocus();
              }}
            >
              Vazgeç
            </button>
          </div>
        </Card>
      )}

      {member ? (
        <MemberPanel member={member} onAction={setNotice} onDone={refocus} />
      ) : (
        <Card>
          <EmptyState>
            Ödünç vermek için önce üye numarasını, iade için doğrudan kitap barkodunu okutun.
          </EmptyState>
        </Card>
      )}
    </div>
  );
}

function MemberPanel({
  member,
  onAction,
  onDone,
}: {
  member: MemberSummary;
  onAction: (notice: Notice) => void;
  onDone: () => void;
}) {
  const eligibility = useEligibility(member.id);
  const loans = useLoans({ status: "open", member_id: member.id, size: 50 });
  const returnLoan = useReturnLoan();
  const renewLoan = useRenewLoan();
  const today = todayIso();

  async function run(action: () => Promise<Notice>) {
    try {
      onAction(await action());
    } catch (error) {
      onAction({ tone: "error", lines: [errorMessage(error)] });
    } finally {
      onDone();
    }
  }

  return (
    <Card>
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-lg font-semibold text-brand">
          <Link to={`/uyeler/${member.id}`}>{member.full_name}</Link>
        </h2>
        <span className="font-mono text-sm">{member.member_no}</span>
        <span className="text-sm">{MEMBER_TYPE_LABELS[member.member_type]}</span>
        <MemberStatusBadge status={member.status} />
      </div>

      {eligibility.isPending ? (
        <LoadingState />
      ) : eligibility.data ? (
        <div className="mt-3 space-y-2">
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <span>
              Elindeki kitap: {eligibility.data.active_loan_count} / {eligibility.data.loan_limit}
            </span>
            <span>
              Ödenmemiş ceza: {formatMoney(eligibility.data.unpaid_fine_total)} (sınır{" "}
              {formatMoney(eligibility.data.max_unpaid_fine)})
            </span>
          </div>
          {eligibility.data.can_borrow ? (
            <p className="rounded bg-leaf/10 px-3 py-2 text-sm text-leaf">Kitap alabilir.</p>
          ) : (
            <ul className="space-y-1 rounded bg-danger/10 px-3 py-2 text-sm text-danger">
              {eligibility.data.problems.map((p) => (
                <li key={p.code}>{p.message}</li>
              ))}
            </ul>
          )}
        </div>
      ) : null}

      <h3 className="mt-4 font-medium">Elindeki kitaplar</h3>
      {loans.isPending ? (
        <LoadingState />
      ) : loans.data && loans.data.items.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-sage text-brand">
              <tr>
                <th className="py-2 pr-4">Kitap</th>
                <th className="py-2 pr-4">Barkod</th>
                <th className="py-2 pr-4">Son teslim</th>
                <th className="py-2 pr-4">Durum</th>
                <th className="py-2" />
              </tr>
            </thead>
            <tbody>
              {loans.data.items.map((loan) => (
                <tr key={loan.id} className="border-b border-sage/40">
                  <td className="py-2 pr-4">{loan.book_title}</td>
                  <td className="py-2 pr-4 font-mono">{loan.barcode}</td>
                  <td className="py-2 pr-4">{formatDate(loan.due_date)}</td>
                  <td className="py-2 pr-4">
                    <LoanStatusBadge status={loan.status} due={dueState(loan.due_date, today)} />
                  </td>
                  <td className="flex justify-end gap-2 py-2">
                    <button
                      type="button"
                      className={outlineButton}
                      disabled={renewLoan.isPending}
                      onClick={() =>
                        void run(async () => {
                          const renewed = await renewLoan.mutateAsync(loan.id);
                          return {
                            tone: "success",
                            lines: [
                              `Süre uzatıldı. Yeni son teslim: ${formatDate(renewed.due_date)}`,
                            ],
                          };
                        })
                      }
                    >
                      Uzat
                    </button>
                    <button
                      type="button"
                      className={primaryButton}
                      disabled={returnLoan.isPending}
                      onClick={() =>
                        void run(async () =>
                          returnNotice(await returnLoan.mutateAsync({ id: loan.id })),
                        )
                      }
                    >
                      İade al
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState>Üyenin elinde kitap yok.</EmptyState>
      )}
    </Card>
  );
}
