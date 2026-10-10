import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatPaise, formatCm, formatDateTime } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";

interface YarnBatch {
  code: string;
  supplier_name: string;
  material: string;
  rate_paise_per_kg: number;
}

interface HistoryEntry {
  event: string;
  timestamp: string;
  details: string;
}

interface CostBreakdown {
  yarn_paise: number;
  weaving_paise: number;
  dyeing_paise: number;
  finishing_paise: number;
  overhead_paise: number;
  total_paise: number;
}

interface RollDetail {
  id: string;
  code: string;
  order_code: string;
  buyer_name: string;
  fabric_type_name: string;
  length_cm: number;
  status: string;
  grade: string;
  yarn_batch: YarnBatch;
  history: HistoryEntry[];
  cost_breakdown: CostBreakdown;
  selling_price_paise?: number;
}

const GRADE_COLOR: Record<string, "green" | "yellow" | "red" | "gray"> = {
  A: "green",
  B: "yellow",
  C: "red",
};

const STATUS_COLOR: Record<string, "green" | "blue" | "yellow" | "gray" | "red" | "purple"> = {
  finished: "green",
  dispatched: "blue",
  in_progress: "yellow",
  rejected: "red",
};

export default function RollPassportPage() {
  const [code, setCode] = useState("");
  const [searchCode, setSearchCode] = useState("");

  const { data, isLoading, error, isFetched } = useQuery<RollDetail>({
    queryKey: ["rolls", "lookup", searchCode],
    queryFn: () => api.get(`/rolls/lookup?code=${encodeURIComponent(searchCode)}`),
    enabled: searchCode.length > 0,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchCode(code.trim());
  };

  const roll = data;
  const cost = roll?.cost_breakdown;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <PageHeader title="Roll Passport" subtitle="Trace a roll's complete life history" />

      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-3">
          <input
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Enter roll code (e.g. ROLL-104-07)"
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={!code.trim()}
            className="px-6 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Search
          </button>
        </div>
      </form>

      {isLoading && <Skeleton rows={6} />}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center text-red-700 text-sm">
          Roll not found. Check the code and try again.
        </div>
      )}

      {!isLoading && !error && isFetched && !roll && searchCode && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center text-gray-500">
          No roll found for code "{searchCode}".
        </div>
      )}

      {!searchCode && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center text-gray-400">
          Enter a roll code above to view its passport.
        </div>
      )}

      {roll && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">{roll.code}</h2>
              <div className="flex gap-2">
                <Badge color={STATUS_COLOR[roll.status] ?? "gray"}>{roll.status}</Badge>
                <Badge color={GRADE_COLOR[roll.grade] ?? "gray"}>Grade {roll.grade}</Badge>
              </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Order</p>
                <p className="font-medium text-gray-900">{roll.order_code}</p>
              </div>
              <div>
                <p className="text-gray-500">Buyer</p>
                <p className="font-medium text-gray-900">{roll.buyer_name}</p>
              </div>
              <div>
                <p className="text-gray-500">Fabric</p>
                <p className="font-medium text-gray-900">{roll.fabric_type_name}</p>
              </div>
              <div>
                <p className="text-gray-500">Length</p>
                <p className="font-medium text-gray-900">{formatCm(roll.length_cm)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">Yarn Batch</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Code</p>
                <p className="font-medium text-gray-900">{roll.yarn_batch.code}</p>
              </div>
              <div>
                <p className="text-gray-500">Supplier</p>
                <p className="font-medium text-gray-900">{roll.yarn_batch.supplier_name}</p>
              </div>
              <div>
                <p className="text-gray-500">Material</p>
                <p className="font-medium text-gray-900">{roll.yarn_batch.material}</p>
              </div>
              <div>
                <p className="text-gray-500">Rate</p>
                <p className="font-medium text-gray-900">{formatPaise(roll.yarn_batch.rate_paise_per_kg, { showPaise: true })}/kg</p>
              </div>
            </div>
          </div>

          {roll.history.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4">Journey Timeline</h3>
              <div className="relative">
                <div className="absolute left-3 top-2 bottom-2 w-px bg-gray-200" />
                <div className="space-y-4">
                  {roll.history.map((entry, i) => (
                    <div key={i} className="relative pl-8">
                      <div className="absolute left-1.5 top-1.5 w-3 h-3 rounded-full bg-indigo-500 border-2 border-white ring-2 ring-indigo-200" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{entry.event}</p>
                        <p className="text-xs text-gray-500">{formatDateTime(entry.timestamp)}</p>
                        {entry.details && (
                          <p className="text-xs text-gray-600 mt-0.5">{entry.details}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {cost && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">Cost Breakdown</h3>
              <div className="space-y-2 text-sm">
                {[
                  { label: "Yarn", value: cost.yarn_paise },
                  { label: "Weaving", value: cost.weaving_paise },
                  { label: "Dyeing", value: cost.dyeing_paise },
                  { label: "Finishing", value: cost.finishing_paise },
                  { label: "Overhead", value: cost.overhead_paise },
                ].map((row) => (
                  <div key={row.label} className="flex justify-between py-1">
                    <span className="text-gray-600">{row.label}</span>
                    <span className="font-medium text-gray-900">{formatPaise(row.value, { showPaise: true })}</span>
                  </div>
                ))}
                <div className="border-t border-gray-200 pt-2 flex justify-between font-bold">
                  <span className="text-gray-900">Total Cost</span>
                  <span className="text-gray-900">{formatPaise(cost.total_paise, { showPaise: true })}</span>
                </div>
                {roll.selling_price_paise != null && (
                  <div className="flex justify-between pt-1">
                    <span className="text-gray-600">Margin</span>
                    <span className={roll.selling_price_paise - cost.total_paise >= 0 ? "text-green-700 font-medium" : "text-red-700 font-medium"}>
                      {formatPaise(roll.selling_price_paise - cost.total_paise, { showPaise: true })}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
