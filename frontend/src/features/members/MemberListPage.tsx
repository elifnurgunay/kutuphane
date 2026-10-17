import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Card, EmptyState, ErrorMessage, LoadingState, Pagination } from "../../components/ui";
import { formatDate } from "../../lib/format";
import { inputClass, primaryButton } from "../../lib/ui";
import {
  MEMBER_STATUS_LABELS,
  MEMBER_TYPE_LABELS,
  useMembers,
  type MemberQuery,
  type MemberStatus,
} from "./api";
import { MemberStatusBadge } from "./badges";

const PAGE_SIZE = 20;

function readQuery(params: URLSearchParams): MemberQuery {
  return {
    q: params.get("q") ?? undefined,
    status: (params.get("durum") as MemberStatus | null) ?? undefined,
    page: Number(params.get("sayfa") ?? 1),
    size: PAGE_SIZE,
  };
}

export function MemberListPage() {
  const [params, setParams] = useSearchParams();
  const query = readQuery(params);
  const [search, setSearch] = useState(query.q ?? "");
  const members = useMembers(query);

  function update(changes: Record<string, string | undefined>) {
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    if (!("sayfa" in changes)) next.delete("sayfa");
    setParams(next);
  }

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    update({ q: search.trim() || undefined });
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-semibold text-brand">Üyeler</h1>
        <Link to="/uyeler/yeni" className={primaryButton}>
          Yeni üye
        </Link>
      </div>

      <Card>
        <form onSubmit={handleSearch} className="grid gap-3 md:grid-cols-[2fr_1fr_auto]">
          <input
            type="search"
            placeholder="Ad, e-posta, üye no veya telefon ara"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={inputClass}
          />
          <select
            value={query.status ?? ""}
            onChange={(e) => update({ durum: e.target.value || undefined })}
            className={inputClass}
            aria-label="Durum"
          >
            <option value="">Tüm durumlar</option>
            {Object.entries(MEMBER_STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <button type="submit" className={primaryButton}>
            Ara
          </button>
        </form>
      </Card>

      <Card>
        <ErrorMessage error={members.error} />
        {members.isPending ? (
          <LoadingState />
        ) : members.data && members.data.items.length === 0 ? (
          <EmptyState>Aramanıza uyan üye bulunamadı.</EmptyState>
        ) : members.data ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-sage text-brand">
                  <tr>
                    <th className="py-2 pr-4">Üye no</th>
                    <th className="py-2 pr-4">Ad soyad</th>
                    <th className="py-2 pr-4">Tip</th>
                    <th className="py-2 pr-4">Durum</th>
                    <th className="py-2 pr-4">Üyelik bitişi</th>
                    <th className="py-2">Elindeki kitap</th>
                  </tr>
                </thead>
                <tbody>
                  {members.data.items.map((member) => (
                    <tr key={member.id} className="border-b border-sage/40 hover:bg-sage/20">
                      <td className="py-2 pr-4 font-mono">{member.member_no}</td>
                      <td className="py-2 pr-4">
                        <Link to={`/uyeler/${member.id}`} className="font-medium text-brand">
                          {member.full_name}
                        </Link>
                        <div className="text-xs text-ink/70">{member.email}</div>
                      </td>
                      <td className="py-2 pr-4">{MEMBER_TYPE_LABELS[member.member_type]}</td>
                      <td className="py-2 pr-4">
                        <MemberStatusBadge status={member.status} />
                      </td>
                      <td className="py-2 pr-4">{formatDate(member.membership_end)}</td>
                      <td className="py-2">{member.active_loan_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={members.data.page}
              size={members.data.size}
              total={members.data.total}
              onChange={(page) => update({ sayfa: String(page) })}
            />
          </>
        ) : null}
      </Card>
    </div>
  );
}
