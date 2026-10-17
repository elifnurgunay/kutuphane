import { Card, EmptyState, ErrorMessage, LoadingState } from "../../components/ui";
import { formatDate, formatMoney } from "../../lib/format";
import { FINE_REASON_LABELS, FINE_STATUS_LABELS } from "../members/api";
import { useMyFines } from "./api";

export function MyFinesPage() {
  const fines = useMyFines();

  if (fines.isPending) return <LoadingState />;
  if (fines.error) return <ErrorMessage error={fines.error} />;
  const unpaid = fines.data
    .filter((f) => f.status === "unpaid")
    .reduce((sum, f) => sum + Number(f.amount), 0);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-brand">Cezalarım</h1>
      <Card>
        <p>
          Ödenmemiş toplam: <span className="font-semibold">{formatMoney(unpaid)}</span>
        </p>
        <p className="text-sm text-ink/70">Ödemeler kütüphane bankosunda yapılır.</p>
      </Card>
      <Card>
        {fines.data.length === 0 ? (
          <EmptyState>Ceza kaydınız yok.</EmptyState>
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
                    <td className="py-2">
                      <span className={fine.status === "unpaid" ? "text-danger" : "text-leaf"}>
                        {FINE_STATUS_LABELS[fine.status]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
