import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatCm, formatDate } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";
import { useAuth } from "../../lib/auth";
import { can } from "../../lib/permissions";

interface Order {
  id: string;
  code: string;
  buyer_name: string;
  fabric_type_name: string;
  quantity_cm: number;
  status: string;
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

const STATUS_COLORS: Record<string, "blue" | "yellow" | "purple" | "green" | "gray"> = {
  confirmed: "blue",
  in_production: "yellow",
  qc: "purple",
  ready: "green",
  dispatched: "gray",
};

const HEALTH_DOT: Record<string, string> = {
  green: "bg-green-500",
  amber: "bg-yellow-500",
  red: "bg-red-500",
};

function HealthDot({ orderId }: { orderId: string }) {
  const { data, isLoading } = useQuery<HealthResponse>({
    queryKey: ["order-health", orderId],
    queryFn: () => api.get(`/ripple/orders/${orderId}/health`),
  });

  if (isLoading) return <span className="inline-block w-3 h-3 rounded-full bg-gray-200 animate-pulse" />;
  if (!data) return <span className="inline-block w-3 h-3 rounded-full bg-gray-300" />;

  return (
    <span
      className={`inline-block w-3 h-3 rounded-full ${HEALTH_DOT[data.health] ?? "bg-gray-300"}`}
      title={`${data.health} — ${data.slack_minutes}min slack`}
    />
  );
}

function formatStatus(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function exportOrdersCSV(orders: Order[]) {
  const header = ["Code", "Buyer", "Fabric Type", "Quantity (m)", "Due Date", "Status", "Created At"];
  const rows = orders.map((o) => [
    o.code,
    o.buyer_name,
    o.fabric_type_name ?? "",
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
  const canManage = can(user?.role, "orders:write");
  const isAccounts = user?.role === "accounts";

  const { data, isLoading, isError } = useQuery<OrdersResponse>({
    queryKey: ["orders"],
    queryFn: () => api.get("/orders?page=1&size=50"),
  });

  const actionButton = canManage ? (
    <Link
      to="/app/orders/new"
      className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
    >
      New Order
    </Link>
  ) : isAccounts ? (
    <button
      onClick={() => data?.items && exportOrdersCSV(data.items)}
      disabled={!data?.items?.length}
      className="inline-flex items-center rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
    >
      Export Excel
    </button>
  ) : null;

  return (
    <div className="p-6">
      <PageHeader title="Orders" actions={actionButton} />

      {isLoading && <Skeleton rows={8} />}

      {isError && (
        <div className="bg-red-50 text-red-700 rounded-lg border border-red-200 p-4">
          Failed to load orders.
        </div>
      )}

      {data && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Buyer</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fabric</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Due Date</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Health</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.items.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm">
                    <Link to={`/app/orders/${order.id}`} className="text-blue-600 hover:underline font-medium">
                      {order.code}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">{order.buyer_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{order.fabric_type_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{formatCm(order.quantity_cm)}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{formatDate(order.due_date)}</td>
                  <td className="px-4 py-3 text-sm">
                    <Badge color={STATUS_COLORS[order.status] ?? "gray"}>
                      {formatStatus(order.status)}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <HealthDot orderId={order.id} />
                  </td>
                </tr>
              ))}
              {data.items.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                    No orders yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
