import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatCm, formatDateTime } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import Badge from "../../components/ui/Badge";
import Card from "../../components/ui/Card";
import Table from "../../components/ui/Table";

interface DispatchItem {
  roll_code: string;
  length_cm: number;
}

interface Dispatch {
  id: string;
  code: string;
  buyer_name: string;
  status: string;
  items: DispatchItem[];
  created_at: string;
}

const STATUS_COLOR: Record<string, "green" | "yellow" | "gray" | "blue"> = {
  delivered: "green",
  in_transit: "blue",
  packed: "yellow",
  draft: "gray",
};

const itemColumns = [
  { key: "roll_code", header: "Roll Code" },
  { key: "length_cm", header: "Length", render: (r: DispatchItem) => formatCm(r.length_cm), className: "text-right" },
];

export default function DispatchDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: dispatch, isLoading } = useQuery({
    queryKey: ["dispatches", id],
    queryFn: () => api.get<Dispatch>(`/dispatches/${id}`),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <PageHeader title="Dispatch" />
        <Skeleton rows={8} />
      </div>
    );
  }

  if (!dispatch) {
    return (
      <div className="p-6">
        <PageHeader title="Dispatch" subtitle="Not found" />
      </div>
    );
  }

  return (
    <div className="p-6">
      <PageHeader
        title={dispatch.code}
        subtitle={`Created ${formatDateTime(dispatch.created_at)}`}
        actions={<Badge color={STATUS_COLOR[dispatch.status] ?? "gray"}>{dispatch.status}</Badge>}
      />
      <Card className="mb-6">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-gray-500">Buyer</p>
            <p className="font-medium text-gray-900">{dispatch.buyer_name}</p>
          </div>
          <div>
            <p className="text-gray-500">Status</p>
            <p className="font-medium text-gray-900">{dispatch.status}</p>
          </div>
          <div>
            <p className="text-gray-500">Items</p>
            <p className="font-medium text-gray-900">{dispatch.items.length} rolls</p>
          </div>
        </div>
      </Card>
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <Table columns={itemColumns} data={dispatch.items} rowKey={(r) => r.roll_code} />
      </div>
    </div>
  );
}
