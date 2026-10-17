import { useState } from "react";
import { useConfirm } from "../../lib/confirm";
import { Link, useSearchParams } from "react-router-dom";
import { Card, EmptyState, ErrorMessage, LoadingState, Pagination } from "../../components/ui";
import { formatDate, formatMoney } from "../../lib/format";
import { errorMessage, outlineButton, secondaryButton } from "../../lib/ui";
import { useAuth } from "../../lib/useAuth";
import { FINE_REASON_LABELS, type FineStatus } from "../members/api";
import { useCloseFine, useFines, type FineDetail } from "./api";

const PAGE_SIZE = 20;

const TABS: { value: FineStatus; label: string; empty: string; totalLabel: string }[] = [
  {
    value: "unpaid",
    label: "Ödenmemiş",
    empty: "Ödenmemiş ceza yok.",
    totalLabel: "Toplam alacak",
  },
  { value: "paid", label: "Tahsil edilen", empty: "Kayıt yok.", totalLabel: "Toplam tahsilat" },
  { value: "waived", label: "Affedilen", empty: "Kayıt yok.", totalLabel: "Toplam affedilen" },
];

export function FineListPage() {
  const [params, setParams] = useSearchParams();
  const tab = (params.get("sekme") as FineStatus | null) ?? "unpaid";
  const page = Number(params.get("sayfa") ?? 1);
  const fines = useFines({ status: tab, page, size: PAGE_SIZE });
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const current = TABS.find((t) => t.value === tab) ?? TABS[0];

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-brand">Cezalar</h1>

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
        <p
          role={message.ok ? "status" : "alert"}
          className={`rounded px-3 py-2 text-sm ${
            message.ok ? "bg-leaf/10 text-leaf" : "bg-danger/10 text-danger"
          }`}
        >
          {message.text}
        </p>
      )}

      <Card>
        <ErrorMessage error={fines.error} />
        {fines.isPending ? (
          <LoadingState />
        ) : fines.data && fines.data.items.length === 0 ? (
          <EmptyState>{current.empty}</EmptyState>
        ) : fines.data ? (
          <>
            <p className="mb-3 text-sm">
              {current.totalLabel}:{" "}
              <span className="font-semibold">{formatMoney(fines.data.total_amount)}</span>
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-sage text-brand">
                  <tr>
                    <th className="py-2 pr-4">Tarih</th>
                    <th className="py-2 pr-4">Üye</th>
                    <th className="py-2 pr-4">Kitap</th>
                    <th className="py-2 pr-4">Sebep</th>
                    <th className="py-2 pr-4">Tutar</th>
                    {tab === "unpaid" ? (
                      <th className="py-2" />
                    ) : (
                      <th className="py-2 pr-4">Kapanış</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {fines.data.items.map((fine) => (
                    <FineRow key={fine.id} fine={fine} onMessage={setMessage} />
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={fines.data.page}
              size={fines.data.size}
              total={fines.data.total}
              onChange={(p) => setParams({ sekme: tab, sayfa: String(p) })}
            />
          </>
        ) : null}
      </Card>
    </div>
  );
}

function FineRow({
  fine,
  onMessage,
}: {
  fine: FineDetail;
  onMessage: (message: { ok: boolean; text: string }) => void;
}) {
  const { user } = useAuth();
  const closeFine = useCloseFine();
  const confirm = useConfirm();

  async function close(action: "pay" | "waive") {
    const verb = action === "pay" ? "tahsil edildi" : "affedildi";
    const question =
      action === "pay"
        ? `${fine.member_name} adına ${formatMoney(fine.amount)} tahsil edildi olarak işaretlensin mi?`
        : `${fine.member_name} adına ${formatMoney(fine.amount)} ceza affedilsin mi?`;
    const ok = await confirm({
      title: action === "pay" ? "Tahsilat kaydedilsin mi?" : "Ceza affedilsin mi?",
      message: question,
      confirmLabel: action === "pay" ? "Tahsil et" : "Affet",
    });
    if (!ok) return;
    closeFine.mutate(
      { id: fine.id, action },
      {
        onSuccess: () => onMessage({ ok: true, text: `${formatMoney(fine.amount)} ceza ${verb}.` }),
        onError: (error) => onMessage({ ok: false, text: errorMessage(error) }),
      },
    );
  }

  return (
    <tr className="border-b border-sage/40">
      <td className="py-2 pr-4">{formatDate(fine.created_at)}</td>
      <td className="py-2 pr-4">
        <Link to={`/uyeler/${fine.member_id}`} className="text-brand">
          {fine.member_name}
        </Link>
        <div className="font-mono text-xs text-ink/70">{fine.member_no}</div>
      </td>
      <td className="py-2 pr-4">
        {fine.book_title}
        <div className="font-mono text-xs text-ink/70">{fine.barcode}</div>
      </td>
      <td className="py-2 pr-4">{FINE_REASON_LABELS[fine.reason]}</td>
      <td className="py-2 pr-4 font-medium">{formatMoney(fine.amount)}</td>
      {fine.status === "unpaid" ? (
        <td className="py-2">
          <div className="flex justify-end gap-2">
            <button
              type="button"
              className={secondaryButton}
              disabled={closeFine.isPending}
              onClick={() => void close("pay")}
            >
              Tahsil et
            </button>
            {user?.role === "admin" && (
              <button
                type="button"
                className={outlineButton}
                disabled={closeFine.isPending}
                onClick={() => void close("waive")}
              >
                Affet
              </button>
            )}
          </div>
        </td>
      ) : (
        <td className="py-2 pr-4">{formatDate(fine.paid_at)}</td>
      )}
    </tr>
  );
}
