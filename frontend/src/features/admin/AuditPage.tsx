import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import Table from "../../components/ui/Table";

interface AuditEntry {
  id: string;
  action: string;
  actor_name: string;
  entity: string;
  timestamp: string;
  details: string;
}

interface AuditResponse {
  items: AuditEntry[];
  total: number;
}

const columns = [
  { key: "timestamp", header: "Time", render: (r: AuditEntry) => formatDateTime(r.timestamp) },
  { key: "actor_name", header: "Actor" },
  { key: "action", header: "Action" },
  { key: "entity", header: "Entity" },
  { key: "details", header: "Details", className: "max-w-xs truncate" },
];

export default function AuditPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["audit"],
    queryFn: () => api.get<AuditResponse>("/audit?page=1&size=50"),
  });

  return (
    <div className="p-6">
      <PageHeader title="Audit Log" subtitle={data ? `${data.total} entries` : undefined} />
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
