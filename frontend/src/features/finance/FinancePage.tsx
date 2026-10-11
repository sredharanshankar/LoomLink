import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
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
  { label: "Invoices", path: "/app/finance/invoices" },
  { label: "Supplier Bills", path: "/app/finance/supplier-bills" },
  { label: "Expenses", path: "/app/finance/expenses" },
  { label: "Payments", path: "/app/finance/payments" },
  { label: "Month Close", path: "/app/finance/month-close" },
  { label: "Payroll", path: "/app/workers/payroll" },
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
    <div className="p-6 space-y-6">
      <PageHeader title="Finance" />

      {isLoading ? (
        <Skeleton rows={4} className="max-w-sm" />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiTile label="Revenue" value={mc ? formatPaise(mc.revenue_subtotal_paise) : "-"} />
          <KpiTile label="Costs" value={mc ? formatPaise(mc.total_cost_paise) : "-"} />
          <KpiTile label="Profit" value={mc ? formatPaise(mc.gross_profit_paise) : "-"} />
          <KpiTile label="Receivables" value={receivables ? formatPaise(receivables.total_outstanding_paise) : "-"} />
        </div>
      )}

      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Sections</h2>
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
