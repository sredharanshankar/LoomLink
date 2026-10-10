import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { formatGrams } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import KpiTile from "../../components/ui/KpiTile";
import Skeleton from "../../components/ui/Skeleton";
import Badge from "../../components/ui/Badge";

interface StockItem {
  yarn_type_id: string;
  code: string;
  material: string;
  count_label: string;
  colour: string;
  colour_hex: string;
  reorder_level_g: number;
  on_hand_g: number;
  reserved_g: number;
  available_g: number;
  is_low: boolean;
  batches_count: number;
}

interface StockResponse {
  items: StockItem[];
}

interface AlertsResponse {
  low_stock: StockItem[];
}

export default function InventoryPage() {
  const { data: stock, isLoading: stockLoading } = useQuery({
    queryKey: ["inventory-stock"],
    queryFn: () => api.get<StockResponse>("/inventory/stock"),
  });

  const { data: alerts, isLoading: alertsLoading } = useQuery({
    queryKey: ["inventory-alerts"],
    queryFn: () => api.get<AlertsResponse>("/inventory/alerts"),
  });

  const isLoading = stockLoading || alertsLoading;

  const totalTypes = stock?.items.length ?? 0;
  const lowStockCount = alerts?.low_stock?.length ?? 0;
  const totalWeightG = stock?.items.reduce((sum, item) => sum + item.on_hand_g, 0) ?? 0;

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="Inventory"
        subtitle="Yarn stock overview"
        actions={
          <Link
            to="/app/inventory/receive"
            className="inline-flex items-center justify-center rounded-md font-medium h-10 px-4 text-sm bg-brand-700 text-white hover:bg-brand-800 transition-colors"
          >
            Receive Yarn
          </Link>
        }
      />

      {isLoading ? (
        <Skeleton rows={4} className="max-w-sm" />
      ) : (
        <>
          {/* KPI Summary */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <KpiTile label="Yarn Types" value={totalTypes} />
            <KpiTile
              label="Low Stock Alerts"
              value={lowStockCount}
              trend={lowStockCount > 0 ? "down" : "neutral"}
            />
            <KpiTile label="Total Stock" value={formatGrams(totalWeightG)} />
          </div>

          {/* Stock Table */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Code</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Colour</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Stock</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Reorder Level</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {stock?.items.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                        No yarn stock found.
                      </td>
                    </tr>
                  )}
                  {stock?.items.map((item) => (
                      <tr key={item.code} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-mono text-gray-900">{item.code}</td>
                        <td className="px-4 py-3 text-sm text-gray-900">{item.material} {item.count_label}</td>
                        <td className="px-4 py-3 text-sm text-gray-700">
                          <span className="inline-flex items-center gap-2">
                            <span
                              className="inline-block w-3 h-3 rounded-full border border-gray-300"
                              style={{ backgroundColor: item.colour_hex }}
                            />
                            {item.colour}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                          {formatGrams(item.on_hand_g)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500 text-right">
                          {formatGrams(item.reorder_level_g)}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <Badge color={item.is_low ? "red" : "green"}>
                            {item.is_low ? "Low" : "OK"}
                          </Badge>
                        </td>
                      </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
