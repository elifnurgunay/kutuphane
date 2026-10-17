import { Link } from "react-router-dom";
import { Card, EmptyState, ErrorMessage, LoadingState } from "../../components/ui";
import { addDaysIso, formatDate, formatMoney, todayIso } from "../../lib/format";
import { primaryButton } from "../../lib/ui";
import { useDashboard, useOverdue, usePopularBooks } from "./api";
import { PopularBooksChart } from "./charts";

// Gösterge panelindeki "popüler kitaplar" penceresi (yalnızca görünüm tercihi)
const POPULAR_WINDOW_DAYS = 30;
const OVERDUE_PREVIEW = 5;

function StatCard({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "default" | "danger";
}) {
  return (
    <div
      className={`rounded-lg border bg-surface p-4 ${tone === "danger" ? "border-danger" : "border-sage"}`}
    >
      <p className="text-sm text-ink/70">{label}</p>
      <p
        className={`mt-1 text-2xl font-semibold ${tone === "danger" ? "text-danger" : "text-brand"}`}
      >
        {value}
      </p>
      {hint && <p className="mt-1 text-xs text-ink/60">{hint}</p>}
    </div>
  );
}

export function DashboardPage() {
  const dashboard = useDashboard();
  const today = todayIso();
  const popular = usePopularBooks({ from: addDaysIso(today, -POPULAR_WINDOW_DAYS), to: today }, 8);
  const overdue = useOverdue();

  if (dashboard.isPending) return <LoadingState />;
  if (dashboard.error) return <ErrorMessage error={dashboard.error} />;
  const d = dashboard.data;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-semibold text-brand">Gösterge Paneli</h1>
        <Link to="/islem" className={primaryButton}>
          Hızlı işlem
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Kitap" value={d.total_books} hint={`${d.total_copies} nüsha`} />
        <StatCard label="Rafta (müsait)" value={d.available_copies} />
        <StatCard label="Ödünçte" value={d.open_loans} />
        <StatCard
          label="Gecikmiş"
          value={d.overdue_loans}
          tone={d.overdue_loans > 0 ? "danger" : "default"}
        />
        <StatCard label="Bugün verilen" value={d.loans_today} />
        <StatCard label="Bugün iade" value={d.returns_today} />
        <StatCard label="Aktif üye" value={d.active_members} />
        <StatCard label="Ödenmemiş ceza" value={formatMoney(d.unpaid_fine_total)} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="text-lg font-semibold text-brand">
            Popüler kitaplar <span className="text-sm font-normal text-ink/60">(son 30 gün)</span>
          </h2>
          {popular.isPending ? (
            <LoadingState />
          ) : popular.data && popular.data.length > 0 ? (
            <PopularBooksChart data={popular.data} />
          ) : (
            <EmptyState>Bu dönemde ödünç kaydı yok.</EmptyState>
          )}
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-brand">Gecikmiş ödünçler</h2>
            <Link to="/raporlar?rapor=overdue" className="text-sm text-leaf">
              Tümü →
            </Link>
          </div>
          {overdue.isPending ? (
            <LoadingState />
          ) : overdue.data && overdue.data.length > 0 ? (
            <ul className="mt-2 divide-y divide-sage/40 text-sm">
              {overdue.data.slice(0, OVERDUE_PREVIEW).map((item) => (
                <li key={item.loan_id} className="flex justify-between gap-2 py-2">
                  <span>
                    <Link to={`/uyeler/${item.member_id}`} className="text-brand">
                      {item.member_name}
                    </Link>{" "}
                    · {item.book_title}
                  </span>
                  <span className="shrink-0 text-danger">{item.days_late} gün</span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState>Gecikmiş ödünç yok.</EmptyState>
          )}
        </Card>
      </div>

      <Card>
        <h2 className="text-lg font-semibold text-brand">Son işlemler</h2>
        {d.recent_activity.length === 0 ? (
          <EmptyState>Henüz işlem yok.</EmptyState>
        ) : (
          <ul className="mt-2 divide-y divide-sage/40 text-sm">
            {d.recent_activity.map((a) => (
              <li
                key={`${a.kind}-${a.loan_id}`}
                className="flex flex-wrap justify-between gap-2 py-2"
              >
                <span>
                  <span
                    className={`mr-2 inline-block rounded px-2 py-0.5 text-xs ${
                      a.kind === "loan" ? "bg-sage text-brand" : "bg-leaf text-white"
                    }`}
                  >
                    {a.kind === "loan" ? "Ödünç" : "İade"}
                  </span>
                  {a.book_title} — {a.member_name}{" "}
                  <span className="font-mono text-xs text-ink/60">{a.member_no}</span>
                </span>
                <span className="text-ink/70">{formatDate(a.day)}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
