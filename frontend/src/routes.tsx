import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { BookDetailPage } from "./features/books/BookDetailPage";
import { BookFormPage } from "./features/books/BookFormPage";
import { BookListPage } from "./features/books/BookListPage";
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
            <Route path="/kitaplar" element={<BookListPage />} />
            <Route path="/kitaplar/yeni" element={<BookFormPage />} />
            <Route path="/kitaplar/:id" element={<BookDetailPage />} />
            <Route path="/kitaplar/:id/duzenle" element={<BookFormPage />} />
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
