import { useTranslation } from "react-i18next";
import { useAuth } from "../../../lib/auth";

export default function WorkerMePage() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="rounded-xl bg-gray-50 border border-gray-200 p-4">
        <p className="text-base font-semibold text-gray-900">{user?.full_name}</p>
        <p className="text-sm text-gray-500 capitalize mt-0.5">{user?.role?.replace(/_/g, " ")}</p>
        <p className="text-xs text-gray-400 mt-0.5">{user?.employee_code}</p>
      </div>

      <button
        onClick={() => logout()}
        className="w-full py-3 rounded-xl border border-red-200 text-red-600 text-sm font-medium hover:bg-red-50 transition-colors"
      >
        {t("logout", "Log out")}
      </button>
    </div>
  );
}
