import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatCm, formatDate } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";

interface Buyer {
  id: string;
  code: string;
  name: string;
  contact_name: string;
  phone: string;
  email: string;
  gst_number: string;
  address: string;
}

interface Order {
  id: string;
  code: string;
  fabric_type_name: string;
  quantity_cm: number;
  status: string;
  due_date: string;
}

interface OrdersResponse {
  items: Order[];
  total: number;
}

const STATUS_COLORS: Record<string, "blue" | "yellow" | "purple" | "green" | "gray"> = {
  confirmed: "blue",
  in_production: "yellow",
  qc: "purple",
  ready: "green",
  dispatched: "gray",
};

function formatStatus(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function BuyerDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: buyer, isLoading, isError } = useQuery<Buyer>({
    queryKey: ["buyer", id],
    queryFn: () => api.get(`/buyers/${id}`),
    enabled: !!id,
  });

  const { data: orders } = useQuery<OrdersResponse>({
    queryKey: ["buyer-orders", id],
    queryFn: () => api.get(`/orders?buyer_id=${id}&page=1&size=50`),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-6"><Skeleton rows={6} /></div>;

  if (isError || !buyer) {
    return (
      <div className="p-6">
        <div className="bg-red-50 text-red-700 rounded-lg border border-red-200 p-4">
          Failed to load buyer details.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <PageHeader title={buyer.name} subtitle={buyer.code} />

      <div className="bg-white rounded-lg border border-gray-200 p-5 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Buyer Information</h2>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
          <div>
            <dt className="text-sm text-gray-500">Contact</dt>
            <dd className="text-sm font-medium text-gray-900">{buyer.contact_name}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Phone</dt>
            <dd className="text-sm font-medium text-gray-900">{buyer.phone}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Email</dt>
            <dd className="text-sm font-medium text-gray-900">{buyer.email}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">GST Number</dt>
            <dd className="text-sm font-medium text-gray-900">{buyer.gst_number}</dd>
          </div>
          <div className="md:col-span-2">
            <dt className="text-sm text-gray-500">Address</dt>
            <dd className="text-sm font-medium text-gray-900">{buyer.address}</dd>
          </div>
        </dl>
      </div>

      {orders && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Orders</h2>
          {orders.items.length === 0 ? (
            <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-400">
              No orders for this buyer.
            </div>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fabric</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Due Date</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {orders.items.map((order) => (
                    <tr key={order.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">
                        <Link to={`/app/orders/${order.id}`} className="text-brand-600 hover:underline font-medium">
                          {order.code}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">{order.fabric_type_name}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{formatCm(order.quantity_cm)}</td>
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
        </div>
      )}
    </div>
  );
}
