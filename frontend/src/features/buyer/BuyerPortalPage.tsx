import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { formatCm, formatDate } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";
import KpiTile from "../../components/ui/KpiTile";

interface BuyerProfile {
  id: string;
  code: string;
  name: string;
  contact_person: string;
  phone: string;
  email: string;
  address: string;
  payment_terms_days: number;
}

interface Order {
  id: string;
  code: string;
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

const STATUS_COLORS: Record<string, "blue" | "yellow" | "purple" | "green" | "gray" | "red"> = {
  pending_approval: "red",
  confirmed: "blue",
  in_production: "yellow",
  qc: "purple",
  ready: "green",
  dispatched: "gray",
};

function formatStatus(s: string) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function BuyerPortalPage() {
  const { data: profile, isLoading: loadingProfile, error: profileError } = useQuery<BuyerProfile>({
    queryKey: ["buyer-portal-me"],
    queryFn: () => api.get("/buyer/portal/me"),
    staleTime: 60_000,
    retry: false,
  });

  const noProfileLinked =
    profileError instanceof Error &&
    profileError.message.toLowerCase().includes("no buyer profile");

  const { data: orders, isLoading: loadingOrders } = useQuery<OrdersResponse>({
    queryKey: ["buyer-portal-orders"],
    queryFn: () => api.get("/buyer/portal/orders?page=1&size=50"),
    staleTime: 30_000,
    refetchInterval: 60_000,
    enabled: !noProfileLinked,
  });

  const items = orders?.items ?? [];

  const statusCounts = {
    active: items.filter((o) => !["dispatched"].includes(o.status)).length,
    in_production: items.filter((o) => o.status === "in_production").length,
    ready: items.filter((o) => o.status === "ready").length,
    dispatched: items.filter((o) => o.status === "dispatched").length,
  };

  const placeOrderButton = (
    <Link
      to="/app/buyer-portal/new"
      className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
    >
      Place New Order
    </Link>
  );

  if (noProfileLinked) {
    return (
      <div className="p-6 max-w-lg">
        <PageHeader title="My Portal" />
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800">
          <p className="font-semibold mb-1">Account not linked to a buyer profile</p>
          <p>
            Your login account hasn't been connected to a buyer entity yet.
            Please ask your LoomLink administrator to open{" "}
            <strong>Settings → Users</strong>, find your account, and click{" "}
            <strong>"Link Buyer"</strong>.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title={loadingProfile ? "My Portal" : (profile?.name ?? "My Portal")}
        subtitle={profile ? `${profile.code} · Payment terms: ${profile.payment_terms_days} days` : undefined}
        actions={placeOrderButton}
      />

      {loadingProfile || loadingOrders ? (
        <Skeleton rows={4} />
      ) : (
        <>
          {/* KPI row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <KpiTile label="Total Orders" value={items.length} />
            <KpiTile label="Active" value={statusCounts.active} trend="up" />
            <KpiTile label="Ready to Ship" value={statusCounts.ready} trend="up" />
            <KpiTile label="Dispatched" value={statusCounts.dispatched} />
          </div>

          {/* Orders table */}
          <section>
            <h2 className="text-base font-semibold text-gray-900 mb-3">Your Orders</h2>
            {items.length === 0 ? (
              <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
                <p className="text-gray-400 text-sm mb-4">No orders yet.</p>
                <Link
                  to="/app/buyer-portal/new"
                  className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Place Your First Order
                </Link>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fabric</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Quantity</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Due Date</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {items.map((order) => (
                      <tr key={order.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-medium text-blue-600">{order.code}</td>
                        <td className="px-4 py-3 text-sm text-gray-700">{order.fabric_type_name ?? "—"}</td>
                        <td className="px-4 py-3 text-sm text-gray-700 text-right tabular-nums">{formatCm(order.quantity_cm)}</td>
                        <td className="px-4 py-3 text-sm text-gray-700">{formatDate(order.due_date)}</td>
                        <td className="px-4 py-3 text-sm">
                          <Badge color={STATUS_COLORS[order.status] ?? "gray"}>
                            {formatStatus(order.status)}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Profile summary */}
          {profile && (
            <section>
              <h2 className="text-base font-semibold text-gray-900 mb-3">Account Details</h2>
              <div className="bg-white rounded-lg border border-gray-200 p-5 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                {profile.contact_person && (
                  <div><p className="text-gray-500 text-xs uppercase tracking-wide">Contact</p><p className="text-gray-900 mt-0.5">{profile.contact_person}</p></div>
                )}
                {profile.phone && (
                  <div><p className="text-gray-500 text-xs uppercase tracking-wide">Phone</p><p className="text-gray-900 mt-0.5">{profile.phone}</p></div>
                )}
                {profile.email && (
                  <div><p className="text-gray-500 text-xs uppercase tracking-wide">Email</p><p className="text-gray-900 mt-0.5">{profile.email}</p></div>
                )}
                {profile.address && (
                  <div className="sm:col-span-2"><p className="text-gray-500 text-xs uppercase tracking-wide">Address</p><p className="text-gray-900 mt-0.5">{profile.address}</p></div>
                )}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
