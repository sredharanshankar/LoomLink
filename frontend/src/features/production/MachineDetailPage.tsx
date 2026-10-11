import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, CheckCircle2, Wrench } from "lucide-react";
import { api } from "../../lib/api";
import { formatCm, formatDateTime } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
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
    <div className="p-6 lg:p-8">
      <Link to="/app/machines" className="mb-3 inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800">
        <ArrowLeft className="h-4 w-4" /> Machines
      </Link>
      <PageHeader
        eyebrow={machine.code}
        title={machine.name}
        subtitle={`${formatStatus(machine.stage)} stage`}
        actions={
          canOperate ? (
            <>
              {(status === "idle" || status === "running") && (
                <Button
                  variant="secondary"
                  className="text-red-700"
                  onClick={() => setShowNotesFor(showNotesFor === "breakdown" ? null : "breakdown")}
                >
                  <AlertTriangle className="h-4 w-4" /> Report breakdown
                </Button>
              )}
              {status === "idle" && (
                <Button variant="secondary" onClick={() => setShowNotesFor(showNotesFor === "maintenance" ? null : "maintenance")}>
                  <Wrench className="h-4 w-4" /> Put in maintenance
                </Button>
              )}
              {(status === "breakdown" || status === "maintenance") && (
                <Button variant="success" loading={repairedMutation.isPending} onClick={() => repairedMutation.mutate()}>
                  <CheckCircle2 className="h-4 w-4" />
                  {status === "breakdown" ? "Mark repaired" : "Mark ready"}
                </Button>
              )}
            </>
          ) : null
        }
      />

      {showNotesFor && (
        <div className="card mb-6 flex animate-fade-up flex-col gap-3 border-l-2 border-l-brand-500 p-4 sm:flex-row sm:items-end">
          <div className="flex-1">
            <Input
              label={`${showNotesFor === "breakdown" ? "Breakdown reason" : "Maintenance notes"} (optional)`}
              placeholder={showNotesFor === "breakdown" ? "e.g. Motor failure, belt snapped…" : "e.g. Scheduled service…"}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" onClick={() => { setShowNotesFor(null); setNotes(""); }}>
              Cancel
            </Button>
            <Button
              variant={showNotesFor === "breakdown" ? "danger" : "primary"}
              loading={breakdownMutation.isPending || maintenanceMutation.isPending}
              onClick={() => {
                if (showNotesFor === "breakdown") breakdownMutation.mutate(notes);
                else maintenanceMutation.mutate(notes);
              }}
            >
              {showNotesFor === "breakdown" ? "Report breakdown" : "Start maintenance"}
            </Button>
          </div>
        </div>
      )}

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
            <Link to={`/app/jobs/${machine.current_job.id}`} className="text-brand-600 hover:underline text-sm font-medium">
              {machine.current_job.code}
            </Link>
            <p className="text-xs text-gray-500 mt-1">
              Order: <span className="font-medium text-gray-700">{machine.current_job.order_code}</span>
              &nbsp;·&nbsp; {machine.current_job.fabric_type}
            </p>
            {machine.current_job.planned_qty > 0 && (() => {
              const pct = Math.min(100, Math.round((machine.current_job!.produced_qty / machine.current_job!.planned_qty) * 100));
              return (
                <div className="mt-2">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>{formatCm(machine.current_job!.produced_qty)} done</span>
                    <span>{pct}%</span>
                  </div>
                  <div className="w-full bg-green-200 rounded-full h-1.5">
                    <div className="bg-green-600 h-1.5 rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })()}
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
