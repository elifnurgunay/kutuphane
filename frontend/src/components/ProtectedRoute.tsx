import { Navigate, Outlet, useLocation } from "react-router-dom";
import type { UserRole } from "../api/auth";
import { useAuth } from "../lib/useAuth";
import { homePathFor } from "../lib/roles";

export function ProtectedRoute({ roles }: { roles?: UserRole[] }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <p className="p-6 text-center text-ink/70">Yükleniyor…</p>;
  }
  if (!user) {
    return <Navigate to="/giris" replace state={{ from: location.pathname }} />;
  }
  if (roles && !roles.includes(user.role)) {
    return <Navigate to={homePathFor(user.role)} replace />;
  }
  return <Outlet />;
}
