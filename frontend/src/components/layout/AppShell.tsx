import { useState } from "react";
import { Outlet, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  LayoutDashboard, LayoutGrid, Zap, Package, Truck, ClipboardList, ShoppingBag, Building2,
  Activity, Cog, ShieldCheck, PackageCheck, Users, CalendarCheck, Banknote, Landmark,
  CreditCard, Receipt, Wallet, Settings2, UserCog, ScrollText,
  Bell, Search, Sun, Moon, Wifi, WifiOff, RefreshCw, Menu, X, Globe, LogOut, ChevronDown, Check,
} from "lucide-react";
import { useAuth } from "../../lib/auth";
import { can } from "../../lib/permissions";
import { useDarkMode } from "../../lib/dark-mode";
import { useLiveStatus } from "../../lib/live-status";
import { RippleLiveToaster } from "../../features/ripple/index";
import { clsx } from "clsx";
import i18n from "../../lib/i18n";
import Logo from "../ui/Logo";

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
      { to: "/app/floor",     key: "floor",     icon: LayoutGrid,      perm: "production:read" },
      { to: "/app/ripple",    key: "ripple",    icon: Zap,             perm: "ripple:read" },
    ],
  },
  {
    label: "inventory",
    items: [
      { to: "/app/inventory",       key: "inventory",      icon: Package,       perm: "inventory:read" },
      { to: "/app/suppliers",       key: "suppliers",      icon: Truck,         perm: "inventory:read" },
      { to: "/app/purchase-orders", key: "purchaseOrders", icon: ClipboardList, perm: "inventory:read" },
    ],
  },
  {
    label: "orders",
    items: [
      { to: "/app/orders", key: "orders", icon: ShoppingBag, perm: "orders:read" },
      { to: "/app/buyers", key: "buyers", icon: Building2,   perm: "orders:read" },
    ],
  },
  {
    label: "production",
    items: [
      { to: "/app/production", key: "production", icon: Activity, perm: "production:read" },
      { to: "/app/machines",   key: "machines",   icon: Cog,      perm: "production:read" },
    ],
  },
  {
    label: "quality",
    items: [{ to: "/app/quality", key: "quality", icon: ShieldCheck, perm: "quality:read" }],
  },
  {
    label: "dispatch",
    items: [{ to: "/app/dispatch", key: "dispatch", icon: PackageCheck, perm: "dispatch:read" }],
  },
  {
    label: "workers",
    items: [
      { to: "/app/workers",    key: "workers",    icon: Users,         perm: "workers:read" },
      { to: "/app/attendance", key: "attendance", icon: CalendarCheck, perm: "workers:read" },
      { to: "/app/payroll",    key: "payroll",    icon: Banknote,      perm: "finance:read" },
    ],
  },
  {
    label: "finance",
    items: [
      { to: "/app/finance",        key: "finance",       icon: Landmark,   perm: "finance:read" },
      { to: "/app/payments",       key: "payments",      icon: CreditCard, perm: "finance:read" },
      { to: "/app/supplier-bills", key: "supplierBills", icon: Receipt,    perm: "finance:read" },
      { to: "/app/expenses",       key: "expenses",      icon: Wallet,     perm: "finance:read" },
    ],
  },
  {
    label: "admin",
    items: [
      { to: "/app/settings", key: "settings", icon: Settings2,  perm: "admin:read" },
      { to: "/app/users",    key: "users",    icon: UserCog,    perm: "admin:read" },
      { to: "/app/audit",    key: "audit",    icon: ScrollText, perm: "admin:read" },
    ],
  },
];

const BUYER_NAV_GROUPS: { label: string; items: NavItem[] }[] = [
  { label: "overview", items: [{ to: "/app/dashboard", key: "dashboard", icon: LayoutDashboard, perm: null }] },
  { label: "orders", items: [{ to: "/app/buyer-portal", key: "myOrders", icon: ShoppingBag, perm: null }] },
];

function LiveIndicator() {
  const status = useLiveStatus();
  const cfg = {
    connected: { label: "Live", icon: Wifi, cls: "text-emerald-700 bg-emerald-50 ring-emerald-600/20", dot: "bg-emerald-500" },
    reconnecting: { label: "Reconnecting", icon: RefreshCw, cls: "text-amber-700 bg-amber-50 ring-amber-600/20", dot: "bg-amber-500" },
  }[status as "connected" | "reconnecting"] ?? {
    label: "Offline", icon: WifiOff, cls: "text-red-700 bg-red-50 ring-red-600/20", dot: "bg-red-500",
  };
  return (
    <span className={clsx("hidden sm:inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset", cfg.cls)}>
      <span className="relative flex h-1.5 w-1.5">
        {status === "connected" && <span className={clsx("absolute inline-flex h-full w-full animate-ping rounded-full opacity-70", cfg.dot)} />}
        <span className={clsx("relative inline-flex h-1.5 w-1.5 rounded-full", cfg.dot)} />
      </span>
      {cfg.label}
    </span>
  );
}

const iconBtn =
  "flex h-9 w-9 items-center justify-center rounded-lg text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900";

export default function AppShell() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { dark, toggle: toggleDark } = useDarkMode();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);

  const filteredGroups = user?.role === "buyer"
    ? BUYER_NAV_GROUPS
    : NAV_GROUPS.map((g) => ({
        ...g,
        items: g.items.filter((item) => item.perm === null || can(user?.role, item.perm)),
      })).filter((g) => g.items.length > 0);

  const initials = user?.full_name
    ? user.full_name.split(" ").slice(0, 2).map((w) => w[0]).join("").toUpperCase()
    : "?";
  const roleLabel = user?.role?.replace(/_/g, " ");

  const sidebarContent = (
    <>
      <div className="flex h-16 shrink-0 items-center justify-between px-5 text-white">
        <Logo />
        <button
          className="rounded-md p-1 text-white/50 transition-colors hover:bg-white/10 hover:text-white md:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close menu"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <nav className="sidebar-scroll flex-1 space-y-6 overflow-y-auto px-3 pb-6 pt-2" aria-label="Main">
        {filteredGroups.map((group) => (
          <div key={group.label}>
            <p className="mb-1.5 select-none px-3 text-[10.5px] font-semibold uppercase tracking-[0.14em] text-white/35">
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
                      "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-[13.5px] transition-all duration-150",
                      isActive
                        ? "bg-white/[0.09] font-medium text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
                        : "text-white/60 hover:bg-white/[0.05] hover:text-white",
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      <span
                        className={clsx(
                          "absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-indigo-400 transition-opacity",
                          isActive ? "opacity-100" : "opacity-0",
                        )}
                      />
                      <item.icon
                        className={clsx("h-[17px] w-[17px] shrink-0", isActive ? "text-indigo-300" : "text-white/45 group-hover:text-white/80")}
                        strokeWidth={1.9}
                      />
                      {t(item.key)}
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="shrink-0 border-t border-white/[0.06] p-3">
        <div className="flex items-center gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-white/[0.04]">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-400 to-violet-500 text-[11px] font-semibold text-white ring-2 ring-white/10">
            {initials}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[13px] font-medium text-white/90">{user?.full_name}</p>
            <p className="truncate text-[11px] capitalize text-white/45">{roleLabel}</p>
          </div>
          <button
            onClick={() => logout().then(() => navigate("/login"))}
            className="rounded-md p-1.5 text-white/40 transition-colors hover:bg-white/10 hover:text-white"
            aria-label={t("logout")}
            title={t("logout")}
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </>
  );

  const sidebarSurface =
    "theme-light flex flex-col bg-[#0b0f1e] bg-[radial-gradient(120%_60%_at_0%_0%,rgba(99,102,241,0.18),transparent_60%)]";

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <aside className={clsx("hidden w-[var(--sidebar-width)] shrink-0 md:flex", sidebarSurface)}>
        {sidebarContent}
      </aside>

      {sidebarOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="absolute inset-0 animate-fade-in bg-black/60 backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
          <aside className={clsx("relative z-50 h-full w-72 animate-fade-in", sidebarSurface)}>
            {sidebarContent}
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center gap-3 border-b border-gray-200/80 bg-surface/80 px-4 backdrop-blur-xl sm:px-6">
          <button className={clsx(iconBtn, "md:hidden")} onClick={() => setSidebarOpen(true)} aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </button>

          <Logo subtitle={false} className="text-gray-900 sm:hidden" />

          <label className="group hidden h-9 max-w-md flex-1 items-center gap-2 sm:flex rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm transition focus-within:border-brand-500 focus-within:bg-surface focus-within:ring-4 focus-within:ring-brand-500/10">
            <Search className="h-4 w-4 shrink-0 text-gray-400" />
            <input
              className="min-w-0 flex-1 bg-transparent text-sm text-gray-800 outline-none placeholder:text-gray-400"
              placeholder={`${t("search")}…`}
              aria-label={t("search")}
            />
            <kbd className="hidden rounded border border-gray-200 bg-surface px-1.5 py-0.5 font-mono text-[10px] text-gray-400 sm:inline">/</kbd>
          </label>

          <div className="ml-auto flex items-center gap-1.5">
            <LiveIndicator />

            <div className="relative">
              <button
                className="flex h-9 items-center gap-1.5 rounded-lg px-2.5 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900"
                onClick={() => setLangOpen((o) => !o)}
                aria-label="Language"
                aria-expanded={langOpen}
              >
                <Globe className="h-[18px] w-[18px]" />
                <span className="hidden text-xs font-semibold uppercase sm:inline">{i18n.language.slice(0, 2)}</span>
                <ChevronDown className="h-3 w-3 opacity-60" />
              </button>
              {langOpen && (
                <>
                  <button className="fixed inset-0 z-40 cursor-default" aria-hidden="true" tabIndex={-1} onClick={() => setLangOpen(false)} />
                  <div
                    className="absolute right-0 z-50 mt-2 w-44 animate-fade-up overflow-hidden rounded-xl border border-gray-200 bg-surface p-1 shadow-pop"
                    role="menu"
                  >
                    {LANGS.map((l) => {
                      const active = i18n.language.startsWith(l.code);
                      return (
                        <button
                          key={l.code}
                          role="menuitem"
                          className={clsx(
                            "flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition-colors",
                            active ? "bg-brand-50 font-medium text-brand-700" : "text-gray-700 hover:bg-gray-50",
                          )}
                          onClick={() => { i18n.changeLanguage(l.code); setLangOpen(false); }}
                        >
                          {l.label}
                          {active && <Check className="h-4 w-4" />}
                        </button>
                      );
                    })}
                  </div>
                </>
              )}
            </div>

            <button className={clsx(iconBtn, "relative")} aria-label={t("notifications", "Notifications")}>
              <Bell className="h-[18px] w-[18px]" />
            </button>

            <button
              onClick={toggleDark}
              className={iconBtn}
              aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
              title={dark ? "Light mode" : "Dark mode"}
            >
              {dark ? <Sun className="h-[18px] w-[18px]" /> : <Moon className="h-[18px] w-[18px]" />}
            </button>

            <div className="ml-1.5 hidden h-6 w-px bg-gray-200 sm:block" />

            <div className="ml-1.5 flex items-center gap-2.5" title={user?.full_name}>
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-violet-500 text-[11px] font-semibold text-white shadow-sm">
                {initials}
              </div>
              <div className="hidden leading-tight lg:block">
                <p className="text-[13px] font-medium text-gray-900">{user?.full_name}</p>
                <p className="text-[11px] capitalize text-gray-500">{roleLabel}</p>
              </div>
            </div>
          </div>
        </header>

        <main className="scrollbar-thin flex-1 overflow-y-auto">
          <div key={location.pathname} className="mx-auto w-full max-w-[1440px] animate-fade-up">
            <Outlet />
          </div>
        </main>
      </div>

      <RippleLiveToaster />
    </div>
  );
}
