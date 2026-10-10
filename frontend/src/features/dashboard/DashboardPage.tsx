import { useTranslation } from "react-i18next";
import { useAuth } from "../../lib/auth";
import Card from "../../components/ui/Card";

export default function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t("dashboard")}</h1>
        <p className="text-gray-500 mt-1">Welcome, {user?.full_name}</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {["Orders", "Jobs", "Rolls", "Dispatches"].map((label) => (
          <Card key={label}>
            <p className="text-sm text-gray-500">{label}</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">-</p>
          </Card>
        ))}
      </div>
    </div>
  );
}