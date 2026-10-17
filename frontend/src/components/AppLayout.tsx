import {
  BarChart3,
  BookMarked,
  BookOpen,
  ClipboardList,
  CreditCard,
  History,
  LayoutDashboard,
  Library,
  LogOut,
  Menu,
  ScanLine,
  Search,
  Settings,
  UserCog,
  UserRound,
  Users,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import type { UserRole } from "../api/auth";
import { ROLE_LABELS, STAFF_ROLES } from "../lib/roles";
import { useAuth } from "../lib/useAuth";

interface MenuItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

interface MenuGroup {
  title?: string;
  items: MenuItem[];
  roles?: UserRole[];
}

const STAFF_MENU: MenuGroup[] = [
  {
    items: [
      { to: "/panel", label: "Gösterge Paneli", icon: LayoutDashboard },
      { to: "/islem", label: "Hızlı İşlem", icon: ScanLine },
    ],
  },
  {
    title: "Dolaşım",
    items: [
      { to: "/oduncler", label: "Ödünçler", icon: BookOpen },
      { to: "/rezervasyonlar", label: "Rezervasyonlar", icon: BookMarked },
      { to: "/cezalar", label: "Cezalar", icon: CreditCard },
    ],
  },
  {
    title: "Kayıtlar",
    items: [
      { to: "/kitaplar", label: "Kitaplar", icon: Library },
      { to: "/uyeler", label: "Üyeler", icon: Users },
      { to: "/raporlar", label: "Raporlar", icon: BarChart3 },
    ],
  },
  {
    title: "Yönetim",
    roles: ["admin"],
    items: [
      { to: "/ayarlar", label: "Ayarlar", icon: Settings },
      { to: "/personel", label: "Personel", icon: UserCog },
      { to: "/islem-kayitlari", label: "İşlem kayıtları", icon: History },
    ],
  },
];

const MEMBER_MENU: MenuGroup[] = [
  {
    items: [
      { to: "/hesabim", label: "Ödünçlerim", icon: BookOpen },
      { to: "/katalog", label: "Katalog", icon: Search },
      { to: "/rezervasyonlarim", label: "Rezervasyonlarım", icon: BookMarked },
      { to: "/cezalarim", label: "Cezalarım", icon: ClipboardList },
      { to: "/profil", label: "Profilim", icon: UserRound },
    ],
  },
];

function Brand() {
  return (
    <div className="flex items-center gap-2">
      <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-leaf">
        <Library className="h-5 w-5" aria-hidden />
      </span>
      <span className="text-lg font-semibold tracking-tight">Kütüphane</span>
    </div>
  );
}

function Navigation({
  groups,
  role,
  onNavigate,
}: {
  groups: MenuGroup[];
  role: UserRole;
  onNavigate?: () => void;
}) {
  return (
    <nav className="space-y-5">
      {groups
        .filter((group) => !group.roles || group.roles.includes(role))
        .map((group, index) => (
          <div key={group.title ?? index}>
            {group.title && (
              <p className="mb-1 px-3 text-xs font-semibold uppercase tracking-wider text-cream/60">
                {group.title}
              </p>
            )}
            <ul className="space-y-0.5">
              {group.items.map(({ to, label, icon: Icon }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    onClick={onNavigate}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                        isActive
                          ? "bg-leaf font-medium text-white"
                          : "text-cream/90 hover:bg-sage hover:text-brand"
                      }`
                    }
                  >
                    <Icon className="h-4 w-4 shrink-0" aria-hidden />
                    {label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
    </nav>
  );
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  if (!user) return null;
  const groups = STAFF_ROLES.includes(user.role) ? STAFF_MENU : MEMBER_MENU;

  const userBox = (
    <div className="flex items-center justify-between gap-2 border-t border-cream/15 pt-4 text-sm">
      <div className="min-w-0">
        <p className="truncate font-medium">{user.full_name}</p>
        <p className="text-xs text-cream/70">{ROLE_LABELS[user.role]}</p>
      </div>
      <button
        type="button"
        onClick={() => void logout()}
        className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-cream/90 hover:bg-sage hover:text-brand"
      >
        <LogOut className="h-4 w-4" aria-hidden />
        Çıkış
      </button>
    </div>
  );

  return (
    <div className="min-h-screen lg:flex">
      {/* Masaüstü yan menü */}
      <aside className="hidden w-64 shrink-0 flex-col gap-6 bg-brand px-4 py-5 text-white lg:sticky lg:top-0 lg:flex lg:h-screen">
        <Brand />
        <div className="flex-1 overflow-y-auto">
          <Navigation groups={groups} role={user.role} />
        </div>
        {userBox}
      </aside>

      {/* Mobil üst çubuk ve açılır menü */}
      <header className="sticky top-0 z-20 bg-brand text-white lg:hidden">
        <div className="flex items-center justify-between px-4 py-3">
          <Brand />
          <button
            type="button"
            aria-label={menuOpen ? "Menüyü kapat" : "Menüyü aç"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
            className="rounded-lg p-2 hover:bg-sage hover:text-brand"
          >
            {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
        {menuOpen && (
          <div className="space-y-4 border-t border-cream/15 px-4 pb-4 pt-3">
            <Navigation groups={groups} role={user.role} onNavigate={() => setMenuOpen(false)} />
            {userBox}
          </div>
        )}
      </header>

      <main className="min-w-0 flex-1">
        <div className="mx-auto max-w-6xl p-4 sm:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
