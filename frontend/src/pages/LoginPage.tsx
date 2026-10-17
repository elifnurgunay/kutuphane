import { useState } from "react";
import type { FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../lib/useAuth";
import { BookOpen, Library, ScanLine, Users } from "lucide-react";
import { homePathFor } from "../lib/roles";
import { inputClass, primaryButton } from "../lib/ui";

const FEATURES = [
  { icon: ScanLine, text: "Barkodla hızlı ödünç ve iade" },
  { icon: BookOpen, text: "Rezervasyon kuyruğu ve gecikme takibi" },
  { icon: Users, text: "Üyeler için kendi hesap paneli" },
];

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from;

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to={from ?? homePathFor(user.role)} replace />;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const me = await login(email, password);
      navigate(from ?? homePathFor(me.role), { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Sunucuya ulaşılamadı.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <aside className="hidden flex-col justify-between bg-brand p-10 text-white lg:flex">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-leaf">
            <Library className="h-6 w-6" aria-hidden />
          </span>
          <span className="text-xl font-semibold">Kütüphane Otomasyon Sistemi</span>
        </div>
        <div>
          <p className="text-3xl font-semibold leading-snug">
            Kitaplar, üyeler ve ödünçler
            <br />
            tek yerde.
          </p>
          <ul className="mt-8 space-y-4">
            {FEATURES.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-cream/90">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-sage/30">
                  <Icon className="h-4 w-4" aria-hidden />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-sm text-cream/60">© Kütüphane Otomasyon Sistemi</p>
      </aside>

      <div className="flex items-center justify-center px-4 py-12">
        <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-5">
          <div className="flex items-center gap-3 lg:hidden">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand text-white">
              <Library className="h-5 w-5" aria-hidden />
            </span>
            <span className="text-lg font-semibold text-brand">Kütüphane</span>
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-brand">Giriş yap</h1>
            <p className="mt-1 text-sm text-ink/70">Devam etmek için hesabınızla giriş yapın.</p>
          </div>

          <label className="block space-y-1">
            <span className="text-sm font-medium">E-posta</span>
            <input
              type="email"
              autoComplete="username"
              required
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
            />
          </label>

          <label className="block space-y-1">
            <span className="text-sm font-medium">Şifre</span>
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
            />
          </label>

          {error && (
            <p role="alert" className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">
              {error}
            </p>
          )}

          <button type="submit" disabled={submitting} className={`${primaryButton} w-full py-2.5`}>
            {submitting ? "Giriş yapılıyor…" : "Giriş yap"}
          </button>
        </form>
      </div>
    </div>
  );
}
