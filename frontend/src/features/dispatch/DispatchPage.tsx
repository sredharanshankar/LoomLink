import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import { qk } from "../../lib/query-keys";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import StatusPill from "../../components/ui/StatusPill";

interface Dispatch {
  id: string;
  code: string;
  buyer_name: string;
  status: string;
  rolls_count: number;
  created_at: string;
}

interface FinishedStock {
  order_code: string;
  roll_code: string;
  length_cm: number;
  status: string;
  location: string;
}

export default function DispatchPage() {
  const { data: dispatches, isLoading: loadingDispatches } = useQuery({
    queryKey: qk.dispatch.dispatches(),
    queryFn: () => api.get<{ items: Dispatch[]; total: number }>("/dispatches?page=1&size=50"),
  });

  const { data: stock, isLoading: loadingStock } = useQuery({
    queryKey: ["dispatch-finished-stock"],
    queryFn: () => api.get<{ items: FinishedStock[] }>("/dispatch/finished-stock"),
  });

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="Dispatch" subtitle={`${dispatches?.total ?? 0} dispatches`} />

      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Finished Stock Ready</h2>
        {loadingStock ? (
          <Skeleton rows={4} />
        ) : (
          <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Order</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Roll</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Length (cm)</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Location</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {stock?.items.map((s) => (
                  <tr key={s.roll_code}>
                    <td className="px-4 py-3 text-gray-900">{s.order_code}</td>
                    <td className="px-4 py-3 font-mono text-gray-700">{s.roll_code}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{s.length_cm.toLocaleString("en-IN")}</td>
                    <td className="px-4 py-3"><StatusPill status={s.status} size="sm" /></td>
                    <td className="px-4 py-3 text-gray-700">{s.location}</td>
                  </tr>
                ))}
                {stock?.items.length === 0 && (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No finished stock</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Dispatches</h2>
        {loadingDispatches ? (
          <Skeleton rows={6} />
        ) : (
          <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Code</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Buyer</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Rolls</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {dispatches?.items.map((d) => (
                  <tr key={d.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link to={`/app/dispatch/${d.id}`} className="text-blue-600 hover:underline font-medium">
                        {d.code}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-900">{d.buyer_name}</td>
                    <td className="px-4 py-3"><StatusPill status={d.status} size="sm" /></td>
                    <td className="px-4 py-3 text-right tabular-nums">{d.rolls_count}</td>
                    <td className="px-4 py-3 text-gray-500">{formatDateTime(d.created_at)}</td>
                  </tr>
                ))}
                {dispatches?.items.length === 0 && (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No dispatches</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
