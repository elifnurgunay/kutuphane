import { useAuth } from "../lib/useAuth";

export function StaffHomePage() {
  const { user } = useAuth();
  return (
    <section className="rounded-lg border border-sage bg-surface p-6">
      <h1 className="text-xl font-semibold text-brand">Gösterge Paneli</h1>
      <p className="mt-2">Hoş geldiniz, {user?.full_name}.</p>
    </section>
  );
}
