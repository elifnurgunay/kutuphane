import { useState } from "react";
import type { FormEvent } from "react";
import { Card, EmptyState, ErrorMessage, Field, LoadingState } from "../../components/ui";
import { useConfirm } from "../../lib/confirm";
import { formatDate } from "../../lib/format";
import { ROLE_LABELS } from "../../lib/roles";
import { errorMessage, inputClass, outlineButton, primaryButton } from "../../lib/ui";
import { useAuth } from "../../lib/useAuth";
import {
  useResetStaffPassword,
  useSaveStaff,
  useStaff,
  type StaffInput,
  type StaffRole,
  type StaffUser,
} from "./api";

export function StaffPage() {
  const staff = useStaff();
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-brand">Personel</h1>
      {message && (
        <p
          role={message.ok ? "status" : "alert"}
          className={`rounded-lg px-3 py-2 text-sm ${
            message.ok ? "bg-leaf/10 text-leaf" : "bg-danger/10 text-danger"
          }`}
        >
          {message.text}
        </p>
      )}
      <Card>
        {staff.isPending ? (
          <LoadingState />
        ) : staff.error ? (
          <ErrorMessage error={staff.error} />
        ) : staff.data.length === 0 ? (
          <EmptyState>Personel kaydı yok.</EmptyState>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-sage text-brand">
                <tr>
                  <th className="py-2 pr-4">Ad soyad</th>
                  <th className="py-2 pr-4">E-posta</th>
                  <th className="py-2 pr-4">Rol</th>
                  <th className="py-2 pr-4">Durum</th>
                  <th className="py-2 pr-4">Kayıt</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody>
                {staff.data.map((user) => (
                  <StaffRow key={user.id} user={user} onMessage={setMessage} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      <NewStaffCard onMessage={setMessage} />
    </div>
  );
}

function StaffRow({
  user,
  onMessage,
}: {
  user: StaffUser;
  onMessage: (message: { ok: boolean; text: string }) => void;
}) {
  const { user: me } = useAuth();
  const confirm = useConfirm();
  const save = useSaveStaff();
  const reset = useResetStaffPassword();
  const isMe = me?.id === user.id;
  const [resetting, setResetting] = useState(false);
  const [newPassword, setNewPassword] = useState("");

  function update(changes: Partial<StaffInput>, success: string) {
    const input: StaffInput = {
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      is_active: user.is_active,
      ...changes,
    };
    save.mutate(
      { id: user.id, input },
      {
        onSuccess: () => onMessage({ ok: true, text: success }),
        onError: (error) => onMessage({ ok: false, text: errorMessage(error) }),
      },
    );
  }

  async function toggleActive() {
    const ok = await confirm({
      title: user.is_active ? "Hesap kapatılsın mı?" : "Hesap açılsın mı?",
      message: user.is_active
        ? `${user.full_name} artık giriş yapamayacak.`
        : `${user.full_name} yeniden giriş yapabilecek.`,
      confirmLabel: user.is_active ? "Hesabı kapat" : "Hesabı aç",
      tone: user.is_active ? "danger" : "default",
    });
    if (ok) {
      update(
        { is_active: !user.is_active },
        `${user.full_name} hesabı ${user.is_active ? "kapatıldı" : "açıldı"}.`,
      );
    }
  }

  function resetPassword(event: FormEvent) {
    event.preventDefault();
    reset.mutate(
      { id: user.id, password: newPassword },
      {
        onSuccess: () => {
          onMessage({ ok: true, text: `${user.full_name} şifresi değiştirildi.` });
          setResetting(false);
          setNewPassword("");
        },
        onError: (error) => onMessage({ ok: false, text: errorMessage(error) }),
      },
    );
  }

  return (
    <tr className="border-b border-sage/40">
      <td className="py-2 pr-4 font-medium">
        {user.full_name}
        {isMe && <span className="ml-2 text-xs text-ink/60">(siz)</span>}
      </td>
      <td className="py-2 pr-4">{user.email}</td>
      <td className="py-2 pr-4">
        <select
          value={user.role}
          disabled={isMe || save.isPending}
          onChange={(e) =>
            update({ role: e.target.value as StaffRole }, `${user.full_name} rolü güncellendi.`)
          }
          className={`${inputClass} py-1`}
          aria-label="Rol"
        >
          <option value="librarian">{ROLE_LABELS.librarian}</option>
          <option value="admin">{ROLE_LABELS.admin}</option>
        </select>
      </td>
      <td className="py-2 pr-4">
        <span className={user.is_active ? "text-leaf" : "text-danger"}>
          {user.is_active ? "Aktif" : "Kapalı"}
        </span>
      </td>
      <td className="py-2 pr-4">{formatDate(user.created_at)}</td>
      <td className="py-2">
        {resetting ? (
          <form onSubmit={resetPassword} className="flex justify-end gap-2">
            <input
              type="password"
              required
              minLength={8}
              autoFocus
              autoComplete="new-password"
              placeholder="Yeni şifre (en az 8)"
              aria-label={`${user.full_name} için yeni şifre`}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className={`${inputClass} w-48 py-1`}
            />
            <button type="submit" className={primaryButton} disabled={reset.isPending}>
              Kaydet
            </button>
            <button type="button" className={outlineButton} onClick={() => setResetting(false)}>
              Vazgeç
            </button>
          </form>
        ) : (
          <div className="flex justify-end gap-2">
            <button type="button" className={outlineButton} onClick={() => setResetting(true)}>
              Şifre sıfırla
            </button>
            {!isMe && (
              <button
                type="button"
                className={outlineButton}
                disabled={save.isPending}
                onClick={() => void toggleActive()}
              >
                {user.is_active ? "Hesabı kapat" : "Hesabı aç"}
              </button>
            )}
          </div>
        )}
      </td>
    </tr>
  );
}

const EMPTY: StaffInput = { email: "", full_name: "", role: "librarian", password: "" };

function NewStaffCard({
  onMessage,
}: {
  onMessage: (message: { ok: boolean; text: string }) => void;
}) {
  const [form, setForm] = useState<StaffInput>(EMPTY);
  const save = useSaveStaff();

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    save.mutate(
      { input: form },
      {
        onSuccess: (user) => {
          onMessage({ ok: true, text: `${user.full_name} eklendi.` });
          setForm(EMPTY);
        },
      },
    );
  }

  return (
    <Card>
      <h2 className="text-lg font-semibold text-brand">Yeni personel</h2>
      <form onSubmit={handleSubmit} className="mt-3 grid gap-3 md:grid-cols-2">
        <Field label="Ad soyad">
          <input
            required
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            className={inputClass}
          />
        </Field>
        <Field label="E-posta">
          <input
            required
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className={inputClass}
          />
        </Field>
        <Field label="Rol">
          <select
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value as StaffRole })}
            className={inputClass}
          >
            <option value="librarian">{ROLE_LABELS.librarian}</option>
            <option value="admin">{ROLE_LABELS.admin}</option>
          </select>
        </Field>
        <Field label="İlk şifre (en az 8 karakter)">
          <input
            required
            type="password"
            minLength={8}
            autoComplete="new-password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className={inputClass}
          />
        </Field>
        <div className="space-y-3 md:col-span-2">
          <ErrorMessage error={save.error} />
          <button type="submit" className={primaryButton} disabled={save.isPending}>
            Personel ekle
          </button>
        </div>
      </form>
    </Card>
  );
}
