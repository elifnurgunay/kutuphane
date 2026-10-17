import { lazy, Suspense } from "react";
import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { LoadingState } from "./components/ui";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { BookDetailPage } from "./features/books/BookDetailPage";
import { BookFormPage } from "./features/books/BookFormPage";
import { BookListPage } from "./features/books/BookListPage";
import { MemberDetailPage } from "./features/members/MemberDetailPage";
import { MemberFormPage } from "./features/members/MemberFormPage";
import { MemberListPage } from "./features/members/MemberListPage";
import { LoanListPage } from "./features/loans/LoanListPage";
import { QuickTransactionPage } from "./features/loans/QuickTransactionPage";
import { FineListPage } from "./features/reservations/FineListPage";
import { ReservationListPage } from "./features/reservations/ReservationListPage";
import { CatalogPage } from "./features/me/CatalogPage";
import { MyFinesPage } from "./features/me/MyFinesPage";
import { MyLoansPage } from "./features/me/MyLoansPage";
import { MyReservationsPage } from "./features/me/MyReservationsPage";
import { ProfilePage } from "./features/me/ProfilePage";
import { AuditLogPage } from "./features/admin/AuditLogPage";
import { SettingsPage } from "./features/admin/SettingsPage";
import { StaffPage } from "./features/admin/StaffPage";
import { useAuth } from "./lib/useAuth";
import { homePathFor, STAFF_ROLES } from "./lib/roles";
import { LoginPage } from "./pages/LoginPage";

// Grafik kütüphanesi büyük olduğundan rapor sayfaları ayrı parça olarak yüklenir.
const DashboardPage = lazy(() =>
  import("./features/reports/DashboardPage").then((m) => ({ default: m.DashboardPage })),
);
const ReportsPage = lazy(() =>
  import("./features/reports/ReportsPage").then((m) => ({ default: m.ReportsPage })),
);

function Lazy({ children }: { children: ReactNode }) {
  return <Suspense fallback={<LoadingState />}>{children}</Suspense>;
}

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
            <Route
              path="/panel"
              element={
                <Lazy>
                  <DashboardPage />
                </Lazy>
              }
            />
            <Route
              path="/raporlar"
              element={
                <Lazy>
                  <ReportsPage />
                </Lazy>
              }
            />
            <Route path="/islem" element={<QuickTransactionPage />} />
            <Route path="/oduncler" element={<LoanListPage />} />
            <Route path="/rezervasyonlar" element={<ReservationListPage />} />
            <Route path="/cezalar" element={<FineListPage />} />
            <Route path="/kitaplar" element={<BookListPage />} />
            <Route path="/kitaplar/yeni" element={<BookFormPage />} />
            <Route path="/kitaplar/:id" element={<BookDetailPage />} />
            <Route path="/kitaplar/:id/duzenle" element={<BookFormPage />} />
            <Route path="/uyeler" element={<MemberListPage />} />
            <Route path="/uyeler/yeni" element={<MemberFormPage />} />
            <Route path="/uyeler/:id" element={<MemberDetailPage />} />
            <Route path="/uyeler/:id/duzenle" element={<MemberFormPage />} />
          </Route>
          <Route element={<ProtectedRoute roles={["admin"]} />}>
            <Route path="/ayarlar" element={<SettingsPage />} />
            <Route path="/personel" element={<StaffPage />} />
            <Route path="/islem-kayitlari" element={<AuditLogPage />} />
          </Route>
          <Route element={<ProtectedRoute roles={["member"]} />}>
            <Route path="/hesabim" element={<MyLoansPage />} />
            <Route path="/katalog" element={<CatalogPage />} />
            <Route path="/rezervasyonlarim" element={<MyReservationsPage />} />
            <Route path="/cezalarim" element={<MyFinesPage />} />
            <Route path="/profil" element={<ProfilePage />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<HomeRedirect />} />
    </Routes>
  );
}
