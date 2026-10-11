import { Link, useNavigate } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { clsx } from "clsx";
import { Check, Download, Inbox, Plus, Search, X } from "lucide-react";
import { api } from "../../lib/api";
import { formatCm, formatDate } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import StatusPill from "../../components/ui/StatusPill";
import Skeleton from "../../components/ui/Skeleton";
import EmptyState from "../../components/ui/EmptyState";
import Button from "../../components/ui/Button";
import { useAuth } from "../../lib/auth";
import { can } from "../../lib/permissions";

interface Order {
  id: string;
  code: string;
  buyer_name: string;
  fabric_type_id?: string;
  fabric_type_name?: string;
  quantity_cm: number;
  status: string;
  priority?: string;
  due_date: string;
  created_at: string;
}

interface OrdersResponse {
  items: Order[];
  total: number;
}

interface HealthResponse {
  health: "green" | "amber" | "red";
  slack_minutes: number;
  predicted_dispatch_at: string;
}

const STATUS_FILTERS = [
  { value: "", label: "All" },
  { value: "draft", label: "Draft" },
  { value: "pending_approval", label: "Awaiting approval" },
  { value: "confirmed", label: "Confirmed" },
  { value: "in_production", label: "In production" },
  { value: "qc", label: "QC" },
  { value: "ready", label: "Ready" },
  { value: "dispatched", label: "Dispatched" },
];

const HEALTH: Record<string, { dot: string; label: string }> = {
  green: { dot: "bg-emerald-500", label: "On track" },
  amber: { dot: "bg-amber-500", label: "At risk" },
  red: { dot: "bg-red-500", label: "Late" },
};

function HealthIndicator({ orderId }: { orderId: string }) {
  const { data, isLoading } = useQuery<HealthResponse>({
    queryKey: ["order-health", orderId],
    queryFn: () => api.get(`/ripple/orders/${orderId}/health`),
  });

  if (isLoading) return <span className="inline-block h-2 w-14 animate-pulse rounded-full bg-gray-100" />;
  const h = data ? HEALTH[data.health] : undefined;
  if (!h) return <span className="text-xs text-gray-400">—</span>;
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-gray-700" title={`${data!.slack_minutes} min slack`}>
      <span className={clsx("h-2 w-2 rounded-full", h.dot)} />
      {h.label}
    </span>
  );
}

function formatStatus(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function exportOrdersCSV(orders: Order[], fabricName: (o: Order) => string) {
  const header = ["Code", "Buyer", "Fabric Type", "Quantity (m)", "Due Date", "Status", "Created At"];
  const rows = orders.map((o) => [
    o.code,
    o.buyer_name,
    fabricName(o),
    (o.quantity_cm / 100).toFixed(2),
    o.due_date,
    formatStatus(o.status),
    o.created_at?.slice(0, 10) ?? "",
  ]);
  const csv = [header, ...rows].map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `orders_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function OrdersPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (user?.role === "buyer") {
      navigate("/app/buyer-portal", { replace: true });
    }
  }, [user, navigate]);

  const canManage = can(user?.role, "orders:write");
  const isAccounts = user?.role === "accounts";

  const { data, isLoading, isError } = useQuery<OrdersResponse>({
    queryKey: ["orders"],
    queryFn: () => api.get("/orders?page=1&size=50"),
  });

  const { data: fabrics } = useQuery({
    queryKey: ["fabric-types"],
    queryFn: () => api.get<{ items: { id: string; name: string }[] }>("/fabric-types"),
    retry: false,
  });

  const fabricName = useMemo(() => {
    const byId = new Map((fabrics?.items ?? []).map((f) => [f.id, f.name]));
    return (o: Order) => o.fabric_type_name ?? (o.fabric_type_id ? byId.get(o.fabric_type_id) : undefined) ?? "—";
  }, [fabrics]);

  const items = useMemo(() => data?.items ?? [], [data]);
  const pendingOrders = items.filter((o) => o.status === "pending_approval");
  const counts = useMemo(() => {
    const c: Record<string, number> = { "": items.length };
    for (const o of items) c[o.status] = (c[o.status] ?? 0) + 1;
    return c;
  }, [items]);

  const q = search.trim().toLowerCase();
  const visible = items.filter(
    (o) =>
      (!statusFilter || o.status === statusFilter) &&
      (!q || o.code.toLowerCase().includes(q) || o.buyer_name?.toLowerCase().includes(q)),
  );

  const approveMutation = useMutation({
    mutationFn: (id: string) => api.post(`/orders/${id}/approve`, {}),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["orders"] }),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) => api.post(`/orders/${id}/reject`, { reason: "Rejected by owner" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["orders"] }),
  });

  const actionButton = canManage ? (
    <Link to="/app/orders/new" className="btn-primary">
      <Plus className="h-4 w-4" /> New order
    </Link>
  ) : isAccounts ? (
    <Button variant="secondary" onClick={() => exportOrdersCSV(items, fabricName)} disabled={!items.length}>
      <Download className="h-4 w-4" /> Export CSV
    </Button>
  ) : null;

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader
        title="Orders"
        subtitle={data ? `${data.total} orders · ${counts.in_production ?? 0} in production` : undefined}
        actions={actionButton}
      />

      {canManage && pendingOrders.length > 0 && (
        <div className="card overflow-hidden border-amber-300/60">
          <div className="flex items-center gap-2 border-b border-amber-200/70 bg-amber-50 px-5 py-3">
            <Inbox className="h-4 w-4 text-amber-600" />
            <h2 className="text-sm font-semibold text-amber-900">
              Buyer requests · {pendingOrders.length} awaiting approval
            </h2>
          </div>
          <ul className="divide-y divide-gray-100">
            {pendingOrders.map((order) => (
              <li key={order.id} className="flex flex-col gap-3 px-5 py-3.5 sm:flex-row sm:items-center">
                <div className="min-w-0 flex-1">
                  <Link to={`/app/orders/${order.id}`} className="font-mono text-sm font-semibold text-gray-900 hover:text-brand-600">
                    {order.code}
                  </Link>
                  <p className="text-xs text-gray-500">
                    {order.buyer_name} · {fabricName(order)} · {formatCm(order.quantity_cm)} · Due {formatDate(order.due_date)}
                  </p>
                </div>
                <div className="flex shrink-0 gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => rejectMutation.mutate(order.id)}
                    disabled={approveMutation.isPending || rejectMutation.isPending}
                  >
                    <X className="h-3.5 w-3.5" /> Reject
                  </Button>
                  <Button
                    size="sm"
                    variant="success"
                    onClick={() => approveMutation.mutate(order.id)}
                    disabled={approveMutation.isPending || rejectMutation.isPending}
                  >
                    <Check className="h-3.5 w-3.5" /> Approve
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {isError && (
        <div className="rounded-xl bg-red-50 p-4 text-sm text-red-700 ring-1 ring-inset ring-red-600/15">Failed to load orders.</div>
      )}

      <div className="card overflow-hidden">
        <div className="flex flex-col gap-3 border-b border-gray-100 p-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap gap-1">
            {STATUS_FILTERS.filter((f) => !f.value || counts[f.value]).map((f) => (
              <button
                key={f.value}
                onClick={() => setStatusFilter(f.value)}
                className={clsx(
                  "inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-colors",
                  statusFilter === f.value ? "bg-brand-600 text-white shadow-sm" : "text-gray-600 hover:bg-gray-100",
                )}
              >
                {f.label}
                <span
                  className={clsx(
                    "tabular rounded-md px-1.5 text-[11px]",
                    statusFilter === f.value ? "bg-white/20 text-white" : "bg-gray-100 text-gray-500",
                  )}
                >
                  {counts[f.value] ?? 0}
                </span>
              </button>
            ))}
          </div>
          <label className="flex h-9 items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 text-sm transition focus-within:border-brand-500 focus-within:ring-4 focus-within:ring-brand-500/10 lg:w-72">
            <Search className="h-4 w-4 text-gray-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search code or buyer"
              aria-label="Search orders"
              className="min-w-0 flex-1 bg-transparent text-gray-900 outline-none placeholder:text-gray-400"
            />
          </label>
        </div>

        {isLoading ? (
          <div className="p-5"><Skeleton rows={8} /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50/80">
                  <th className="table-header-cell">Order</th>
                  <th className="table-header-cell">Buyer</th>
                  <th className="table-header-cell">Fabric</th>
                  <th className="table-header-cell text-right">Quantity</th>
                  <th className="table-header-cell">Due</th>
                  <th className="table-header-cell">Status</th>
                  <th className="table-header-cell">Health</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {visible.map((order) => (
                  <tr
                    key={order.id}
                    onClick={() => navigate(`/app/orders/${order.id}`)}
                    className="cursor-pointer transition-colors hover:bg-gray-50"
                  >
                    <td className="px-4 py-3">
                      <Link
                        to={`/app/orders/${order.id}`}
                        onClick={(e) => e.stopPropagation()}
                        className="font-mono text-sm font-semibold text-gray-900 hover:text-brand-600"
                      >
                        {order.code}
                      </Link>
                      {order.priority === "high" && (
                        <span className="ml-2 rounded bg-red-50 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-red-700">High</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">{order.buyer_name}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{fabricName(order)}</td>
                    <td className="px-4 py-3 text-right text-sm font-medium text-gray-900">{formatCm(order.quantity_cm)}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">{formatDate(order.due_date)}</td>
                    <td className="px-4 py-3"><StatusPill status={order.status} size="sm" /></td>
                    <td className="px-4 py-3"><HealthIndicator orderId={order.id} /></td>
                  </tr>
                ))}
                {visible.length === 0 && (
                  <tr>
                    <td colSpan={7}>
                      <EmptyState
                        title={items.length ? "No orders match these filters" : "No orders yet"}
                        description={items.length ? "Try a different status or search term." : undefined}
                      />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
