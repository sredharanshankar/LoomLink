import { useState } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from "recharts";
import { api } from "../../lib/api";
import { formatPaise } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import KpiTile from "../../components/ui/KpiTile";
import Skeleton from "../../components/ui/Skeleton";

interface MonthClose {
  period: string;
  revenue_subtotal_paise: number;
  revenue_gst_paise: number;
  revenue_total_paise: number;
  payments_received_paise: number;
  yarn_cost_paise: number;
  expenses_paise: number;
  payroll_paise: number;
  total_cost_paise: number;
  gross_profit_paise: number;
}

interface ByBuyer {
  buyer_id: string;
  buyer_name: string;
  invoice_count: number;
  outstanding_paise: number;
  overdue_paise: number;
}

interface Receivables {
  total_outstanding_paise: number;
  total_overdue_paise: number;
  by_buyer: ByBuyer[];
}

interface BySupplier {
  supplier_id: string;
  supplier_name: string;
  bill_count: number;
  outstanding_paise: number;
  overdue_paise: number;
}

interface Payables {
  total_outstanding_paise: number;
  total_overdue_paise: number;
  by_supplier: BySupplier[];
}

const SUB_PAGES = [
  { label: "Invoices", path: "/app/finance/invoices" },
  { label: "Supplier Bills", path: "/app/finance/supplier-bills" },
  { label: "Expenses", path: "/app/finance/expenses" },
  { label: "Payments", path: "/app/finance/payments" },
  { label: "Month Close", path: "/app/finance/month-close" },
  { label: "Payroll", path: "/app/workers/payroll" },
];

const CHART_COLORS = {
  revenue: "#3b82f6",
  cost: "#ef4444",
  profit: "#10b981",
  yarn: "#f59e0b",
  payroll: "#8b5cf6",
  expenses: "#6b7280",
};

const PIE_COLORS = [CHART_COLORS.yarn, CHART_COLORS.payroll, CHART_COLORS.expenses];

function getMonths(count: number): string[] {
  const months: string[] = [];
  const now = new Date();
  for (let i = count - 1; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    months.push(d.toISOString().slice(0, 7));
  }
  return months;
}

function shortMonth(period: string): string {
  const [year, month] = period.split("-");
  const d = new Date(Number(year), Number(month) - 1, 1);
  return d.toLocaleDateString("en-IN", { month: "short", year: "2-digit" });
}

function toL(paise: number): number {
  return Math.round(paise / 100_000) / 10;
}

function exportFinanceCSV(months: MonthClose[], receivables: Receivables | undefined, payables: Payables | undefined) {
  const lines: string[] = [];
  lines.push(["Month Close Summary"].join(""));
  lines.push(["Period", "Revenue (₹)", "Total Cost (₹)", "Gross Profit (₹)", "Yarn Cost (₹)", "Payroll (₹)", "Expenses (₹)"].map(h => `"${h}"`).join(","));
  for (const m of months) {
    lines.push([
      m.period,
      (m.revenue_subtotal_paise / 100).toFixed(2),
      (m.total_cost_paise / 100).toFixed(2),
      (m.gross_profit_paise / 100).toFixed(2),
      (m.yarn_cost_paise / 100).toFixed(2),
      (m.payroll_paise / 100).toFixed(2),
      (m.expenses_paise / 100).toFixed(2),
    ].map(v => `"${v}"`).join(","));
  }
  lines.push("");
  lines.push(["Receivables by Buyer"].join(""));
  lines.push(["Buyer", "Invoice Count", "Outstanding (₹)", "Overdue (₹)"].map(h => `"${h}"`).join(","));
  for (const b of receivables?.by_buyer ?? []) {
    lines.push([
      b.buyer_name,
      b.invoice_count,
      (b.outstanding_paise / 100).toFixed(2),
      (b.overdue_paise / 100).toFixed(2),
    ].map(v => `"${v}"`).join(","));
  }
  lines.push("");
  lines.push(["Payables by Supplier"].join(""));
  lines.push(["Supplier", "Bill Count", "Outstanding (₹)", "Overdue (₹)"].map(h => `"${h}"`).join(","));
  for (const s of payables?.by_supplier ?? []) {
    lines.push([
      s.supplier_name,
      s.bill_count,
      (s.outstanding_paise / 100).toFixed(2),
      (s.overdue_paise / 100).toFixed(2),
    ].map(v => `"${v}"`).join(","));
  }
  const csv = lines.join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `finance_report_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function FinancePage() {
  const [numMonths, setNumMonths] = useState<1 | 3 | 6>(3);
  const months = getMonths(numMonths);
  const currentPeriod = months[months.length - 1];

  const monthQueries = useQueries({
    queries: months.map((period) => ({
      queryKey: ["finance-month-close", period],
      queryFn: () => api.get<MonthClose>(`/finance/month-close?period=${period}`),
      staleTime: 30_000,
      refetchInterval: 60_000,
    })),
  });

  const { data: receivables, isLoading: loadingRec } = useQuery<Receivables>({
    queryKey: ["finance-receivables"],
    queryFn: () => api.get("/finance/receivables"),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  const { data: payables, isLoading: loadingPay } = useQuery<Payables>({
    queryKey: ["finance-payables"],
    queryFn: () => api.get("/finance/payables"),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  const allLoaded = monthQueries.every((q) => !q.isLoading);
  const monthData = monthQueries.map((q) => q.data).filter(Boolean) as MonthClose[];
  const currentMc = monthData.find((m) => m.period === currentPeriod);

  const barData = monthData.map((m) => ({
    month: shortMonth(m.period),
    Revenue: toL(m.revenue_subtotal_paise),
    Cost: toL(m.total_cost_paise),
    Profit: toL(m.gross_profit_paise),
  }));

  const pieData = currentMc
    ? [
        { name: "Yarn / Material", value: Math.max(0, currentMc.yarn_cost_paise) },
        { name: "Payroll", value: Math.max(0, currentMc.payroll_paise) },
        { name: "Expenses", value: Math.max(0, currentMc.expenses_paise) },
      ].filter((d) => d.value > 0)
    : [];

  const isLoading = !allLoaded || loadingRec || loadingPay;

  const profitMargin =
    currentMc && currentMc.revenue_subtotal_paise > 0
      ? ((currentMc.gross_profit_paise / currentMc.revenue_subtotal_paise) * 100).toFixed(1)
      : null;

  const exportButton = (
    <button
      onClick={() => exportFinanceCSV(monthData, receivables, payables)}
      disabled={monthData.length === 0}
      className="inline-flex items-center rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-40 transition-colors"
    >
      Export CSV
    </button>
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <PageHeader title="Finance Dashboard" />
        <div className="flex items-center gap-3">
          <div className="flex rounded-md border border-gray-200 overflow-hidden text-sm">
            {([1, 3, 6] as const).map((n) => (
              <button
                key={n}
                onClick={() => setNumMonths(n)}
                className={`px-3 py-1.5 ${numMonths === n ? "bg-blue-600 text-white" : "bg-white text-gray-700 hover:bg-gray-50"}`}
              >
                {n === 1 ? "This Month" : `${n}M`}
              </button>
            ))}
          </div>
          {exportButton}
        </div>
      </div>

      {isLoading ? (
        <Skeleton rows={4} />
      ) : (
        <>
          {/* KPI Row */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <KpiTile
              label="Revenue MTD"
              value={currentMc ? formatPaise(currentMc.revenue_subtotal_paise) : "—"}
              sub={currentMc && currentMc.revenue_gst_paise ? `+GST ${formatPaise(currentMc.revenue_gst_paise)}` : undefined}
            />
            <KpiTile
              label="Total Costs"
              value={currentMc ? formatPaise(currentMc.total_cost_paise) : "—"}
              trend="down"
            />
            <KpiTile
              label="Gross Profit"
              value={currentMc ? formatPaise(currentMc.gross_profit_paise) : "—"}
              sub={profitMargin ? `${profitMargin}% margin` : undefined}
              trend={currentMc && currentMc.gross_profit_paise > 0 ? "up" : "down"}
            />
            <KpiTile
              label="Receivables"
              value={receivables ? formatPaise(receivables.total_outstanding_paise) : "—"}
              sub={receivables && receivables.total_overdue_paise > 0 ? `Overdue: ${formatPaise(receivables.total_overdue_paise)}` : "No overdue"}
              trend={receivables && receivables.total_overdue_paise > 0 ? "down" : "neutral"}
            />
            <KpiTile
              label="Payables"
              value={payables ? formatPaise(payables.total_outstanding_paise) : "—"}
              sub={payables && payables.total_overdue_paise > 0 ? `Overdue: ${formatPaise(payables.total_overdue_paise)}` : "No overdue"}
              trend={payables && payables.total_overdue_paise > 0 ? "down" : "neutral"}
            />
            <KpiTile
              label="Payments Received"
              value={currentMc ? formatPaise(currentMc.payments_received_paise) : "—"}
              trend="up"
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Revenue vs Cost bar chart */}
            <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Revenue vs Costs vs Profit (₹ Lakhs)</h2>
              {barData.length === 0 ? (
                <div className="h-48 flex items-center justify-center text-gray-400 text-sm">No data</div>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={barData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}L`} />
                    <Tooltip formatter={(v: number) => [`${v}L`, undefined]} />
                    <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="Revenue" fill={CHART_COLORS.revenue} radius={[3, 3, 0, 0]} />
                    <Bar dataKey="Cost" fill={CHART_COLORS.cost} radius={[3, 3, 0, 0]} />
                    <Bar dataKey="Profit" fill={CHART_COLORS.profit} radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Cost breakdown donut */}
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Cost Breakdown (Current Month)</h2>
              {pieData.length === 0 ? (
                <div className="h-48 flex items-center justify-center text-gray-400 text-sm">No cost data</div>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={85}
                      dataKey="value"
                      nameKey="name"
                      label={({ name, percent }) => `${name.split(" ")[0]} ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {pieData.map((_, i) => (
                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v: number) => formatPaise(v)} />
                  </PieChart>
                </ResponsiveContainer>
              )}
              {currentMc && (
                <div className="mt-3 space-y-1 text-xs text-gray-600">
                  <div className="flex justify-between"><span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-400" />Yarn</span><span>{formatPaise(currentMc.yarn_cost_paise)}</span></div>
                  <div className="flex justify-between"><span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-violet-500" />Payroll</span><span>{formatPaise(currentMc.payroll_paise)}</span></div>
                  <div className="flex justify-between"><span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-gray-400" />Expenses</span><span>{formatPaise(currentMc.expenses_paise)}</span></div>
                </div>
              )}
            </div>
          </div>

          {/* Receivables Table */}
          {receivables && (
            <section>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-base font-semibold text-gray-900">
                  Receivables by Buyer
                  {receivables.total_overdue_paise > 0 && (
                    <span className="ml-2 text-xs font-normal text-red-600 bg-red-50 border border-red-200 rounded px-1.5 py-0.5">
                      {formatPaise(receivables.total_overdue_paise)} overdue
                    </span>
                  )}
                </h2>
                <span className="text-sm text-gray-500">Total: {formatPaise(receivables.total_outstanding_paise)}</span>
              </div>
              {receivables.by_buyer.length === 0 ? (
                <div className="bg-white rounded-lg border border-gray-200 p-6 text-center text-gray-400 text-sm">
                  No outstanding receivables
                </div>
              ) : (
                <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium text-gray-500">Buyer</th>
                        <th className="px-4 py-3 text-right font-medium text-gray-500">Invoices</th>
                        <th className="px-4 py-3 text-right font-medium text-gray-500">Outstanding</th>
                        <th className="px-4 py-3 text-right font-medium text-gray-500">Overdue</th>
                        <th className="px-4 py-3 text-right font-medium text-gray-500">Overdue %</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {receivables.by_buyer.map((b) => {
                        const overdueRatio = b.outstanding_paise > 0 ? b.overdue_paise / b.outstanding_paise : 0;
                        const isHighRisk = overdueRatio > 0.5;
                        return (
                          <tr key={b.buyer_id} className={isHighRisk ? "bg-red-50" : "hover:bg-gray-50"}>
                            <td className="px-4 py-3 font-medium text-gray-900">{b.buyer_name}</td>
                            <td className="px-4 py-3 text-right tabular-nums text-gray-600">{b.invoice_count}</td>
                            <td className="px-4 py-3 text-right tabular-nums font-medium">{formatPaise(b.outstanding_paise)}</td>
                            <td className={`px-4 py-3 text-right tabular-nums ${b.overdue_paise > 0 ? "text-red-600 font-medium" : "text-gray-400"}`}>
                              {b.overdue_paise > 0 ? formatPaise(b.overdue_paise) : "—"}
                            </td>
                            <td className="px-4 py-3 text-right">
                              {b.outstanding_paise > 0 ? (
                                <div className="flex items-center justify-end gap-2">
                                  <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                    <div
                                      className={`h-full rounded-full ${overdueRatio > 0.5 ? "bg-red-500" : overdueRatio > 0.2 ? "bg-yellow-500" : "bg-green-500"}`}
                                      style={{ width: `${Math.min(100, overdueRatio * 100)}%` }}
                                    />
                                  </div>
                                  <span className="text-xs text-gray-500">{(overdueRatio * 100).toFixed(0)}%</span>
                                </div>
                              ) : "—"}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}

          {/* Payables Table */}
          {payables && (
            <section>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-base font-semibold text-gray-900">
                  Payables by Supplier
                  {payables.total_overdue_paise > 0 && (
                    <span className="ml-2 text-xs font-normal text-orange-700 bg-orange-50 border border-orange-200 rounded px-1.5 py-0.5">
                      {formatPaise(payables.total_overdue_paise)} overdue
                    </span>
                  )}
                </h2>
                <span className="text-sm text-gray-500">Total: {formatPaise(payables.total_outstanding_paise)}</span>
              </div>
              {payables.by_supplier.length === 0 ? (
                <div className="bg-white rounded-lg border border-gray-200 p-6 text-center text-gray-400 text-sm">
                  No outstanding payables
                </div>
              ) : (
                <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium text-gray-500">Supplier</th>
                        <th className="px-4 py-3 text-right font-medium text-gray-500">Bills</th>
                        <th className="px-4 py-3 text-right font-medium text-gray-500">Outstanding</th>
                        <th className="px-4 py-3 text-right font-medium text-gray-500">Overdue</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {payables.by_supplier.map((s) => (
                        <tr key={s.supplier_id} className={s.overdue_paise > 0 ? "bg-orange-50 hover:bg-orange-100" : "hover:bg-gray-50"}>
                          <td className="px-4 py-3 font-medium text-gray-900">{s.supplier_name}</td>
                          <td className="px-4 py-3 text-right tabular-nums text-gray-600">{s.bill_count}</td>
                          <td className="px-4 py-3 text-right tabular-nums font-medium">{formatPaise(s.outstanding_paise)}</td>
                          <td className={`px-4 py-3 text-right tabular-nums ${s.overdue_paise > 0 ? "text-orange-700 font-medium" : "text-gray-400"}`}>
                            {s.overdue_paise > 0 ? formatPaise(s.overdue_paise) : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}

          {/* Section links */}
          <section>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Finance Sections</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {SUB_PAGES.map((sp) => (
                <Link
                  key={sp.path}
                  to={sp.path}
                  className="bg-white rounded-lg border border-gray-200 px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition"
                >
                  {sp.label}
                </Link>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
