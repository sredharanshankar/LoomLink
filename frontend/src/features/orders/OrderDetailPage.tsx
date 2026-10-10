import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatCm, formatDate, formatDateTime } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Badge from "../../components/ui/Badge";
import KpiTile from "../../components/ui/KpiTile";
import Skeleton from "../../components/ui/Skeleton";

interface Job {
  id: string;
  code: string;
  stage: string;
  status: string;
  planned_qty: number;
  produced_qty: number;
  machine?: string;
}

interface Roll {
  id: string;
  code: string;
  length_cm: number;
  grade: string;
}

interface OrderDetail {
  id: string;
  code: string;
  buyer_name: string;
  fabric_type_name: string;
  quantity_cm: number;
  status: string;
  due_date: string;
  created_at: string;
  route_stages: string[];
  jobs: Job[];
  rolls: Roll[];
}

interface HealthResponse {
  health: "green" | "amber" | "red";
  slack_minutes: number;
  predicted_dispatch_at: string;
}

const STATUS_COLORS: Record<string, "blue" | "yellow" | "purple" | "green" | "gray"> = {
  confirmed: "blue",
  in_production: "yellow",
  qc: "purple",
  ready: "green",
  dispatched: "gray",
};

const HEALTH_COLORS: Record<string, "green" | "yellow" | "red"> = {
  green: "green",
  amber: "yellow",
  red: "red",
};

function formatStatus(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: order, isLoading, isError } = useQuery<OrderDetail>({
    queryKey: ["order", id],
    queryFn: () => api.get(`/orders/${id}`),
    enabled: !!id,
  });

  const { data: health } = useQuery<HealthResponse>({
    queryKey: ["order-health", id],
    queryFn: () => api.get(`/ripple/orders/${id}/health`),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-6"><Skeleton rows={10} /></div>;
  if (isError || !order) {
    return (
      <div className="p-6">
        <div className="bg-red-50 text-red-700 rounded-lg border border-red-200 p-4">
          Failed to load order.
        </div>
      </div>
    );
  }

  const producedTotal = order.jobs.reduce((sum, j) => sum + j.produced_qty, 0);

  return (
    <div className="p-6">
      <PageHeader
        title={order.code}
        subtitle={`${order.buyer_name} — ${order.fabric_type_name}`}
        actions={
          <div className="flex items-center gap-3">
            {health && (
              <Badge color={HEALTH_COLORS[health.health] ?? "gray"}>
                {health.health.toUpperCase()}
              </Badge>
            )}
            <Badge color={STATUS_COLORS[order.status] ?? "gray"}>
              {formatStatus(order.status)}
            </Badge>
            <Link to="/app/orders" className="text-sm text-gray-500 hover:text-gray-700">
              Back to Orders
            </Link>
          </div>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <KpiTile label="Quantity" value={formatCm(order.quantity_cm)} />
        <KpiTile label="Due Date" value={formatDate(order.due_date)} />
        <KpiTile
          label="Produced So Far"
          value={formatCm(producedTotal)}
          sub={order.quantity_cm > 0 ? `${Math.round((producedTotal / order.quantity_cm) * 100)}%` : undefined}
        />
        <KpiTile
          label="Health"
          value={health ? health.health.toUpperCase() : "—"}
          sub={health ? `${health.slack_minutes}min slack` : undefined}
          trend={health?.health === "green" ? "up" : health?.health === "red" ? "down" : "neutral"}
        />
      </div>

      <section className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Jobs</h2>
        {order.jobs.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-6 text-center text-gray-400">
            No jobs created yet.
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stage</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Progress</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Machine</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {order.jobs.map((job) => {
                  const pct = job.planned_qty > 0 ? Math.min(100, Math.round((job.produced_qty / job.planned_qty) * 100)) : 0;
                  return (
                    <tr key={job.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{job.code}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{formatStatus(job.stage)}</td>
                      <td className="px-4 py-3 text-sm">
                        <Badge color={STATUS_COLORS[job.status] ?? "gray"}>
                          {formatStatus(job.status)}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-500 rounded-full"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500">{pct}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">{job.machine ?? "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {order.rolls.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Rolls</h2>
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Length</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grade</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {order.rolls.map((roll) => (
                  <tr key={roll.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{roll.code}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{formatCm(roll.length_cm)}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{roll.grade}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <div className="mt-6 text-xs text-gray-400">
        Created {formatDateTime(order.created_at)}
      </div>
    </div>
  );
}
