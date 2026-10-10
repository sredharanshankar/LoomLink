import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatPaise } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import Badge from "../../components/ui/Badge";
import Card from "../../components/ui/Card";
import Table from "../../components/ui/Table";

interface PayrollWorker {
  name: string;
  employee_code: string;
  days_worked: number;
  daily_wage_paise: number;
  total_paise: number;
}

interface PayrollRun {
  id: string;
  period: string;
  status: string;
  total_paise: number;
  workers: PayrollWorker[];
}

const STATUS_COLOR: Record<string, "green" | "yellow" | "gray" | "blue"> = {
  completed: "green",
  approved: "green",
  pending: "yellow",
  draft: "gray",
  processing: "blue",
};

const workerColumns = [
  { key: "employee_code", header: "Code" },
  { key: "name", header: "Name" },
  { key: "days_worked", header: "Days", className: "text-right" },
  { key: "daily_wage_paise", header: "Daily Wage", render: (r: PayrollWorker) => formatPaise(r.daily_wage_paise), className: "text-right" },
  { key: "total_paise", header: "Total", render: (r: PayrollWorker) => formatPaise(r.total_paise), className: "text-right" },
];

export default function PayrollRunPage() {
  const { id } = useParams<{ id: string }>();

  const { data: run, isLoading } = useQuery({
    queryKey: ["payroll-run", id],
    queryFn: () => api.get<PayrollRun>(`/payroll/runs/${id}`),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <PageHeader title="Payroll Run" />
        <Skeleton rows={10} />
      </div>
    );
  }

  if (!run) {
    return (
      <div className="p-6">
        <PageHeader title="Payroll Run" subtitle="Not found" />
      </div>
    );
  }

  return (
    <div className="p-6">
      <PageHeader
        title={`Payroll Run: ${run.period}`}
        actions={<Badge color={STATUS_COLOR[run.status] ?? "gray"}>{run.status}</Badge>}
      />
      <Card className="mb-6">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-gray-500">Period</p>
            <p className="font-medium text-gray-900">{run.period}</p>
          </div>
          <div>
            <p className="text-gray-500">Status</p>
            <p className="font-medium text-gray-900">{run.status}</p>
          </div>
          <div>
            <p className="text-gray-500">Total</p>
            <p className="font-medium text-gray-900">{formatPaise(run.total_paise)}</p>
          </div>
        </div>
      </Card>
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <Table columns={workerColumns} data={run.workers} rowKey={(r) => r.employee_code} />
      </div>
    </div>
  );
}
