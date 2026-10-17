import { useState } from "react";
import type { FormEvent } from "react";
import { Card, ErrorMessage, Field, LoadingState } from "../../components/ui";
import { formatDate, formatMoney } from "../../lib/format";
import { inputClass, primaryButton } from "../../lib/ui";
import { MEMBER_TYPE_LABELS } from "../members/api";
import { MemberStatusBadge } from "../members/badges";
import { useChangePassword, useMyProfile } from "./api";

export function ProfilePage() {
  const profile = useMyProfile();

  if (profile.isPending) return <LoadingState />;
  if (profile.error) return <ErrorMessage error={profile.error} />;
  const p = profile.data;

  const rows: [string, string][] = [
    ["Üye no", p.member_no],
    ["E-posta", p.email],
    ["Telefon", p.phone ?? "—"],
    ["Adres", p.address ?? "—"],
    ["Üye tipi", MEMBER_TYPE_LABELS[p.member_type]],
    ["Üyelik", `${formatDate(p.membership_start)} – ${formatDate(p.membership_end)}`],
    ["Elimdeki kitap", String(p.active_loan_count)],
    ["Ödenmemiş ceza", formatMoney(p.unpaid_fine_total)],
  ];

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold text-brand">{p.full_name}</h1>
          <MemberStatusBadge status={p.status} />
        </div>
        <dl className="mt-4 grid gap-x-6 gap-y-2 sm:grid-cols-2">
          {rows.map(([label, value]) => (
            <div key={label} className="flex gap-2">
              <dt className="w-32 shrink-0 text-sm text-ink/70">{label}</dt>
              <dd className="break-all">{value}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-4 text-sm text-ink/70">
          Bilgilerinizde değişiklik için kütüphane görevlisine başvurun.
        </p>
      </Card>
      <ChangePasswordCard />
    </div>
  );
}

function ChangePasswordCard() {
  const change = useChangePassword();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [repeat, setRepeat] = useState("");
  const [mismatch, setMismatch] = useState(false);
  const [done, setDone] = useState(false);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setDone(false);
    if (next !== repeat) {
      setMismatch(true);
      return;
    }
    setMismatch(false);
    change.mutate(
      { current_password: current, new_password: next },
      {
        onSuccess: () => {
          setDone(true);
          setCurrent("");
          setNext("");
          setRepeat("");
        },
      },
    );
  }

  return (
    <Card>
      <h2 className="text-lg font-semibold text-brand">Şifre değiştir</h2>
      <form onSubmit={handleSubmit} className="mt-3 grid max-w-md gap-3">
        <Field label="Mevcut şifre">
          <input
            type="password"
            required
            autoComplete="current-password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            className={inputClass}
          />
        </Field>
        <Field label="Yeni şifre (en az 8 karakter)">
          <input
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            className={inputClass}
          />
        </Field>
        <Field label="Yeni şifre (tekrar)">
          <input
            type="password"
            required
            autoComplete="new-password"
            value={repeat}
            onChange={(e) => setRepeat(e.target.value)}
            className={inputClass}
          />
        </Field>
        {mismatch && (
          <p role="alert" className="rounded bg-danger/10 px-3 py-2 text-sm text-danger">
            Yeni şifreler aynı değil.
          </p>
        )}
        <ErrorMessage error={change.error} />
        {done && (
          <p role="status" className="rounded bg-leaf/10 px-3 py-2 text-sm text-leaf">
            Şifreniz değiştirildi.
          </p>
        )}
        <button type="submit" className={primaryButton} disabled={change.isPending}>
          Şifreyi değiştir
        </button>
      </form>
    </Card>
  );
}
