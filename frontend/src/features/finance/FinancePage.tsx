import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ArrowRight, Banknote, CalendarCheck, CreditCard, Landmark, Receipt, TrendingUp, Wallet, Scale } from "lucide-react";
import { api } from "../../lib/api";
import { formatPaise } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import KpiTile from "../../components/ui/KpiTile";
import Skeleton from "../../components/ui/Skeleton";

interface Receivables {
  total_outstanding_paise: number;
  total_overdue_paise: number;
  by_buyer: { buyer_name: string; outstanding_paise: number; overdue_paise: number; invoice_count: number }[];
}

interface MonthClose {
  revenue_subtotal_paise: number;
  revenue_total_paise: number;
  yarn_cost_paise: number;
  expenses_paise: number;
  payroll_paise: number;
  total_cost_paise: number;
  gross_profit_paise: number;
}

const SUB_PAGES = [
  { label: "Payments", path: "/app/payments", icon: CreditCard, body: "Record and allocate buyer payments" },
  { label: "Supplier bills", path: "/app/supplier-bills", icon: Receipt, body: "Yarn and service payables" },
  { label: "Expenses", path: "/app/expenses", icon: Wallet, body: "Day-to-day mill spending" },
  { label: "Month close", path: "/app/finance/month-close", icon: CalendarCheck, body: "Revenue, costs and margin by period" },
  { label: "Payroll", path: "/app/payroll", icon: Banknote, body: "Wages from attendance and output" },
];

export default function FinancePage() {
  const period = new Date().toISOString().slice(0, 7);

  const { data: receivables, isLoading: loadingRec } = useQuery({
    queryKey: ["finance-receivables"],
    queryFn: () => api.get<Receivables>("/finance/receivables"),
  });

  const { data: mc, isLoading: loadingMc } = useQuery({
    queryKey: ["finance-month-close", period],
    queryFn: () => api.get<MonthClose>(`/finance/month-close?period=${period}`),
  });

  const isLoading = loadingRec || loadingMc;

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader title="Finance" subtitle={`Month to date · ${new Date().toLocaleDateString("en-IN", { month: "long", year: "numeric" })}`} />

      {isLoading ? (
        <Skeleton rows={4} className="max-w-sm" />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiTile label="Revenue" icon={TrendingUp} tone="brand" value={mc ? formatPaise(mc.revenue_subtotal_paise) : "—"} />
          <KpiTile label="Costs" icon={Scale} tone="amber" value={mc ? formatPaise(mc.total_cost_paise) : "—"} />
          <KpiTile
            label="Gross profit"
            icon={Landmark}
            tone={mc && mc.gross_profit_paise < 0 ? "red" : "emerald"}
            value={mc ? formatPaise(mc.gross_profit_paise) : "—"}
          />
          <KpiTile
            label="Receivables"
            icon={Wallet}
            tone="sky"
            value={receivables ? formatPaise(receivables.total_outstanding_paise) : "—"}
            sub={receivables?.total_overdue_paise ? `${formatPaise(receivables.total_overdue_paise)} overdue` : undefined}
            trend={receivables?.total_overdue_paise ? "down" : undefined}
          />
        </div>
      )}

      <section>
        <h2 className="mb-3 text-[15px] font-semibold text-gray-900">Workspaces</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {SUB_PAGES.map(({ label, path, icon: Icon, body }) => (
            <Link
              key={path}
              to={path}
              className="card group flex items-center gap-4 p-4 transition-all hover:-translate-y-0.5 hover:shadow-lift"
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 ring-1 ring-inset ring-brand-600/10">
                <Icon className="h-5 w-5" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-semibold text-gray-900">{label}</span>
                <span className="block text-xs text-gray-500">{body}</span>
              </span>
              <ArrowRight className="h-4 w-4 text-gray-300 transition-transform group-hover:translate-x-0.5 group-hover:text-gray-500" />
            </Link>
          ))}
        </div>
      </section>

      {receivables && receivables.by_buyer?.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Outstanding Receivables</h2>
          <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Buyer</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Outstanding</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Overdue</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Invoices</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {receivables.by_buyer.map((r) => (
                  <tr key={r.buyer_name}>
                    <td className="px-4 py-3 text-gray-900">{r.buyer_name}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{formatPaise(r.outstanding_paise)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{formatPaise(r.overdue_paise)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{r.invoice_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
