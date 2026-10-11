import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatCm, formatDateTime } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";

interface Speed {
  fabric_type: string;
  metres_per_hour: number;
}

interface Machine {
  id: string;
  code: string;
  name: string;
  stage: string;
  status: string;
  current_job: { id: string; code: string; stage: string; order_code: string; fabric_type: string; quantity_cm: number } | null;
  speeds: Speed[];
}

interface Job {
  id: string;
  code: string;
  order_code: string;
  status: string;
  planned_qty: number;
  created_at: string;
}

interface JobsResponse {
  items: Job[];
  total: number;
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

export default function MachineDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: machine, isLoading, isError } = useQuery<Machine>({
    queryKey: ["machine", id],
    queryFn: () => api.get(`/machines/${id}`),
    enabled: !!id,
  });

  const { data: jobs } = useQuery<JobsResponse>({
    queryKey: ["machine-jobs", id],
    queryFn: () => api.get(`/jobs?machine_id=${id}&page=1&size=10`),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-6"><Skeleton rows={6} /></div>;

  if (isError || !machine) {
    return (
      <div className="p-6">
        <div className="bg-red-50 text-red-700 rounded-lg border border-red-200 p-4">
          Failed to load machine details.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <PageHeader title={machine.name} subtitle={machine.code} />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Stage</p>
          <p className="text-lg font-semibold text-gray-900">{formatStatus(machine.stage)}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Status</p>
          <Badge color={STATUS_COLORS[machine.status] ?? "gray"}>
            {formatStatus(machine.status)}
          </Badge>
        </div>
        {machine.current_job ? (
          <div className="bg-green-50 rounded-lg border border-green-200 p-4">
            <p className="text-sm text-gray-500 mb-1">Running Process</p>
            <p className="text-lg font-bold text-green-800">{formatStatus(machine.current_job.stage)}</p>
            <Link to={`/app/jobs/${machine.current_job.id}`} className="text-blue-600 hover:underline text-sm font-medium">
              {machine.current_job.code}
            </Link>
            <p className="text-xs text-gray-500 mt-1">
              Order: {machine.current_job.order_code} &nbsp;·&nbsp; {machine.current_job.fabric_type} &nbsp;·&nbsp; {formatCm(machine.current_job.quantity_cm)}
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-sm text-gray-500">Running Process</p>
            <p className="text-base font-medium text-gray-400 mt-1">No active job</p>
          </div>
        )}
      </div>

      {(machine.speeds ?? []).length > 0 && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Speeds</h2>
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fabric Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Metres/Hour</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {(machine.speeds ?? []).map((speed) => (
                  <tr key={speed.fabric_type}>
                    <td className="px-4 py-3 text-sm text-gray-700">{speed.fabric_type}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{speed.metres_per_hour}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {jobs && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Recent Jobs</h2>
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {(jobs.items ?? []).map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{job.code}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{job.order_code}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{formatCm(job.planned_qty)}</td>
                    <td className="px-4 py-3 text-sm">
                      <Badge color="gray">{formatStatus(job.status)}</Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">{formatDateTime(job.created_at)}</td>
                  </tr>
                ))}
                {(jobs.items ?? []).length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                      No jobs found for this machine.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
