import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../lib/auth";
import { api } from "../../lib/api";
import { formatPaise, formatCm } from "../../lib/format";
import { qk } from "../../lib/query-keys";
import KpiTile from "../../components/ui/KpiTile";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";

interface DashboardData {
  orders_due_7d?: number;
  orders_at_risk?: number;
  today_output_cm?: number;
  cash_in_mtd_paise?: number;
  receivables_paise?: number;
  low_stock_count?: number;
  jobs_running?: number;
  rolls_in_qc?: number;
  dispatches_today?: number;
  orders_today?: number;
}

export default function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();

  const endpoint = user?.role === "owner" || user?.role === "manager"
    ? "/dashboard/owner"
    : "/dashboard";

  const { data, isLoading } = useQuery({
    queryKey: qk.dashboard(),
    queryFn: () => api.get<DashboardData>(endpoint),
  });

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title={t("dashboard")}
        subtitle={`Welcome, ${user?.full_name}`}
      />
      {isLoading ? (
        <Skeleton rows={4} className="max-w-sm" />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiTile label="Orders due (7 d)" value={data?.orders_due_7d ?? data?.orders_today ?? "-"} />
          <KpiTile label="Jobs running" value={data?.jobs_running ?? "-"} />
          <KpiTile label="Rolls in QC" value={data?.rolls_in_qc ?? "-"} />
          <KpiTile label="Dispatches today" value={data?.dispatches_today ?? "-"} />
          {data?.today_output_cm != null && (
            <KpiTile label="Today output" value={formatCm(data.today_output_cm)} />
          )}
          {data?.cash_in_mtd_paise != null && (
            <KpiTile label="Cash in (MTD)" value={formatPaise(data.cash_in_mtd_paise)} />
          )}
          {data?.receivables_paise != null && (
            <KpiTile label="Receivables" value={formatPaise(data.receivables_paise)} />
          )}
          {data?.low_stock_count != null && (
            <KpiTile
              label="Low stock alerts"
              value={data.low_stock_count}
              trend={data.low_stock_count > 0 ? "down" : "neutral"}
            />
          )}
        </div>
      )}
    </div>
  );
}
