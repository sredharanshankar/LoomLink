import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import PageHeader from "../../../components/ui/PageHeader";
import Badge from "../../../components/ui/Badge";
import Skeleton from "../../../components/ui/Skeleton";

interface Machine {
  id: string;
  code: string;
  name: string;
  stage: string;
  status: string;
  current_job: string | null;
}

interface QueuedJob {
  id: string;
  code: string;
  order_code: string;
  planned_qty: number;
}

const STATUS_COLOR: Record<string, "green" | "yellow" | "gray" | "red"> = {
  running: "green",
  idle: "gray",
  breakdown: "red",
  maintenance: "yellow",
};

export default function WorkerMachinePage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const { data: machine, isLoading } = useQuery({
    queryKey: ["machine", id],
    queryFn: () => api.get<Machine>(`/machines/${id}`),
    enabled: !!id,
  });

  const isIdle = machine?.status === "idle";

  const { data: queuedJobs } = useQuery({
    queryKey: ["machine-queued-jobs", id],
    queryFn: () => api.get<{ items: QueuedJob[] }>(`/jobs?machine_id=${id}&status=queued`),
    enabled: !!id && isIdle,
  });

  const breakdownMutation = useMutation({
    mutationFn: () => api.post(`/machines/${id}/breakdown`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["machine", id] }),
  });

  if (isLoading) return <div className="p-4"><Skeleton rows={5} /></div>;
  if (!machine) return <div className="p-4 text-center text-gray-500">Machine not found</div>;

  return (
    <div className="p-4 space-y-4">
      <PageHeader title={machine.code} subtitle={machine.name} />

      <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">Status</span>
          <Badge color={STATUS_COLOR[machine.status] ?? "gray"}>{machine.status}</Badge>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Stage</span>
          <span className="text-sm font-medium">{machine.stage}</span>
        </div>
        {machine.current_job && (
          <div className="flex justify-between">
            <span className="text-sm text-gray-500">Current Job</span>
            <span className="text-sm font-medium">{machine.current_job}</span>
          </div>
        )}
      </div>

      {isIdle && queuedJobs?.items && queuedJobs.items.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-700">Eligible Jobs</h2>
          {queuedJobs.items.map((job) => (
            <div key={job.id} className="flex items-center justify-between border-b border-gray-100 pb-2 last:border-0 last:pb-0">
              <div>
                <p className="text-sm font-medium">{job.code}</p>
                <p className="text-xs text-gray-500">Order {job.order_code}</p>
              </div>
              <span className="text-xs text-gray-400">{job.planned_qty} cm</span>
            </div>
          ))}
        </div>
      )}

      {isIdle && queuedJobs?.items?.length === 0 && (
        <p className="text-center text-sm text-gray-400">No queued jobs for this machine</p>
      )}

      {machine.status !== "breakdown" && (
        <button
          className="w-full bg-red-600 text-white rounded-lg py-4 text-lg font-semibold active:bg-red-700 disabled:opacity-50"
          disabled={breakdownMutation.isPending}
          onClick={() => breakdownMutation.mutate()}
        >
          {breakdownMutation.isPending ? "Reporting..." : "Report Breakdown"}
        </button>
      )}

      {breakdownMutation.isError && (
        <p className="text-red-600 text-sm text-center">Failed to report breakdown</p>
      )}
    </div>
  );
}
