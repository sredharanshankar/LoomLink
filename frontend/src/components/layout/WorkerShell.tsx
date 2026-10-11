import { Outlet, NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Home, ScanLine, Briefcase, Bell, User } from "lucide-react";
import { clsx } from "clsx";

const BOTTOM_NAV = [
  { to: "/w",        key: "home",   icon: Home,      end: true  },
  { to: "/w/scan",   key: "scan",   icon: ScanLine,  end: false },
  { to: "/w/jobs",   key: "myJobs", icon: Briefcase, end: false },
  { to: "/w/alerts", key: "alerts", icon: Bell,      end: false },
  { to: "/w/me",     key: "me",     icon: User,      end: false },
];

export default function WorkerShell() {
  const { t } = useTranslation();

  return (
    <div className="worker-shell flex flex-col min-h-screen bg-white">
      <div className="flex-1 pb-16 overflow-y-auto">
        <Outlet />
      </div>

      <nav
        className="fixed bottom-0 inset-x-0 h-16 bg-white border-t border-gray-200 flex items-center z-30"
        aria-label={t("navigation", "Navigation")}
      >
        {BOTTOM_NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              clsx(
                "flex-1 flex flex-col items-center justify-center gap-0.5 py-2 text-xs transition-colors",
                isActive ? "text-brand-700 font-semibold" : "text-gray-500"
              )
            }
          >
            {({ isActive }) => (
              <>
                <item.icon
                  className={clsx("h-6 w-6", isActive ? "text-brand-700" : "text-gray-500")}
                  strokeWidth={isActive ? 2.5 : 2}
                />
                <span>{t(item.key)}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
