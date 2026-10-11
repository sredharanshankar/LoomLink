import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatPaise, formatDateTime } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";

interface PurchaseOrder {
  id: string;
  code: string;
  supplier_name: string;
  status: string;
  total_paise: number;
  created_at: string;
}

interface PurchaseOrdersResponse {
  items: PurchaseOrder[];
  total: number;
}

const STATUS_COLORS: Record<string, "blue" | "yellow" | "green" | "gray" | "red"> = {
  draft: "gray",
  sent: "blue",
  confirmed: "yellow",
  received: "green",
  cancelled: "red",
};

function formatStatus(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function PurchaseOrdersPage() {
  const { data, isLoading, isError } = useQuery<PurchaseOrdersResponse>({
    queryKey: ["purchase-orders"],
    queryFn: () => api.get("/purchase-orders?page=1&size=50"),
  });

  return (
    <div className="p-6">
      <PageHeader title="Purchase Orders" />

      {isLoading && <Skeleton rows={8} />}

      {isError && (
        <div className="bg-red-50 text-red-700 rounded-lg border border-red-200 p-4">
          Failed to load purchase orders.
        </div>
      )}

      {data && data.items.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-400">
          No purchase orders
        </div>
      )}

      {data && data.items.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Supplier</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.items.map((po) => (
                <tr key={po.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{po.code}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{po.supplier_name}</td>
                  <td className="px-4 py-3 text-sm">
                    <Badge color={STATUS_COLORS[po.status] ?? "gray"}>
                      {formatStatus(po.status)}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">{formatPaise(po.total_paise)}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{formatDateTime(po.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
