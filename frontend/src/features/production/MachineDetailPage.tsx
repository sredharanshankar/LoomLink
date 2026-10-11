import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatCm, formatDateTime } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";
import { useAuth } from "../../lib/auth";
import { can } from "../../lib/permissions";

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
  current_job: {
    id: string; code: string; stage: string; order_code: string;
    fabric_type: string; quantity_cm: number; planned_qty: number; produced_qty: number;
  } | null;
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
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [notes, setNotes] = useState("");
  const [showNotesFor, setShowNotesFor] = useState<"breakdown" | "maintenance" | null>(null);

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

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["machine", id] });

  const breakdownMutation = useMutation({
    mutationFn: (n: string) => api.post(`/machines/${id}/breakdown`, { notes: n }),
    onSuccess: () => { invalidate(); setShowNotesFor(null); setNotes(""); },
  });

  const repairedMutation = useMutation({
    mutationFn: () => api.post(`/machines/${id}/repaired`, {}),
    onSuccess: invalidate,
  });

  const maintenanceMutation = useMutation({
    mutationFn: (n: string) => api.post(`/machines/${id}/maintenance`, { notes: n }),
    onSuccess: () => { invalidate(); setShowNotesFor(null); setNotes(""); },
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

  const canOperate = can(user?.role, "production:write");
  const status = machine.status;

  return (
    <div className="p-6">
      <PageHeader
        title={machine.name}
        subtitle={machine.code}
        actions={
          canOperate ? (
            <div className="flex items-center gap-2">
              {(status === "idle" || status === "running") && (
                <button
                  onClick={() => setShowNotesFor(showNotesFor === "breakdown" ? null : "breakdown")}
                  className="inline-flex items-center rounded-lg px-3 h-9 text-sm font-medium bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
                >
                  ⚠ Report Breakdown
                </button>
              )}
              {status === "breakdown" && (
                <button
                  onClick={() => repairedMutation.mutate()}
                  disabled={repairedMutation.isPending}
                  className="inline-flex items-center rounded-lg px-3 h-9 text-sm font-medium bg-green-600 text-white hover:bg-green-700 transition-colors disabled:opacity-50"
                >
                  {repairedMutation.isPending ? "Marking…" : "✓ Mark Repaired"}
                </button>
              )}
              {status === "idle" && (
                <button
                  onClick={() => setShowNotesFor(showNotesFor === "maintenance" ? null : "maintenance")}
                  className="inline-flex items-center rounded-lg px-3 h-9 text-sm font-medium bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors"
                >
                  🔧 Put in Maintenance
                </button>
              )}
              {status === "maintenance" && (
                <button
                  onClick={() => repairedMutation.mutate()}
                  disabled={repairedMutation.isPending}
                  className="inline-flex items-center rounded-lg px-3 h-9 text-sm font-medium bg-green-600 text-white hover:bg-green-700 transition-colors disabled:opacity-50"
                >
                  {repairedMutation.isPending ? "Marking…" : "✓ Mark Ready"}
                </button>
              )}
            </div>
          ) : null
        }
      />

      {/* Notes input panel */}
      {showNotesFor && (
        <div className="mb-4 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-end gap-3">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {showNotesFor === "breakdown" ? "Breakdown reason" : "Maintenance notes"} (optional)
            </label>
            <input
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. Motor failure, belt snapped…"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
          <button
            onClick={() => {
              if (showNotesFor === "breakdown") breakdownMutation.mutate(notes);
              else maintenanceMutation.mutate(notes);
            }}
            disabled={breakdownMutation.isPending || maintenanceMutation.isPending}
            className="rounded-lg px-4 h-9 text-sm font-medium bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-900 hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            Confirm
          </button>
          <button
            onClick={() => { setShowNotesFor(null); setNotes(""); }}
            className="rounded-lg px-3 h-9 text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            Cancel
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">Stage</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">{formatStatus(machine.stage)}</p>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">Status</p>
          <Badge color={STATUS_COLORS[machine.status] ?? "gray"}>
            {formatStatus(machine.status)}
          </Badge>
        </div>
        {machine.current_job ? (
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Running Process</p>
            <p className="text-lg font-bold text-green-800 dark:text-green-400">{formatStatus(machine.current_job.stage)}</p>
            <Link to={`/app/jobs/${machine.current_job.id}`} className="text-blue-600 hover:underline text-sm font-medium">
              {machine.current_job.code}
            </Link>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Order: <span className="font-medium text-gray-700 dark:text-gray-300">{machine.current_job.order_code}</span>
              &nbsp;·&nbsp; {machine.current_job.fabric_type}
            </p>
            {machine.current_job.planned_qty > 0 && (() => {
              const pct = Math.min(100, Math.round((machine.current_job!.produced_qty / machine.current_job!.planned_qty) * 100));
              return (
                <div className="mt-2">
                  <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                    <span>{formatCm(machine.current_job!.produced_qty)} done</span>
                    <span>{pct}%</span>
                  </div>
                  <div className="w-full bg-green-200 dark:bg-green-900/40 rounded-full h-1.5">
                    <div className="bg-green-600 h-1.5 rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })()}
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">Running Process</p>
            <p className="text-base font-medium text-gray-400 mt-1">No active job</p>
          </div>
        )}
      </div>

      {(machine.speeds ?? []).length > 0 && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Speeds</h2>
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Fabric Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Metres/Hour</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {(machine.speeds ?? []).map((speed) => (
                  <tr key={speed.fabric_type}>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{speed.fabric_type}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{speed.metres_per_hour}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {jobs && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Recent Jobs</h2>
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Code</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Order</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Quantity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {(jobs.items ?? []).map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{job.code}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{job.order_code}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{formatCm(job.planned_qty)}</td>
                    <td className="px-4 py-3 text-sm">
                      <Badge color="gray">{formatStatus(job.status)}</Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{formatDateTime(job.created_at)}</td>
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
