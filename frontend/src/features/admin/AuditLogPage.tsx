import { useSearchParams } from "react-router-dom";
import { Card, EmptyState, ErrorMessage, LoadingState, Pagination } from "../../components/ui";
import { inputClass } from "../../lib/ui";
import { useAuditLogs, type AuditLog } from "./api";

const PAGE_SIZE = 50;

const ACTION_LABELS: Record<string, string> = {
  create: "Ekleme",
  update: "Güncelleme",
  delete: "Silme",
  daily_job: "Günlük görev",
};

const ENTITY_LABELS: Record<string, string> = {
  books: "Kitap",
  book_copies: "Nüsha",
  authors: "Yazar",
  publishers: "Yayınevi",
  categories: "Kategori",
  members: "Üye",
  users: "Kullanıcı",
  loans: "Ödünç",
  reservations: "Rezervasyon",
  fines: "Ceza",
  settings: "Ayar",
  system: "Sistem",
};

function formatDateTime(value: string): string {
  return new Date(value.endsWith("Z") || value.includes("+") ? value : `${value}Z`).toLocaleString(
    "tr-TR",
    { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" },
  );
}

function summary(log: AuditLog): string {
  if (!log.details) return "";
  if (log.action === "update") {
    return Object.entries(log.details)
      .map(([key, value]) =>
        Array.isArray(value) ? `${key}: ${String(value[0])} → ${String(value[1])}` : key,
      )
      .join(", ");
  }
  const d = log.details as Record<string, unknown>;
  const name = d.title ?? d.full_name ?? d.name ?? d.barcode ?? d.member_no ?? d.key;
  return name ? String(name) : "";
}

export function AuditLogPage() {
  const [params, setParams] = useSearchParams();
  const entity = params.get("tablo") ?? undefined;
  const page = Number(params.get("sayfa") ?? 1);
  const logs = useAuditLogs({ entity, page, size: PAGE_SIZE });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-brand">İşlem kayıtları</h1>
          <p className="text-sm text-ink/70">Sistemdeki tüm ekleme, güncelleme ve silmeler.</p>
        </div>
        <select
          value={entity ?? ""}
          onChange={(e) => setParams(e.target.value ? { tablo: e.target.value } : {})}
          className={`${inputClass} w-auto`}
          aria-label="Kayıt türü"
        >
          <option value="">Tüm kayıtlar</option>
          {Object.entries(ENTITY_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>
      <Card>
        <ErrorMessage error={logs.error} />
        {logs.isPending ? (
          <LoadingState />
        ) : logs.data && logs.data.items.length === 0 ? (
          <EmptyState>Kayıt yok.</EmptyState>
        ) : logs.data ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-sage text-brand">
                  <tr>
                    <th className="py-2 pr-4">Zaman</th>
                    <th className="py-2 pr-4">Kullanıcı</th>
                    <th className="py-2 pr-4">İşlem</th>
                    <th className="py-2 pr-4">Kayıt</th>
                    <th className="py-2">Ayrıntı</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.data.items.map((log) => (
                    <tr key={log.id} className="border-b border-sage/40 align-top">
                      <td className="whitespace-nowrap py-2 pr-4">
                        {formatDateTime(log.created_at)}
                      </td>
                      <td className="py-2 pr-4">{log.user_name ?? "Sistem"}</td>
                      <td className="py-2 pr-4">{ACTION_LABELS[log.action] ?? log.action}</td>
                      <td className="whitespace-nowrap py-2 pr-4">
                        {ENTITY_LABELS[log.entity] ?? log.entity}
                        {log.entity_id ? ` #${log.entity_id}` : ""}
                      </td>
                      <td className="max-w-md break-words py-2 text-ink/80">{summary(log)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={logs.data.page}
              size={logs.data.size}
              total={logs.data.total}
              onChange={(p) =>
                setParams({ ...(entity ? { tablo: entity } : {}), sayfa: String(p) })
              }
            />
          </>
        ) : null}
      </Card>
    </div>
  );
}
