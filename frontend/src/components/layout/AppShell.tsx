import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  LayoutDashboard, Factory, Package, ShoppingCart,
  Settings2, Cpu, Shield, Truck, Users, Wallet, Zap,
  Bell, Search, Sun, Moon, Wifi, WifiOff, RefreshCw,
  Menu, X, Globe, LogOut, ChevronDown,
} from "lucide-react";
import { useAuth } from "../../lib/auth";
import { can } from "../../lib/permissions";
import { useDarkMode } from "../../lib/dark-mode";
import { useLiveStatus } from "../../lib/live-status";
import { RippleLiveToaster } from "../../features/ripple/index";
import { clsx } from "clsx";
import i18n from "../../lib/i18n";

const LANGS = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिंदी" },
  { code: "te", label: "తెలుగు" },
  { code: "ta", label: "தமிழ்" },
];

type Perm = Parameters<typeof can>[1];

type NavItem = {
  to: string;
  key: string;
  icon: React.ElementType;
  perm: Perm | null;
};

const NAV_GROUPS: { label: string; items: NavItem[] }[] = [
  {
    label: "overview",
    items: [
      { to: "/app/dashboard", key: "dashboard", icon: LayoutDashboard, perm: null },
      { to: "/app/floor",     key: "floor",     icon: Factory,          perm: "production:read" },
      { to: "/app/ripple",    key: "ripple",    icon: Zap,              perm: "ripple:read" },
    ],
  },
  {
    label: "inventory",
    items: [
      { to: "/app/inventory",       key: "inventory",      icon: Package,      perm: "inventory:read" },
      { to: "/app/suppliers",       key: "suppliers",      icon: Truck,        perm: "inventory:read" },
      { to: "/app/purchase-orders", key: "purchaseOrders", icon: ShoppingCart, perm: "inventory:read" },
    ],
  },
  {
    label: "orders",
    items: [
      { to: "/app/orders", key: "orders", icon: ShoppingCart, perm: "orders:read" },
      { to: "/app/buyers", key: "buyers", icon: Users,        perm: "orders:read" },
    ],
  },
  {
    label: "production",
    items: [
      { to: "/app/production", key: "production", icon: Cpu,     perm: "production:read" },
      { to: "/app/machines",   key: "machines",   icon: Factory, perm: "production:read" },
    ],
  },
  {
    label: "quality",
    items: [
      { to: "/app/quality", key: "quality", icon: Shield, perm: "quality:read" },
    ],
  },
  {
    label: "dispatch",
    items: [
      { to: "/app/dispatch", key: "dispatch", icon: Truck, perm: "dispatch:read" },
    ],
  },
  {
    label: "workers",
    items: [
      { to: "/app/workers",    key: "workers",    icon: Users,  perm: "workers:read" },
      { to: "/app/attendance", key: "attendance", icon: Users,  perm: "workers:read" },
      { to: "/app/payroll",    key: "payroll",    icon: Wallet, perm: "workers:read" },
    ],
  },
  {
    label: "finance",
    items: [
      { to: "/app/finance",   key: "finance",   icon: Wallet, perm: "finance:read" },
      { to: "/app/payments",  key: "payments",  icon: Wallet, perm: "finance:read" },
      { to: "/app/supplier-bills", key: "supplierBills", icon: Wallet, perm: "finance:read" },
      { to: "/app/expenses",  key: "expenses",  icon: Wallet, perm: "finance:read" },
    ],
  },
  {
    label: "admin",
    items: [
      { to: "/app/settings", key: "settings", icon: Settings2, perm: "admin:read" },
      { to: "/app/users",    key: "users",    icon: Users,     perm: "admin:read" },
      { to: "/app/audit",    key: "audit",    icon: Shield,    perm: "admin:read" },
    ],
  },
];

function LiveIndicator() {
  const status = useLiveStatus();
  if (status === "connected") return (
    <span className="flex items-center gap-1 text-xs text-green-500 dark:text-green-400">
      <Wifi className="h-3.5 w-3.5" />
      <span className="hidden sm:inline">Live</span>
    </span>
  );
  if (status === "reconnecting") return (
    <span className="flex items-center gap-1 text-xs text-amber-500 dark:text-amber-400 animate-pulse">
      <RefreshCw className="h-3.5 w-3.5" />
      <span className="hidden sm:inline">Reconnecting</span>
    </span>
  );
  return (
    <span className="flex items-center gap-1 text-xs text-red-500 dark:text-red-400">
      <WifiOff className="h-3.5 w-3.5" />
      <span className="hidden sm:inline">Offline</span>
    </span>
  );
}

export default function AppShell() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { dark, toggle: toggleDark } = useDarkMode();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);

  const filteredGroups = NAV_GROUPS.map((g) => ({
    ...g,
    items: g.items.filter((item) => item.perm === null || can(user?.role, item.perm)),
  })).filter((g) => g.items.length > 0);

  const sidebarContent = (
    <>
      <div className="px-5 py-4 border-b border-brand-800 flex items-center justify-between shrink-0">
        <span className="text-lg font-bold tracking-tight text-white">LoomLink</span>
        <button
          className="md:hidden text-brand-300 hover:text-white"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close menu"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto scrollbar-thin py-3 px-2 space-y-4">
        {filteredGroups.map((group) => (
          <div key={group.label}>
            <p className="px-3 mb-1 text-[10px] font-semibold uppercase tracking-wider text-brand-400">
              {t(group.label, group.label)}
            </p>
            <div className="space-y-0.5">
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) =>
                    clsx(
                      "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors",
                      isActive
                        ? "bg-brand-700 text-white font-medium"
                        : "text-brand-200 hover:bg-brand-800 hover:text-white"
                    )
                  }
                >
                  <item.icon className="h-4 w-4 shrink-0" />
                  {t(item.key)}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-brand-800 px-4 py-3 shrink-0">
        <p className="text-xs text-brand-200 font-medium truncate">{user?.full_name}</p>
        <p className="text-xs text-brand-400 capitalize">{user?.role?.replace(/_/g, " ")}</p>
        <button
          onClick={() => logout().then(() => navigate("/login"))}
          className="mt-1.5 flex items-center gap-1.5 text-xs text-brand-300 hover:text-white transition-colors"
        >
          <LogOut className="h-3.5 w-3.5" />
          {t("logout")}
        </button>
      </div>
    </>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950">
      {/* Sidebar desktop */}
      <aside className="hidden md:flex md:flex-col w-56 bg-brand-900 shrink-0">
        {sidebarContent}
      </aside>

      {/* Sidebar mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
          <aside className="relative z-50 flex flex-col h-full w-64 bg-brand-900">
            {sidebarContent}
          </aside>
        </div>
      )}

      <div className="flex flex-col flex-1 min-w-0">
        {/* Top bar */}
        <header className="h-14 shrink-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex items-center gap-3 px-4">
          <button
            className="md:hidden text-gray-500 hover:text-gray-700 dark:text-gray-400"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="flex items-center gap-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-3 h-9 flex-1 max-w-sm text-sm focus-within:border-brand-500">
            <Search className="h-4 w-4 text-gray-400 shrink-0" />
            <input
              className="flex-1 bg-transparent outline-none text-gray-700 dark:text-gray-200 placeholder:text-gray-400"
              placeholder={`${t("search")} orders…`}
              aria-label={t("search")}
            />
            <kbd className="hidden sm:inline text-[10px] text-gray-400 border border-gray-300 dark:border-gray-600 rounded px-1">/</kbd>
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <LiveIndicator />

            <div className="relative">
              <button
                className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 px-2 py-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
                onClick={() => setLangOpen((o) => !o)}
                aria-label="Language"
                aria-expanded={langOpen}
              >
                <Globe className="h-4 w-4" />
                <span className="hidden sm:inline uppercase">{i18n.language.slice(0, 2)}</span>
                <ChevronDown className="h-3 w-3" />
              </button>
              {langOpen && (
                <div
                  className="absolute right-0 mt-1 w-36 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 py-1"
                  role="menu"
                >
                  {LANGS.map((l) => (
                    <button
                      key={l.code}
                      role="menuitem"
                      className={clsx(
                        "w-full text-left px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700",
                        i18n.language === l.code
                          ? "text-brand-700 dark:text-brand-300 font-medium"
                          : "text-gray-700 dark:text-gray-200"
                      )}
                      onClick={() => { i18n.changeLanguage(l.code); setLangOpen(false); }}
                    >
                      {l.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <button
              className="relative p-1.5 rounded-md text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800"
              aria-label={t("notifications", "Notifications")}
            >
              <Bell className="h-5 w-5" />
            </button>

            <button
              onClick={toggleDark}
              className="p-1.5 rounded-md text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800"
              aria-label={dark ? "Light mode" : "Dark mode"}
            >
              {dark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>

      <RippleLiveToaster />
    </div>
  );
}
