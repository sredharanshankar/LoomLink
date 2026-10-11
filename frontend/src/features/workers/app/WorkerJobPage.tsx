import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import { formatCm, formatDateTime } from "../../../lib/format";
import PageHeader from "../../../components/ui/PageHeader";
import Badge from "../../../components/ui/Badge";
import Skeleton from "../../../components/ui/Skeleton";

interface Job {
  id: string;
  code: string;
  order_code: string;
  stage: string;
  status: string;
  planned_qty: number;
  produced_qty: number;
  waste_qty: number;
  machine_code: string;
  started_at: string | null;
}

const STATUS_COLOR: Record<string, "green" | "yellow" | "gray" | "red" | "blue"> = {
  running: "green",
  queued: "gray",
  paused: "yellow",
  finished: "blue",
  cancelled: "red",
};

export default function WorkerJobPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [metres, setMetres] = useState("");

  const { data: job, isLoading } = useQuery({
    queryKey: ["job", id],
    queryFn: () => api.get<Job>(`/jobs/${id}`),
    enabled: !!id,
  });

  const progressMutation = useMutation({
    mutationFn: (metresCm: number) => api.post(`/jobs/${id}/progress`, { delta_qty: metresCm }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job", id] });
      setMetres("");
    },
  });

  const finishMutation = useMutation({
    mutationFn: () => api.post(`/jobs/${id}/finish`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["job", id] }),
  });

  const pauseMutation = useMutation({
    mutationFn: () => api.post(`/jobs/${id}/pause`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["job", id] }),
  });

  if (isLoading) return <div className="p-4"><Skeleton rows={6} /></div>;
  if (!job) return <div className="p-4 text-center text-gray-500">Job not found</div>;

  const progress = job.planned_qty > 0 ? Math.min((job.produced_qty / job.planned_qty) * 100, 100) : 0;
  const isRunning = job.status === "running";

  return (
    <div className="p-4 space-y-4">
      <PageHeader title={job.code} subtitle={`Order ${job.order_code}`} />

      <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">Status</span>
          <Badge color={STATUS_COLOR[job.status] ?? "gray"}>{job.status}</Badge>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Stage</span>
          <span className="text-sm font-medium">{job.stage}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Machine</span>
          <span className="text-sm font-medium">{job.machine_code}</span>
        </div>
        {job.started_at && (
          <div className="flex justify-between">
            <span className="text-sm text-gray-500">Started</span>
            <span className="text-sm font-medium">{formatDateTime(job.started_at)}</span>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Progress</span>
          <span className="font-medium">{formatCm(job.produced_qty)} / {formatCm(job.planned_qty)}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-blue-600 h-3 rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-400">
          <span>{progress.toFixed(0)}%</span>
          <span>Waste: {formatCm(job.waste_qty)}</span>
        </div>
      </div>

      {isRunning && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
          <label className="block text-sm font-medium text-gray-700">Add metres produced</label>
          <input
            type="number"
            inputMode="decimal"
            className="w-full border border-gray-300 rounded-lg px-4 py-3 text-lg"
            placeholder="Metres"
            value={metres}
            onChange={(e) => setMetres(e.target.value)}
          />
          <button
            className="w-full bg-blue-600 text-white rounded-lg py-4 text-lg font-semibold active:bg-blue-700 disabled:opacity-50"
            disabled={!metres || progressMutation.isPending}
            onClick={() => progressMutation.mutate(Math.round(parseFloat(metres) * 100))}
          >
            {progressMutation.isPending ? "Saving..." : "+ Metres"}
          </button>
        </div>
      )}

      {progressMutation.isError && (
        <p className="text-red-600 text-sm text-center">Failed to record progress</p>
      )}

      {isRunning && (
        <div className="flex gap-3">
          <button
            className="flex-1 bg-yellow-500 text-white rounded-lg py-4 text-lg font-semibold active:bg-yellow-600 disabled:opacity-50"
            disabled={pauseMutation.isPending}
            onClick={() => pauseMutation.mutate()}
          >
            {pauseMutation.isPending ? "Pausing..." : "Pause"}
          </button>
          <button
            className="flex-1 bg-green-600 text-white rounded-lg py-4 text-lg font-semibold active:bg-green-700 disabled:opacity-50"
            disabled={finishMutation.isPending}
            onClick={() => finishMutation.mutate()}
          >
            {finishMutation.isPending ? "Finishing..." : "Finish"}
          </button>
        </div>
      )}
    </div>
  );
}
