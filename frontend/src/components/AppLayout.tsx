import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../lib/useAuth";
import { ROLE_LABELS, STAFF_ROLES } from "../lib/roles";

const STAFF_MENU = [
  { to: "/panel", label: "Gösterge Paneli" },
  { to: "/islem", label: "Hızlı İşlem" },
  { to: "/oduncler", label: "Ödünçler" },
  { to: "/kitaplar", label: "Kitaplar" },
  { to: "/uyeler", label: "Üyeler" },
];
const MEMBER_MENU = [{ to: "/hesabim", label: "Hesabım" }];

export function AppLayout() {
  const { user, logout } = useAuth();
  if (!user) return null;
  const menu = STAFF_ROLES.includes(user.role) ? STAFF_MENU : MEMBER_MENU;

  return (
    <div className="min-h-screen">
      <header className="bg-brand text-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <span className="text-lg font-semibold">Kütüphane</span>
          <nav className="flex flex-1 gap-2">
            {menu.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded px-3 py-1.5 text-sm ${isActive ? "bg-leaf" : "hover:bg-sage hover:text-brand"}`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3 text-sm">
            <span>
              {user.full_name} <span className="opacity-75">· {ROLE_LABELS[user.role]}</span>
            </span>
            <button
              type="button"
              onClick={() => void logout()}
              className="rounded border border-cream/60 px-3 py-1.5 hover:bg-sage hover:text-brand"
            >
              Çıkış
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl p-4 sm:p-6">
        <Outlet />
      </main>
    </div>
  );
}
