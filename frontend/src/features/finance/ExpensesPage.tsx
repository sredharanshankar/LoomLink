import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatPaise, formatDate } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import Table from "../../components/ui/Table";

interface Expense {
  id: string;
  category: string;
  description: string;
  amount_paise: number;
  date: string;
  created_by: string;
}

interface ExpensesResponse {
  items: Expense[];
  total: number;
}

const columns = [
  { key: "date", header: "Date", render: (r: Expense) => formatDate(r.date) },
  { key: "category", header: "Category" },
  { key: "description", header: "Description" },
  { key: "amount_paise", header: "Amount", render: (r: Expense) => formatPaise(r.amount_paise), className: "text-right" },
  { key: "created_by", header: "Created By" },
];

export default function ExpensesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["expenses"],
    queryFn: () => api.get<ExpensesResponse>("/expenses?page=1&size=50"),
  });

  return (
    <div className="p-6">
      <PageHeader title="Expenses" subtitle={data ? `${data.total} entries` : undefined} />
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
