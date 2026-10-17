import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Card, EmptyState, ErrorMessage, Field, LoadingState } from "../../components/ui";
import { addDaysIso, formatDate, formatMoney, todayIso } from "../../lib/format";
import { errorMessage, inputClass, outlineButton } from "../../lib/ui";
import {
  downloadReport,
  useActiveMembers,
  useCategoryStats,
  useOverdue,
  usePopularBooks,
  type Period,
  type ReportName,
} from "./api";
import { CategoryChart, PopularBooksChart } from "./charts";

// Rapor ekranı açıldığında önerilen tarih aralığı (görevli değiştirebilir)
const DEFAULT_PERIOD_DAYS = 30;
const TOP_LIMIT = 20;

const REPORTS: { value: ReportName; label: string; usesPeriod: boolean }[] = [
  { value: "popular-books", label: "Popüler kitaplar", usesPeriod: true },
  { value: "overdue", label: "Gecikmiş ödünçler", usesPeriod: false },
  { value: "active-members", label: "Aktif üyeler", usesPeriod: true },
  { value: "category-stats", label: "Kategori istatistikleri", usesPeriod: true },
];

const th = "py-2 pr-4";
const td = "py-2 pr-4";

export function ReportsPage() {
  const [params, setParams] = useSearchParams();
  const report = (params.get("rapor") as ReportName | null) ?? "popular-books";
  const today = todayIso();
  const period: Period = {
    from: params.get("from") ?? addDaysIso(today, -DEFAULT_PERIOD_DAYS),
    to: params.get("to") ?? today,
  };
  const current = REPORTS.find((r) => r.value === report) ?? REPORTS[0];
  const [downloadError, setDownloadError] = useState<string | null>(null);

  function update(changes: Record<string, string>) {
    setParams({ rapor: report, from: period.from ?? "", to: period.to ?? "", ...changes });
  }

  async function handleDownload() {
    setDownloadError(null);
    try {
      await downloadReport(
        report,
        current.usesPeriod ? period : {},
        current.usesPeriod ? TOP_LIMIT : undefined,
      );
    } catch (error) {
      setDownloadError(errorMessage(error));
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-brand">Raporlar</h1>

      <div role="tablist" className="flex flex-wrap gap-2">
        {REPORTS.map((r) => (
          <button
            key={r.value}
            type="button"
            role="tab"
            aria-selected={report === r.value}
            onClick={() => update({ rapor: r.value })}
            className={`rounded px-4 py-2 text-sm ${
              report === r.value
                ? "bg-leaf text-white"
                : "border border-sage text-brand hover:bg-sage/30"
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      <Card>
        <div className="flex flex-wrap items-end gap-3">
          {current.usesPeriod && (
            <>
              <Field label="Başlangıç">
                <input
                  type="date"
                  value={period.from}
                  max={period.to}
                  onChange={(e) => update({ from: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <Field label="Bitiş">
                <input
                  type="date"
                  value={period.to}
                  min={period.from}
                  onChange={(e) => update({ to: e.target.value })}
                  className={inputClass}
                />
              </Field>
            </>
          )}
          <button type="button" className={outlineButton} onClick={() => void handleDownload()}>
            CSV indir
          </button>
        </div>
        {downloadError && (
          <p role="alert" className="mt-3 rounded bg-danger/10 px-3 py-2 text-sm text-danger">
            {downloadError}
          </p>
        )}
      </Card>

      {report === "popular-books" && <PopularBooksReport period={period} />}
      {report === "overdue" && <OverdueReport />}
      {report === "active-members" && <ActiveMembersReport period={period} />}
      {report === "category-stats" && <CategoryReport period={period} />}
    </div>
  );
}

function PopularBooksReport({ period }: { period: Period }) {
  const data = usePopularBooks(period, TOP_LIMIT);
  if (data.isPending) return <LoadingState />;
  if (data.error) return <ErrorMessage error={data.error} />;
  if (data.data.length === 0)
    return (
      <Card>
        <EmptyState>Bu dönemde ödünç kaydı yok.</EmptyState>
      </Card>
    );
  return (
    <>
      <Card>
        <PopularBooksChart data={data.data} />
      </Card>
      <Card>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-sage text-brand">
            <tr>
              <th className={th}>#</th>
              <th className={th}>Kitap</th>
              <th className={th}>Yazar</th>
              <th className="py-2">Ödünç</th>
            </tr>
          </thead>
          <tbody>
            {data.data.map((b, i) => (
              <tr key={b.book_id} className="border-b border-sage/40">
                <td className={td}>{i + 1}</td>
                <td className={td}>
                  <Link to={`/kitaplar/${b.book_id}`} className="text-brand">
                    {b.title}
                  </Link>
                </td>
                <td className={td}>{b.authors}</td>
                <td className="py-2">{b.loan_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}

function OverdueReport() {
  const data = useOverdue();
  if (data.isPending) return <LoadingState />;
  if (data.error) return <ErrorMessage error={data.error} />;
  if (data.data.length === 0)
    return (
      <Card>
        <EmptyState>Gecikmiş ödünç yok.</EmptyState>
      </Card>
    );
  const total = data.data.reduce((sum, item) => sum + Number(item.estimated_fine), 0);
  return (
    <Card>
      <p className="mb-3 text-sm">
        {data.data.length} gecikmiş ödünç · tahmini toplam ceza{" "}
        <span className="font-semibold">{formatMoney(total)}</span>
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-sage text-brand">
            <tr>
              <th className={th}>Üye</th>
              <th className={th}>Telefon</th>
              <th className={th}>Kitap</th>
              <th className={th}>Son teslim</th>
              <th className={th}>Gecikme</th>
              <th className="py-2">Tahmini ceza</th>
            </tr>
          </thead>
          <tbody>
            {data.data.map((item) => (
              <tr key={item.loan_id} className="border-b border-sage/40">
                <td className={td}>
                  <Link to={`/uyeler/${item.member_id}`} className="text-brand">
                    {item.member_name}
                  </Link>
                  <div className="font-mono text-xs text-ink/60">{item.member_no}</div>
                </td>
                <td className={td}>{item.phone ?? "—"}</td>
                <td className={td}>
                  {item.book_title}
                  <div className="font-mono text-xs text-ink/60">{item.barcode}</div>
                </td>
                <td className={td}>{formatDate(item.due_date)}</td>
                <td className={`${td} text-danger`}>{item.days_late} gün</td>
                <td className="py-2">{formatMoney(item.estimated_fine)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function ActiveMembersReport({ period }: { period: Period }) {
  const data = useActiveMembers(period, TOP_LIMIT);
  if (data.isPending) return <LoadingState />;
  if (data.error) return <ErrorMessage error={data.error} />;
  if (data.data.length === 0)
    return (
      <Card>
        <EmptyState>Bu dönemde ödünç alan üye yok.</EmptyState>
      </Card>
    );
  return (
    <Card>
      <table className="w-full text-left text-sm">
        <thead className="border-b border-sage text-brand">
          <tr>
            <th className={th}>#</th>
            <th className={th}>Üye</th>
            <th className={th}>Üye no</th>
            <th className="py-2">Ödünç</th>
          </tr>
        </thead>
        <tbody>
          {data.data.map((m, i) => (
            <tr key={m.member_id} className="border-b border-sage/40">
              <td className={td}>{i + 1}</td>
              <td className={td}>
                <Link to={`/uyeler/${m.member_id}`} className="text-brand">
                  {m.full_name}
                </Link>
              </td>
              <td className={`${td} font-mono`}>{m.member_no}</td>
              <td className="py-2">{m.loan_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function CategoryReport({ period }: { period: Period }) {
  const data = useCategoryStats(period);
  if (data.isPending) return <LoadingState />;
  if (data.error) return <ErrorMessage error={data.error} />;
  return (
    <>
      <Card>
        <CategoryChart data={data.data} />
      </Card>
      <Card>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-sage text-brand">
            <tr>
              <th className={th}>Kategori</th>
              <th className={th}>Kitap</th>
              <th className={th}>Nüsha</th>
              <th className="py-2">Ödünç (dönem)</th>
            </tr>
          </thead>
          <tbody>
            {data.data.map((c) => (
              <tr key={c.category_id} className="border-b border-sage/40">
                <td className={td}>{c.name}</td>
                <td className={td}>{c.book_count}</td>
                <td className={td}>{c.copy_count}</td>
                <td className="py-2">{c.loan_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}
