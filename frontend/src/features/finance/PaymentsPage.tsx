import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatPaise, formatDate } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import KpiTile from "../../components/ui/KpiTile";
import Table from "../../components/ui/Table";

interface PaidInvoice {
  id: string;
  code: string;
  buyer_name: string;
  amount_paise: number;
  paid_at: string;
}

interface InvoicesResponse {
  items: PaidInvoice[];
  total: number;
}

interface Receivables {
  total_outstanding_paise: number;
  overdue_paise: number;
  count: number;
}

const columns = [
  { key: "code", header: "Invoice Code" },
  { key: "buyer_name", header: "Buyer" },
  { key: "amount_paise", header: "Amount", render: (r: PaidInvoice) => formatPaise(r.amount_paise), className: "text-right" },
  { key: "paid_at", header: "Paid Date", render: (r: PaidInvoice) => formatDate(r.paid_at) },
];

export default function PaymentsPage() {
  const { data: receivables, isLoading: loadingReceivables } = useQuery({
    queryKey: ["finance-receivables"],
    queryFn: () => api.get<Receivables>("/finance/receivables"),
  });

  const { data: invoices, isLoading: loadingInvoices } = useQuery({
    queryKey: ["invoices", { status: "paid" }],
    queryFn: () => api.get<InvoicesResponse>("/invoices?status=paid&page=1&size=50"),
  });

  return (
    <div className="p-6">
      <PageHeader title="Payments" />
      {loadingReceivables ? (
        <Skeleton rows={2} className="mb-6" />
      ) : receivables ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <KpiTile label="Outstanding" value={formatPaise(receivables.total_outstanding_paise)} />
          <KpiTile label="Overdue" value={formatPaise(receivables.overdue_paise)} trend={receivables.overdue_paise > 0 ? "down" : "neutral"} />
          <KpiTile label="Invoices Due" value={receivables.count} />
        </div>
      ) : null}
      {loadingInvoices ? (
        <Skeleton rows={8} />
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <Table columns={columns} data={invoices?.items ?? []} rowKey={(r) => r.id} emptyMessage="No paid invoices" />
        </div>
      )}
    </div>
  );
}
