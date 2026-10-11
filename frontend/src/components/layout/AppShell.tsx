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

  const isBuyer = user?.role === "buyer";

  const BUYER_NAV_GROUPS: { label: string; items: NavItem[] }[] = [
    {
      label: "overview",
      items: [{ to: "/app/dashboard", key: "dashboard", icon: LayoutDashboard, perm: null }],
    },
    {
      label: "orders",
      items: [{ to: "/app/buyer-portal", key: "myOrders", icon: ShoppingCart, perm: null }],
    },
  ];

  const filteredGroups = isBuyer
    ? BUYER_NAV_GROUPS
    : NAV_GROUPS.map((g) => ({
        ...g,
        items: g.items.filter((item) => item.perm === null || can(user?.role, item.perm)),
      })).filter((g) => g.items.length > 0);

  const initials = user?.full_name
    ? user.full_name.split(" ").slice(0, 2).map((w) => w[0]).join("").toUpperCase()
    : "?";

  const sidebarContent = (
    <>
      {/* Logo */}
      <div className="h-14 px-4 flex items-center justify-between shrink-0 border-b border-white/[0.07]">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-brand-500 flex items-center justify-center shrink-0 shadow-lg shadow-brand-900/50">
            <span className="text-white font-bold text-xs leading-none">L</span>
          </div>
          <span className="text-[15px] font-semibold tracking-tight text-white">LoomLink</span>
        </div>
        <button
          className="md:hidden p-1 rounded-md text-white/50 hover:text-white hover:bg-white/10 transition-colors"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close menu"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto sidebar-scroll py-4 px-3 space-y-5">
        {filteredGroups.map((group) => (
          <div key={group.label}>
            <p className="px-2.5 mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-white/30 select-none">
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
                      "flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-colors duration-100",
                      isActive
                        ? "bg-white/[0.12] text-white font-semibold shadow-sm"
                        : "text-white/60 hover:bg-white/[0.06] hover:text-white/90"
                    )
                  }
                >
                  <item.icon className="h-4 w-4 shrink-0 opacity-90" />
                  {t(item.key)}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* User footer */}
      <div className="border-t border-white/[0.07] px-3 py-3 shrink-0">
        <div className="flex items-center gap-2.5 px-1">
          <div className="w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center text-white text-[11px] font-semibold shrink-0 ring-2 ring-white/10">
            {initials}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs text-white/80 font-medium truncate">{user?.full_name}</p>
            <p className="text-[10px] text-white/40 capitalize">{user?.role?.replace(/_/g, " ")}</p>
          </div>
          <button
            onClick={() => logout().then(() => navigate("/login"))}
            className="p-1.5 rounded-md text-white/40 hover:text-white hover:bg-white/10 transition-colors shrink-0"
            aria-label={t("logout")}
          >
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-[#0d1117]">
      {/* Sidebar desktop */}
      <aside className="hidden md:flex md:flex-col w-60 bg-brand-900 shrink-0">
        {sidebarContent}
      </aside>

      {/* Sidebar mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
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
        <header className="h-14 shrink-0 bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 flex items-center gap-3 px-4">
          <button
            className="md:hidden p-1.5 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-800 transition-colors"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Search */}
          <div className="flex items-center gap-2 rounded-lg border border-gray-200 dark:border-gray-700/60 bg-gray-50 dark:bg-gray-900 px-3 h-9 flex-1 max-w-xs text-sm focus-within:border-brand-400 dark:focus-within:border-brand-500 transition-colors">
            <Search className="h-3.5 w-3.5 text-gray-400 shrink-0" />
            <input
              className="flex-1 bg-transparent outline-none text-gray-700 dark:text-gray-300 placeholder:text-gray-400 dark:placeholder:text-gray-600 text-sm"
              placeholder={`${t("search")}…`}
              aria-label={t("search")}
            />
            <kbd className="hidden sm:inline text-[10px] text-gray-400 dark:text-gray-600 border border-gray-300 dark:border-gray-700 rounded px-1 py-0.5 font-mono">/</kbd>
          </div>

          <div className="flex items-center gap-1 ml-auto">
            <LiveIndicator />

            {/* Language */}
            <div className="relative">
              <button
                className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 px-2 py-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                onClick={() => setLangOpen((o) => !o)}
                aria-label="Language"
                aria-expanded={langOpen}
              >
                <Globe className="h-4 w-4" />
                <span className="hidden sm:inline uppercase font-medium text-[11px]">{i18n.language.slice(0, 2)}</span>
                <ChevronDown className="h-3 w-3 opacity-60" />
              </button>
              {langOpen && (
                <div
                  className="absolute right-0 mt-1.5 w-36 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg dark:shadow-black/30 z-50 py-1 overflow-hidden"
                  role="menu"
                >
                  {LANGS.map((l) => (
                    <button
                      key={l.code}
                      role="menuitem"
                      className={clsx(
                        "w-full text-left px-3 py-2 text-sm transition-colors",
                        i18n.language === l.code
                          ? "bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300 font-medium"
                          : "text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
                      )}
                      onClick={() => { i18n.changeLanguage(l.code); setLangOpen(false); }}
                    >
                      {l.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Notifications */}
            <button
              className="p-1.5 rounded-lg text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label={t("notifications", "Notifications")}
            >
              <Bell className="h-4.5 w-4.5" style={{ width: "1.125rem", height: "1.125rem" }} />
            </button>

            {/* Dark mode toggle */}
            <button
              onClick={toggleDark}
              className="p-1.5 rounded-lg text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
            >
              {dark ? <Sun className="h-4.5 w-4.5" style={{ width: "1.125rem", height: "1.125rem" }} /> : <Moon className="h-4.5 w-4.5" style={{ width: "1.125rem", height: "1.125rem" }} />}
            </button>

            {/* User avatar */}
            <div className="ml-1 w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center text-white text-[11px] font-semibold cursor-default ring-2 ring-brand-200 dark:ring-brand-800" title={user?.full_name}>
              {initials}
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto scrollbar-thin">
          <Outlet />
        </main>
      </div>

      <RippleLiveToaster />
    </div>
  );
}
