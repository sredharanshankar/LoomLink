import { Fragment, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { clsx } from "clsx";
import { AlertTriangle, CheckCircle2, Wrench } from "lucide-react";
import { api } from "../../lib/api";
import { formatDateTime, formatRelative } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import StatusPill from "../../components/ui/StatusPill";
import Skeleton from "../../components/ui/Skeleton";
import EmptyState from "../../components/ui/EmptyState";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import { useAuth } from "../../lib/auth";
import { can } from "../../lib/permissions";

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

function formatStatus(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function MachinesPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const canOperate = can(user?.role, "production:write");

  const [actionMachineId, setActionMachineId] = useState<string | null>(null);
  const [actionType, setActionType] = useState<"breakdown" | "maintenance" | null>(null);
  const [notes, setNotes] = useState("");

  const { data, isLoading, isError } = useQuery<MachinesResponse>({
    queryKey: ["machines"],
    queryFn: () => api.get("/machines"),
  });

  const breakdownMutation = useMutation({
    mutationFn: ({ machineId, n }: { machineId: string; n: string }) =>
      api.post(`/machines/${machineId}/breakdown`, { notes: n }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["machines"] });
      setActionMachineId(null); setActionType(null); setNotes("");
    },
  });

  const repairedMutation = useMutation({
    mutationFn: (machineId: string) => api.post(`/machines/${machineId}/repaired`, {}),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["machines"] }),
  });

  const maintenanceMutation = useMutation({
    mutationFn: ({ machineId, n }: { machineId: string; n: string }) =>
      api.post(`/machines/${machineId}/maintenance`, { notes: n }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["machines"] });
      setActionMachineId(null); setActionType(null); setNotes("");
    },
  });

  function openPanel(machineId: string, type: "breakdown" | "maintenance") {
    if (actionMachineId === machineId && actionType === type) {
      setActionMachineId(null); setActionType(null); setNotes("");
    } else {
      setActionMachineId(machineId); setActionType(type); setNotes("");
    }
  }

  function handleConfirm(machineId: string) {
    if (actionType === "breakdown") breakdownMutation.mutate({ machineId, n: notes });
    else if (actionType === "maintenance") maintenanceMutation.mutate({ machineId, n: notes });
  }

  const colSpan = canOperate ? 5 : 4;

  const saving = breakdownMutation.isPending || maintenanceMutation.isPending;
  const chip = "inline-flex h-8 items-center gap-1.5 rounded-lg px-2.5 text-[13px] font-medium ring-1 ring-inset transition-colors disabled:opacity-50";

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        title="Machines"
        subtitle={data ? `${data.items.length} machines across spinning, weaving, dyeing and finishing` : undefined}
      />

      {isLoading && <div className="card p-5"><Skeleton rows={8} /></div>}

      {isError && (
        <div className="rounded-xl bg-red-50 p-4 text-sm text-red-700 ring-1 ring-inset ring-red-600/15">Failed to load machines.</div>
      )}

      {data && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50/80">
                  <th className="table-header-cell">Machine</th>
                  <th className="table-header-cell">Stage</th>
                  <th className="table-header-cell">Status</th>
                  <th className="table-header-cell">Since</th>
                  {canOperate && <th className="table-header-cell text-right">Actions</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.items.length === 0 && (
                  <tr>
                    <td colSpan={colSpan}>
                      <EmptyState title="No machines found" />
                    </td>
                  </tr>
                )}
                {data.items.map((machine) => {
                  const isPanelOpen = actionMachineId === machine.id;
                  const s = machine.status;
                  const restoring = repairedMutation.isPending && repairedMutation.variables === machine.id;
                  return (
                    <Fragment key={machine.id}>
                      <tr className={clsx("transition-colors hover:bg-gray-50", isPanelOpen && "bg-gray-50")}>
                        <td className="px-4 py-3">
                          <Link to={`/app/machines/${machine.id}`} className="group block">
                            <span className="font-mono text-sm font-semibold text-gray-900 group-hover:text-brand-600">{machine.code}</span>
                            <span className="block text-xs text-gray-500">{machine.name}</span>
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700">{formatStatus(machine.stage)}</td>
                        <td className="px-4 py-3">
                          <StatusPill status={s} size="sm" />
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500" title={formatDateTime(machine.status_changed_at)}>
                          {formatRelative(machine.status_changed_at)}
                        </td>

                        {canOperate && (
                          <td className="px-4 py-3">
                            <div className="flex items-center justify-end gap-2">
                              {(s === "idle" || s === "running") && (
                                <button
                                  onClick={() => openPanel(machine.id, "breakdown")}
                                  className={clsx(chip, isPanelOpen && actionType === "breakdown"
                                    ? "bg-gray-100 text-gray-700 ring-gray-300"
                                    : "bg-white text-red-700 ring-red-600/25 hover:bg-red-50")}
                                >
                                  <AlertTriangle className="h-3.5 w-3.5" />
                                  Breakdown
                                </button>
                              )}
                              {s === "idle" && (
                                <button
                                  onClick={() => openPanel(machine.id, "maintenance")}
                                  className={clsx(chip, isPanelOpen && actionType === "maintenance"
                                    ? "bg-gray-100 text-gray-700 ring-gray-300"
                                    : "bg-white text-violet-700 ring-violet-600/25 hover:bg-violet-50")}
                                >
                                  <Wrench className="h-3.5 w-3.5" />
                                  Maintenance
                                </button>
                              )}
                              {(s === "breakdown" || s === "maintenance") && (
                                <button
                                  onClick={() => repairedMutation.mutate(machine.id)}
                                  disabled={restoring}
                                  className={clsx(chip, "bg-emerald-600 text-white ring-emerald-600 hover:bg-emerald-700")}
                                >
                                  <CheckCircle2 className="h-3.5 w-3.5" />
                                  {restoring ? "Saving…" : s === "breakdown" ? "Mark repaired" : "Mark ready"}
                                </button>
                              )}
                            </div>
                          </td>
                        )}
                      </tr>

                      {isPanelOpen && (
                        <tr>
                          <td colSpan={colSpan} className="border-l-2 border-brand-500 bg-gray-50 px-4 py-4">
                            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                              <div className="flex-1">
                                <Input
                                  label={`${actionType === "breakdown" ? "Breakdown reason" : "Maintenance notes"} for ${machine.code} (optional)`}
                                  value={notes}
                                  onChange={(e) => setNotes(e.target.value)}
                                  onKeyDown={(e) => e.key === "Enter" && handleConfirm(machine.id)}
                                  placeholder={actionType === "breakdown" ? "e.g. Motor failure, belt snapped…" : "e.g. Scheduled service…"}
                                />
                              </div>
                              <div className="flex gap-2">
                                <Button variant="ghost" onClick={() => { setActionMachineId(null); setActionType(null); setNotes(""); }}>
                                  Cancel
                                </Button>
                                <Button
                                  variant={actionType === "breakdown" ? "danger" : "primary"}
                                  loading={saving}
                                  onClick={() => handleConfirm(machine.id)}
                                >
                                  {actionType === "breakdown" ? "Report breakdown" : "Start maintenance"}
                                </Button>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
