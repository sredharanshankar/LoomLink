import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../lib/auth";
import { can } from "../../lib/permissions";
import { clsx } from "clsx";

const NAV_ITEMS = [
  { to: "/app/dashboard", key: "dashboard", perm: null },
  { to: "/app/inventory", key: "inventory", perm: "inventory:read" as const },
  { to: "/app/orders", key: "orders", perm: "orders:read" as const },
  { to: "/app/buyers", key: "buyers", perm: "orders:read" as const },
  { to: "/app/production", key: "production", perm: "production:read" as const },
  { to: "/app/machines", key: "machines", perm: "production:read" as const },
  { to: "/app/quality", key: "quality", perm: "quality:read" as const },
  { to: "/app/dispatch", key: "dispatch", perm: "dispatch:read" as const },
  { to: "/app/workers", key: "workers", perm: "workers:read" as const },
  { to: "/app/finance", key: "finance", perm: "finance:read" as const },
  { to: "/app/ripple", key: "ripple", perm: "ripple:read" as const },
];

export default function AppShell() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const visibleItems = NAV_ITEMS.filter(
    (item) => item.perm === null || can(user?.role, item.perm)
  );

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Sidebar */}
      <aside className="hidden md:flex md:flex-col w-56 bg-brand-900 text-white shrink-0">
        <div className="px-5 py-4 text-lg font-bold tracking-tight border-b border-brand-800">
          LoomLink
        </div>
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-brand-700 text-white font-medium"
                    : "text-brand-200 hover:bg-brand-800 hover:text-white"
                )
              }
            >
              {t(item.key)}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-brand-800 px-4 py-3">
          <p className="text-xs text-brand-300 truncate">{user?.full_name}</p>
          <p className="text-xs text-brand-400">{user?.role}</p>
          <button
            onClick={() => logout().then(() => navigate("/login"))}
            className="mt-2 text-xs text-brand-300 hover:text-white transition-colors"
          >
            {t("logout")}
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}