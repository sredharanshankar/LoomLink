import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatPaise, formatDateTime } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import Badge from "../../components/ui/Badge";
import Card from "../../components/ui/Card";
import Table from "../../components/ui/Table";

interface LineItem {
  description: string;
  qty: number;
  rate_paise: number;
  amount_paise: number;
}

interface Invoice {
  id: string;
  code: string;
  buyer_name: string;
  status: string;
  amount_paise: number;
  gst_paise: number;
  total_paise: number;
  items: LineItem[];
  created_at: string;
}

const STATUS_COLOR: Record<string, "green" | "yellow" | "red" | "gray" | "blue"> = {
  paid: "green",
  sent: "blue",
  draft: "gray",
  overdue: "red",
  partial: "yellow",
};

const lineColumns = [
  { key: "description", header: "Description" },
  { key: "qty", header: "Qty", className: "text-right" },
  { key: "rate_paise", header: "Rate", render: (r: LineItem) => formatPaise(r.rate_paise), className: "text-right" },
  { key: "amount_paise", header: "Amount", render: (r: LineItem) => formatPaise(r.amount_paise), className: "text-right" },
];

export default function InvoiceDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: invoice, isLoading } = useQuery({
    queryKey: ["invoices", id],
    queryFn: () => api.get<Invoice>(`/invoices/${id}`),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <PageHeader title="Invoice" />
        <Skeleton rows={10} />
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="p-6">
        <PageHeader title="Invoice" subtitle="Not found" />
      </div>
    );
  }

  return (
    <div className="p-6">
      <PageHeader
        title={invoice.code}
        subtitle={`Created ${formatDateTime(invoice.created_at)}`}
        actions={<Badge color={STATUS_COLOR[invoice.status] ?? "gray"}>{invoice.status}</Badge>}
      />
      <Card className="mb-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-gray-500">Buyer</p>
            <p className="font-medium text-gray-900">{invoice.buyer_name}</p>
          </div>
          <div>
            <p className="text-gray-500">Status</p>
            <p className="font-medium text-gray-900">{invoice.status}</p>
          </div>
          <div>
            <p className="text-gray-500">Date</p>
            <p className="font-medium text-gray-900">{formatDateTime(invoice.created_at)}</p>
          </div>
          <div>
            <p className="text-gray-500">Total</p>
            <p className="font-medium text-gray-900">{formatPaise(invoice.total_paise)}</p>
          </div>
        </div>
      </Card>
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm mb-6">
        <Table columns={lineColumns} data={invoice.items} rowKey={(r) => r.description} />
      </div>
      <Card>
        <div className="flex flex-col items-end gap-1 text-sm">
          <div className="flex justify-between w-48">
            <span className="text-gray-500">Subtotal</span>
            <span className="font-medium">{formatPaise(invoice.amount_paise)}</span>
          </div>
          <div className="flex justify-between w-48">
            <span className="text-gray-500">GST</span>
            <span className="font-medium">{formatPaise(invoice.gst_paise)}</span>
          </div>
          <div className="flex justify-between w-48 border-t border-gray-200 pt-1 mt-1">
            <span className="text-gray-900 font-semibold">Total</span>
            <span className="font-bold text-gray-900">{formatPaise(invoice.total_paise)}</span>
          </div>
        </div>
      </Card>
    </div>
  );
}
