import { useState } from "react";
import type { FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../lib/useAuth";
import { homePathFor } from "../lib/roles";

const inputClass =
  "w-full rounded border border-sage bg-cream px-3 py-2 text-ink outline-none focus:ring-2 focus:ring-leaf";

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
    <div className="flex min-h-screen items-center justify-center px-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-lg border border-sage bg-surface p-6 shadow-sm"
      >
        <div>
          <h1 className="text-2xl font-semibold text-brand">Kütüphane</h1>
          <p className="text-sm text-ink/70">Devam etmek için giriş yapın.</p>
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
          <p role="alert" className="rounded bg-danger/10 px-3 py-2 text-sm text-danger">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded bg-brand px-4 py-2 font-medium text-white hover:bg-brand/90 disabled:opacity-60"
        >
          {submitting ? "Giriş yapılıyor…" : "Giriş yap"}
        </button>
      </form>
    </div>
  );
}
