import { useQuery } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import { formatGrams } from "../../../lib/format";
import PageHeader from "../../../components/ui/PageHeader";
import Skeleton from "../../../components/ui/Skeleton";
import Badge from "../../../components/ui/Badge";

interface StockAlert {
  yarn_type_id: string;
  code: string;
  colour: string;
  colour_hex: string;
  on_hand_g: number;
  reorder_level_g: number;
  is_low: boolean;
}

interface RippleEvent {
  id: string;
  code: string;
  title: string;
  event_type: string;
  severity: string;
  status: string;
  at_risk_paise: number;
}

export default function WorkerAlertsPage() {
  const { data: stockAlerts, isLoading: stockLoading } = useQuery({
    queryKey: ["worker-stock-alerts"],
    queryFn: () => api.get<{ items: StockAlert[] }>("/inventory/stock"),
  });

  const { data: ripple, isLoading: rippleLoading } = useQuery({
    queryKey: ["worker-ripple-alerts"],
    queryFn: () => api.get<{ items: RippleEvent[] }>("/ripple/events"),
  });

  const isLoading = stockLoading || rippleLoading;
  const lowStock = stockAlerts?.items.filter((s) => s.is_low) ?? [];
  const activeEvents = ripple?.items.filter((e) => e.status === "open") ?? [];
  const totalAlerts = lowStock.length + activeEvents.length;

  return (
    <div className="p-4 space-y-4">
      <PageHeader
        title="Alerts"
        subtitle={totalAlerts > 0 ? `${totalAlerts} active alert${totalAlerts > 1 ? "s" : ""}` : "All clear"}
      />

      {isLoading ? (
        <Skeleton rows={4} />
      ) : totalAlerts === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <p className="text-3xl mb-2">✅</p>
          <p className="text-gray-500 text-sm">No active alerts — everything is running smoothly.</p>
        </div>
      ) : (
        <>
          {/* Ripple events */}
          {activeEvents.length > 0 && (
            <section>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Ripple Events
              </h3>
              <div className="space-y-2">
                {activeEvents.map((evt) => (
                  <div
                    key={evt.id}
                    className="bg-white rounded-lg border border-red-200 p-3"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900">{evt.code}</span>
                      <Badge color="red">{evt.event_type}</Badge>
                    </div>
                    <p className="text-xs text-gray-600">{evt.title}</p>
                    <p className="text-xs text-red-600 mt-1">
                      ₹{(evt.at_risk_paise / 100).toLocaleString("en-IN")} at risk
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Low stock alerts */}
          {lowStock.length > 0 && (
            <section>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 mt-4">
                Low Stock ({lowStock.length})
              </h3>
              <div className="space-y-2">
                {lowStock.map((item) => (
                  <div
                    key={item.yarn_type_id}
                    className="bg-white rounded-lg border border-yellow-200 p-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className="inline-block w-3 h-3 rounded-full border border-gray-300"
                          style={{ backgroundColor: item.colour_hex }}
                        />
                        <span className="text-sm font-medium text-gray-900">{item.code}</span>
                      </div>
                      <Badge color="yellow">Low Stock</Badge>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatGrams(item.on_hand_g)} on hand — reorder at {formatGrams(item.reorder_level_g)}
                    </p>
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
