import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { useAuth } from "./lib/useAuth";
import { homePathFor, STAFF_ROLES } from "./lib/roles";
import { LoginPage } from "./pages/LoginPage";
import { MemberHomePage } from "./pages/MemberHomePage";
import { StaffHomePage } from "./pages/StaffHomePage";

function HomeRedirect() {
  const { user } = useAuth();
  return <Navigate to={user ? homePathFor(user.role) : "/giris"} replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/giris" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route element={<ProtectedRoute roles={STAFF_ROLES} />}>
            <Route path="/panel" element={<StaffHomePage />} />
          </Route>
          <Route element={<ProtectedRoute roles={["member"]} />}>
            <Route path="/hesabim" element={<MemberHomePage />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<HomeRedirect />} />
    </Routes>
  );
}
