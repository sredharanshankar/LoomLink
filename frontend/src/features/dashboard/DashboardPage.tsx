import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
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
  // production dashboard fields
  active_jobs?: { stage: string; total: number; running: number; paused: number; blocked: number }[];
  floor_map?: unknown[];
  today_output?: { stage: string; produced_cm: number }[];
  attendance?: Record<string, number>;
}

export default function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();

  const isBuyer = user?.role === "buyer";
  const useOwnerDash = user?.role === "owner" || user?.role === "manager" || user?.role === "accounts";
  const isOwnerOrManager = useOwnerDash;
  const endpoint = useOwnerDash ? "/dashboard/owner" : "/dashboard/production";

  const { data, isLoading } = useQuery({
    queryKey: qk.dashboard(),
    queryFn: () => api.get<DashboardData>(endpoint),
    enabled: !isBuyer,
  });

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title={t("dashboard")}
        subtitle={`Welcome, ${user?.full_name}`}
      />
      {isBuyer ? (
        <div className="space-y-4">
          <p className="text-gray-600">View your orders and track their progress.</p>
          <Link
            to="/app/orders"
            className="inline-flex items-center gap-2 bg-brand-600 text-white px-4 py-2 rounded-lg hover:bg-brand-700 transition font-medium"
          >
            View My Orders
          </Link>
        </div>
      ) : isLoading ? (
        <Skeleton rows={4} className="max-w-sm" />
      ) : isOwnerOrManager ? (
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
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {(data?.active_jobs ?? []).map((j) => (
              <KpiTile
                key={j.stage}
                label={j.stage.charAt(0).toUpperCase() + j.stage.slice(1)}
                value={`${j.running} running`}
                sub={`${j.total} total${j.paused ? `, ${j.paused} paused` : ""}${j.blocked ? `, ${j.blocked} blocked` : ""}`}
              />
            ))}
          </div>
          {(data?.today_output ?? []).length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Today&apos;s Output</h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {(data?.today_output ?? []).map((o) => (
                  <KpiTile key={o.stage} label={o.stage} value={formatCm(o.produced_cm)} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
