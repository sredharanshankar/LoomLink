import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../lib/auth";
import { api } from "../../lib/api";
import { formatPaise, formatCm } from "../../lib/format";
import { qk } from "../../lib/query-keys";
import KpiTile from "../../components/ui/KpiTile";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import Badge from "../../components/ui/Badge";

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

interface ProductionDashboard {
  as_of: string;
  active_jobs: { stage: string; total: number; running: number; paused: number; blocked: number }[];
  floor_map: {
    code: string;
    stage: string;
    status: string;
    floor_x: number;
    floor_y: number;
    current_job: string | null;
    order_code: string | null;
  }[];
  today_output: { stage: string; produced_cm: number }[];
  attendance: Record<string, number>;
}

const MACHINE_STATUS_COLOR: Record<string, "green" | "yellow" | "red" | "blue" | "gray"> = {
  running: "green",
  idle: "yellow",
  breakdown: "red",
  maintenance: "blue",
  changeover: "yellow",
  offline: "gray",
};

const PRODUCTION_ROLES = ["operator", "qc_inspector", "supervisor", "dispatch"];

// ─── Operator / production floor dashboard ───────────────────────────────────
function OperatorDashboard({ name }: { name: string }) {
  const { data, isLoading, isError } = useQuery<ProductionDashboard>({
    queryKey: ["dashboard", "production"],
    queryFn: () => api.get("/dashboard/production"),
    refetchInterval: 30_000,
  });

  const totalRunning = data?.active_jobs.reduce((s, j) => s + j.running, 0) ?? 0;
  const totalJobs = data?.active_jobs.reduce((s, j) => s + j.total, 0) ?? 0;
  const machinesActive = data?.floor_map.filter((m) => m.status === "running").length ?? 0;
  const totalOutputCm = data?.today_output.reduce((s, r) => s + r.produced_cm, 0) ?? 0;

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="Production Dashboard" subtitle={`Welcome, ${name}`} />

      {isLoading && <Skeleton rows={6} />}

      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          Failed to load production data.
        </div>
      )}

      {data && (
        <>
          {/* KPI row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <KpiTile label="Jobs running" value={totalRunning} trend={totalRunning > 0 ? "up" : "neutral"} />
            <KpiTile label="Total active jobs" value={totalJobs} />
            <KpiTile label="Machines running" value={machinesActive} trend={machinesActive > 0 ? "up" : "neutral"} />
            <KpiTile label="Today's output" value={formatCm(totalOutputCm)} />
          </div>

          {/* Jobs by stage */}
          {data.active_jobs.length > 0 && (
            <section>
              <h2 className="text-base font-semibold text-gray-800 mb-3">Active Jobs by Stage</h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {data.active_jobs.map((j) => (
                  <div key={j.stage} className="bg-white rounded-lg border border-gray-200 p-4">
                    <p className="text-xs text-gray-500 uppercase tracking-wide capitalize mb-2">{j.stage}</p>
                    <div className="flex gap-3 text-sm">
                      <span className="text-green-700 font-semibold">{j.running} running</span>
                      {j.paused > 0 && <span className="text-amber-600">{j.paused} paused</span>}
                      {j.blocked > 0 && <span className="text-red-600">{j.blocked} blocked</span>}
                    </div>
                    <p className="text-xs text-gray-400 mt-1">{j.total} total</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Machine ↔ Job ↔ Order table */}
          <section>
            <h2 className="text-base font-semibold text-gray-800 mb-3">Machines — Current Assignment</h2>
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Machine</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Stage</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Current Job</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Order</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.floor_map.map((m) => (
                    <tr key={m.code} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{m.code}</td>
                      <td className="px-4 py-3 text-sm text-gray-600 capitalize">{m.stage}</td>
                      <td className="px-4 py-3 text-sm">
                        <Badge color={MACHINE_STATUS_COLOR[m.status] ?? "gray"}>
                          {m.status.replace(/_/g, " ")}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-sm font-mono text-gray-700">
                        {m.current_job ?? <span className="text-gray-300 italic">—</span>}
                      </td>
                      <td className="px-4 py-3 text-sm font-medium text-blue-700">
                        {m.order_code ?? <span className="text-gray-300 italic">—</span>}
                      </td>
                    </tr>
                  ))}
                  {data.floor_map.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-gray-400 text-sm">
                        No machines configured yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          {/* Today's output by stage */}
          {data.today_output.length > 0 && (
            <section>
              <h2 className="text-base font-semibold text-gray-800 mb-3">Today's Output by Stage</h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {data.today_output.map((r) => (
                  <div key={r.stage} className="bg-white rounded-lg border border-gray-200 p-4">
                    <p className="text-xs text-gray-500 uppercase tracking-wide capitalize mb-1">{r.stage}</p>
                    <p className="text-lg font-bold text-gray-900">{formatCm(r.produced_cm)}</p>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

// ─── Owner / Manager dashboard ───────────────────────────────────────────────
function OwnerDashboard({ name }: { name: string }) {
  const { t } = useTranslation();

  const { data, isLoading } = useQuery({
    queryKey: qk.dashboard(),
    queryFn: () => api.get<DashboardData>("/dashboard/owner"),
  });

  return (
    <div className="p-6 space-y-6">
      <PageHeader title={t("dashboard")} subtitle={`Welcome, ${name}`} />
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

// ─── Root ─────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { user } = useAuth();
  const name = user?.full_name ?? "";

  if (PRODUCTION_ROLES.includes(user?.role ?? "")) {
    return <OperatorDashboard name={name} />;
  }

  return <OwnerDashboard name={name} />;
}
