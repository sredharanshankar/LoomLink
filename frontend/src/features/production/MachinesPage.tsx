import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";
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

  const colSpan = canOperate ? 6 : 5;

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
                {canOperate && (
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.items.length === 0 && (
                <tr>
                  <td colSpan={colSpan} className="px-4 py-8 text-center text-gray-400">
                    No machines found.
                  </td>
                </tr>
              )}
              {data.items.map((machine) => {
                const isPanelOpen = actionMachineId === machine.id;
                const s = machine.status;
                return (
                  <>
                    <tr key={machine.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">
                        <Link to={`/app/machines/${machine.id}`} className="text-blue-600 hover:underline font-medium">
                          {machine.code}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">{machine.name}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{formatStatus(machine.stage)}</td>
                      <td className="px-4 py-3 text-sm">
                        <Badge color={STATUS_COLORS[s] ?? "gray"}>
                          {formatStatus(s)}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">{formatDateTime(machine.status_changed_at)}</td>

                      {canOperate && (
                        <td className="px-4 py-3 text-sm">
                          <div className="flex items-center gap-2">
                            {(s === "idle" || s === "running") && (
                              <button
                                onClick={() => openPanel(machine.id, "breakdown")}
                                className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                                  isPanelOpen && actionType === "breakdown"
                                    ? "bg-gray-200 text-gray-700"
                                    : "bg-red-100 text-red-700 hover:bg-red-200"
                                }`}
                              >
                                {isPanelOpen && actionType === "breakdown" ? "Cancel" : "⚠ Breakdown"}
                              </button>
                            )}
                            {s === "idle" && (
                              <button
                                onClick={() => openPanel(machine.id, "maintenance")}
                                className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                                  isPanelOpen && actionType === "maintenance"
                                    ? "bg-gray-200 text-gray-700"
                                    : "bg-blue-100 text-blue-700 hover:bg-blue-200"
                                }`}
                              >
                                {isPanelOpen && actionType === "maintenance" ? "Cancel" : "🔧 Maintenance"}
                              </button>
                            )}
                            {s === "breakdown" && (
                              <button
                                onClick={() => repairedMutation.mutate(machine.id)}
                                disabled={repairedMutation.isPending}
                                className="inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium bg-green-600 text-white hover:bg-green-700 transition-colors disabled:opacity-50"
                              >
                                {repairedMutation.isPending ? "Marking…" : "✓ Repaired"}
                              </button>
                            )}
                            {s === "maintenance" && (
                              <button
                                onClick={() => repairedMutation.mutate(machine.id)}
                                disabled={repairedMutation.isPending}
                                className="inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium bg-green-600 text-white hover:bg-green-700 transition-colors disabled:opacity-50"
                              >
                                {repairedMutation.isPending ? "Marking…" : "✓ Mark Ready"}
                              </button>
                            )}
                            {s !== "idle" && s !== "running" && s !== "breakdown" && s !== "maintenance" && (
                              <span className="text-gray-400 text-xs">—</span>
                            )}
                          </div>
                        </td>
                      )}
                    </tr>

                    {isPanelOpen && (
                      <tr key={`${machine.id}-panel`}>
                        <td colSpan={colSpan} className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                          <div className="flex items-end gap-3">
                            <div className="flex-1">
                              <label className="block text-xs font-medium text-gray-700 mb-1">
                                {actionType === "breakdown" ? "Breakdown reason" : "Maintenance notes"} (optional)
                              </label>
                              <input
                                type="text"
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                placeholder={actionType === "breakdown" ? "e.g. Motor failure…" : "e.g. Scheduled service…"}
                                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                              />
                            </div>
                            <button
                              onClick={() => handleConfirm(machine.id)}
                              disabled={breakdownMutation.isPending || maintenanceMutation.isPending}
                              className="rounded-lg px-4 h-9 text-sm font-medium bg-gray-800 text-white hover:opacity-90 transition-opacity disabled:opacity-50"
                            >
                              {breakdownMutation.isPending || maintenanceMutation.isPending ? "Saving…" : "Confirm"}
                            </button>
                            <button
                              onClick={() => { setActionMachineId(null); setActionType(null); setNotes(""); }}
                              className="rounded-lg px-3 h-9 text-sm text-gray-500 hover:text-gray-700 transition-colors"
                            >
                              Cancel
                            </button>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
