import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatPaise } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import KpiTile from "../../components/ui/KpiTile";
import Skeleton from "../../components/ui/Skeleton";

interface MonthClose {
  revenue_paise: number;
  material_cost_paise: number;
  wages_paise: number;
  expenses_paise: number;
  profit_paise: number;
}

function buildMonthOptions(): string[] {
  const months: string[] = [];
  const now = new Date();
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    months.push(d.toISOString().slice(0, 7));
  }
  return months;
}

export default function MonthClosePage() {
  const monthOptions = buildMonthOptions();
  const [period, setPeriod] = useState(monthOptions[0]);

  const { data, isLoading } = useQuery({
    queryKey: ["finance-month-close", period],
    queryFn: () => api.get<MonthClose>(`/finance/month-close?period=${period}`),
  });

  const totalCost = data
    ? data.material_cost_paise + data.wages_paise + data.expenses_paise
    : 0;

  const categories = data
    ? [
        { label: "Material Cost", paise: data.material_cost_paise },
        { label: "Wages", paise: data.wages_paise },
        { label: "Expenses", paise: data.expenses_paise },
      ]
    : [];

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="Month Close"
        actions={
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          >
            {monthOptions.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        }
      />

      {isLoading ? (
        <Skeleton rows={4} className="max-w-sm" />
      ) : data ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiTile label="Revenue" value={formatPaise(data.revenue_paise)} />
            <KpiTile label="Total Costs" value={formatPaise(totalCost)} />
            <KpiTile label="Profit" value={formatPaise(data.profit_paise)} />
            <KpiTile
              label="Margin"
              value={data.revenue_paise > 0
                ? `${((data.profit_paise / data.revenue_paise) * 100).toFixed(1)}%`
                : "-"}
            />
          </div>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Cost Breakdown</h2>
            <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
              {categories.map((c) => {
                const pct = totalCost > 0 ? (c.paise / totalCost) * 100 : 0;
                return (
                  <div key={c.label}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-700">{c.label}</span>
                      <span className="tabular-nums text-gray-900">{formatPaise(c.paise)}</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-400">
          No data for {period}
        </div>
      )}
    </div>
  );
}
