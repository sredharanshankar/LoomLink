import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { qk } from "../../lib/query-keys";
import { formatPaise } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import Card from "../../components/ui/Card";

interface MillSettings {
  mill_name: string;
  timezone: string;
  currency: string;
  idle_rate_paise_per_hour: number;
  overtime_premium_bp: number;
  [key: string]: unknown;
}

function SettingRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between py-3 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-900">{value}</span>
    </div>
  );
}

export default function SettingsPage() {
  const { data: settings, isLoading } = useQuery({
    queryKey: qk.settings(),
    queryFn: () => api.get<MillSettings>("/settings"),
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <PageHeader title="Settings" />
        <Skeleton rows={6} />
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="p-6">
        <PageHeader title="Settings" subtitle="Could not load settings" />
      </div>
    );
  }

  return (
    <div className="p-6">
      <PageHeader title="Settings" subtitle="Read-only view of mill configuration" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">General</h2>
          <SettingRow label="Mill Name" value={settings.mill_name} />
          <SettingRow label="Timezone" value={settings.timezone} />
          <SettingRow label="Currency" value={settings.currency} />
        </Card>
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Rates</h2>
          <SettingRow label="Idle Rate (per hour)" value={formatPaise(settings.idle_rate_paise_per_hour)} />
          <SettingRow label="Overtime Premium" value={`${settings.overtime_premium_bp / 100}%`} />
        </Card>
      </div>
    </div>
  );
}
