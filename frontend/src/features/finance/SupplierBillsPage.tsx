import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatPaise, formatDate } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import Badge from "../../components/ui/Badge";
import Table from "../../components/ui/Table";

interface SupplierBill {
  id: string;
  code: string;
  supplier_name: string;
  bill_no: string;
  bill_date: string;
  due_date: string;
  amount_paise: number;
  amount_paid_paise: number;
  balance_paise: number;
  status: string;
}

interface SupplierBillsResponse {
  items: SupplierBill[];
  total: number;
}

const STATUS_COLOR: Record<string, "green" | "yellow" | "red" | "gray"> = {
  paid: "green",
  partial: "yellow",
  overdue: "red",
  pending: "gray",
};

const columns = [
  { key: "code", header: "Code" },
  { key: "supplier_name", header: "Supplier" },
  { key: "bill_no", header: "Bill No" },
  { key: "bill_date", header: "Date", render: (r: SupplierBill) => formatDate(r.bill_date) },
  { key: "due_date", header: "Due", render: (r: SupplierBill) => formatDate(r.due_date) },
  { key: "amount_paise", header: "Amount", render: (r: SupplierBill) => formatPaise(r.amount_paise), className: "text-right" },
  { key: "amount_paid_paise", header: "Paid", render: (r: SupplierBill) => formatPaise(r.amount_paid_paise), className: "text-right" },
  { key: "balance_paise", header: "Balance", render: (r: SupplierBill) => formatPaise(r.balance_paise), className: "text-right" },
  {
    key: "status",
    header: "Status",
    render: (r: SupplierBill) => <Badge color={STATUS_COLOR[r.status] ?? "gray"}>{r.status}</Badge>,
  },
];

export default function SupplierBillsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["supplier-bills"],
    queryFn: () => api.get<SupplierBillsResponse>("/supplier-bills?page=1&size=50"),
  });

  return (
    <div className="p-6">
      <PageHeader title="Supplier Bills" subtitle={data ? `${data.total} bills` : undefined} />
      {isLoading ? (
        <Skeleton rows={8} />
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <Table columns={columns} data={data?.items ?? []} rowKey={(r) => r.id} />
        </div>
      )}
    </div>
  );
}
