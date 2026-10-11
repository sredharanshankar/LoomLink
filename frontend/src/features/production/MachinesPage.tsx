import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";

interface Machine {
  id: string;
  code: string;
  name: string;
  stage: string;
  status: string;
  status_changed_at: string;
}

interface MachinesResponse {
  items: Machine[];
}

const STATUS_COLORS: Record<string, "green" | "yellow" | "red" | "blue" | "gray"> = {
  running: "green",
  idle: "yellow",
  breakdown: "red",
  maintenance: "blue",
};

function formatStatus(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function MachinesPage() {
  const { data, isLoading, isError } = useQuery<MachinesResponse>({
    queryKey: ["machines"],
    queryFn: () => api.get("/machines"),
  });

  return (
    <div className="p-6">
      <PageHeader title="Machines" />

      {isLoading && <Skeleton rows={8} />}

      {isError && (
        <div className="bg-red-50 text-red-700 rounded-lg border border-red-200 p-4">
          Failed to load machines.
        </div>
      )}

      {data && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stage</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status Changed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.items.map((machine) => (
                <tr key={machine.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm">
                    <Link to={`/app/machines/${machine.id}`} className="text-blue-600 hover:underline font-medium">
                      {machine.code}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">{machine.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{formatStatus(machine.stage)}</td>
                  <td className="px-4 py-3 text-sm">
                    <Badge color={STATUS_COLORS[machine.status] ?? "gray"}>
                      {formatStatus(machine.status)}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">{formatDateTime(machine.status_changed_at)}</td>
                </tr>
              ))}
              {data.items.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                    No machines found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
