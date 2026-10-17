import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Card, ErrorMessage, Field, LoadingState } from "../../components/ui";
import { addDaysIso, todayIso } from "../../lib/format";
import { inputClass, primaryButton } from "../../lib/ui";
import {
  MEMBER_TYPE_LABELS,
  useMember,
  useSaveMember,
  type MemberDetail,
  type MemberInput,
  type MemberType,
} from "./api";

// Yalnızca formdaki önerilen bitiş tarihi; görevli değiştirebilir.
const SUGGESTED_MEMBERSHIP_DAYS = 365;

function initialState(member?: MemberDetail): MemberInput {
  const start = member?.membership_start ?? todayIso();
  return {
    email: member?.email ?? "",
    full_name: member?.full_name ?? "",
    phone: member?.phone ?? "",
    address: member?.address ?? "",
    member_type: member?.member_type ?? "student",
    membership_start: start,
    membership_end: member?.membership_end ?? addDaysIso(start, SUGGESTED_MEMBERSHIP_DAYS),
    password: "",
  };
}

export function MemberFormPage() {
  const { id } = useParams();
  const memberId = id ? Number(id) : undefined;
  const member = useMember(memberId);

  if (memberId && member.isPending) return <LoadingState />;
  if (memberId && member.error) return <ErrorMessage error={member.error} />;
  return <MemberForm key={memberId ?? "new"} memberId={memberId} member={member.data} />;
}

function MemberForm({ memberId, member }: { memberId?: number; member?: MemberDetail }) {
  const navigate = useNavigate();
  const [form, setForm] = useState(() => initialState(member));
  const saveMember = useSaveMember(memberId);

  const set = <K extends keyof MemberInput>(key: K, value: MemberInput[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const { password, ...rest } = form;
    const input: MemberInput = {
      ...rest,
      phone: rest.phone?.trim() || null,
      address: rest.address?.trim() || null,
      ...(memberId ? {} : { password }),
    };
    const saved = await saveMember.mutateAsync(input);
    navigate(`/uyeler/${saved.id}`, { replace: true });
  }

  return (
    <div className="space-y-4">
      <Link to={memberId ? `/uyeler/${memberId}` : "/uyeler"} className="text-sm text-leaf">
        ← Geri
      </Link>
      <Card>
        <h1 className="text-xl font-semibold text-brand">
          {memberId ? "Üyeyi düzenle" : "Yeni üye"}
        </h1>
        {member && <p className="text-sm text-ink/70">{member.member_no}</p>}
        <form
          onSubmit={(e) => void handleSubmit(e).catch(() => undefined)}
          className="mt-4 space-y-4"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Ad soyad *">
              <input
                required
                value={form.full_name}
                onChange={(e) => set("full_name", e.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="E-posta *">
              <input
                required
                type="email"
                value={form.email}
                onChange={(e) => set("email", e.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="Telefon">
              <input
                value={form.phone ?? ""}
                onChange={(e) => set("phone", e.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="Üye tipi *">
              <select
                value={form.member_type}
                onChange={(e) => set("member_type", e.target.value as MemberType)}
                className={inputClass}
              >
                {Object.entries(MEMBER_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Üyelik başlangıcı *">
              <input
                required
                type="date"
                value={form.membership_start}
                onChange={(e) => set("membership_start", e.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="Üyelik bitişi *">
              <input
                required
                type="date"
                value={form.membership_end}
                onChange={(e) => set("membership_end", e.target.value)}
                className={inputClass}
              />
            </Field>
            {!memberId && (
              <Field label="İlk şifre * (en az 8 karakter)">
                <input
                  required
                  type="password"
                  minLength={8}
                  autoComplete="new-password"
                  value={form.password ?? ""}
                  onChange={(e) => set("password", e.target.value)}
                  className={inputClass}
                />
              </Field>
            )}
          </div>
          <Field label="Adres">
            <textarea
              rows={2}
              value={form.address ?? ""}
              onChange={(e) => set("address", e.target.value)}
              className={inputClass}
            />
          </Field>

          <ErrorMessage error={saveMember.error} />
          <button type="submit" className={primaryButton} disabled={saveMember.isPending}>
            {saveMember.isPending ? "Kaydediliyor…" : "Kaydet"}
          </button>
        </form>
      </Card>
    </div>
  );
}
