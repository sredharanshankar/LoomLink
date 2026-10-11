import { Fragment, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { qk } from "../../lib/query-keys";
import { formatCm, formatDate } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import KpiTile from "../../components/ui/KpiTile";
import Badge from "../../components/ui/Badge";
import { useAuth } from "../../lib/auth";
import { can } from "../../lib/permissions";

interface Roll {
  id: string;
  code: string;
  order_code: string;
  job_code: string;
  machine_code: string;
  length_cm: number;
  grade: string;
  status: string;
  inspected_at: string | null;
  defects: string[];
  created_at: string;
}

interface RollsResponse {
  items: Roll[];
  total: number;
}

interface QueueStatus {
  count: number;
  items: unknown[];
}
interface QueueData {
  pending_qc: QueueStatus;
  rework: QueueStatus;
  passed: QueueStatus;
  rejected: QueueStatus;
}

interface DefectPattern {
  dimension: string;
  ref_id: string;
  ref_label: string;
  defect_count: number;
  inspection_count: number;
  rate: number;
  mill_avg_rate: number;
}
type DefectPatternsResponse = DefectPattern[];

const GRADE_COLOR: Record<string, "green" | "yellow" | "orange" | "red" | "gray"> = {
  A: "green",
  B: "yellow",
  C: "orange",
  reject: "red",
};

function gradeColor(grade: string) {
  return GRADE_COLOR[grade] ?? "gray";
}

const STATUS_FILTER_OPTIONS = [
  { value: "", label: "All rolls" },
  { value: "pending_qc", label: "Pending Inspection" },
  { value: "rework", label: "In Rework" },
  { value: "passed", label: "Passed" },
  { value: "rejected", label: "Rejected" },
];

export default function QualityPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const canInspect = can(user?.role, "quality:write");

  const [statusFilter, setStatusFilter] = useState("");
  const [inspectRollId, setInspectRollId] = useState<string | null>(null);
  const [decision, setDecision] = useState("pass");
  const [measuredLength, setMeasuredLength] = useState("");
  const [notes, setNotes] = useState("");
  const [formError, setFormError] = useState("");

  const rollsUrl = statusFilter
    ? `/rolls?status=${statusFilter}&page=1&size=50`
    : "/rolls?page=1&size=50";

  const { data: queues, isLoading: queuesLoading } = useQuery({
    queryKey: qk.quality.queues(),
    queryFn: () => api.get<QueueData>("/quality/queues"),
  });

  const { data: rolls, isLoading: rollsLoading } = useQuery({
    queryKey: [...qk.quality.rolls(), statusFilter],
    queryFn: () => api.get<RollsResponse>(rollsUrl),
  });

  const { data: defects } = useQuery({
    queryKey: qk.quality.defectPatterns(),
    queryFn: () => api.get<DefectPatternsResponse>("/quality/defect-patterns") as Promise<DefectPatternsResponse>,
  });

  const inspectMutation = useMutation({
    mutationFn: ({ rollId, body }: { rollId: string; body: { decision: string; measured_length_cm: number; notes?: string } }) =>
      api.post(`/rolls/${rollId}/inspections`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qk.quality.queues() });
      queryClient.invalidateQueries({ queryKey: [...qk.quality.rolls(), statusFilter] });
      setInspectRollId(null);
      setDecision("pass");
      setMeasuredLength("");
      setNotes("");
      setFormError("");
    },
    onError: (err: Error) => setFormError(err.message || "Inspection failed"),
  });

  function openInspect(rollId: string, lengthCm: number) {
    setInspectRollId(inspectRollId === rollId ? null : rollId);
    setDecision("pass");
    setMeasuredLength((lengthCm / 100).toFixed(2));
    setNotes("");
    setFormError("");
  }

  function handleSubmit(rollId: string) {
    setFormError("");
    if (!measuredLength) { setFormError("Measured length is required."); return; }
    const cm = Math.round(parseFloat(measuredLength) * 100);
    if (isNaN(cm) || cm <= 0) { setFormError("Enter a valid length in metres."); return; }
    inspectMutation.mutate({ rollId, body: { decision, measured_length_cm: cm, notes: notes || undefined } });
  }

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="Quality Control" />

      {/* KPI tiles */}
      {queuesLoading ? (
        <Skeleton rows={2} className="max-w-sm" />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiTile label="Pending Inspection" value={queues?.pending_qc?.count ?? "-"} />
          <KpiTile label="In Rework" value={queues?.rework?.count ?? "-"} />
          <KpiTile
            label="Passed"
            value={queues?.passed?.count ?? "-"}
            trend={queues?.passed?.count ? "up" : "neutral"}
          />
          <KpiTile
            label="Rejected"
            value={queues?.rejected?.count ?? "-"}
            trend={queues?.rejected?.count ? "down" : "neutral"}
          />
        </div>
      )}

      {/* Defect patterns summary */}
      {defects && Array.isArray(defects) && defects.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Top Defect Patterns</h3>
          <div className="flex flex-wrap gap-3">
            {defects.map((p) => (
              <div key={p.ref_id} className="flex items-center gap-2 text-sm text-gray-600">
                <span className="font-medium">{p.ref_label}</span>
                <Badge color="gray">{p.defect_count} ({(p.rate * 100).toFixed(1)}%)</Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rolls table */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        {/* Filter bar */}
        <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-3">
          <span className="text-sm font-medium text-gray-700">Filter:</span>
          <div className="flex gap-2 flex-wrap">
            {STATUS_FILTER_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setStatusFilter(opt.value)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  statusFilter === opt.value
                    ? "bg-brand-600 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {rollsLoading ? (
          <div className="p-5"><Skeleton rows={6} /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Roll Code</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Order</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Grade</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Length</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Inspected</th>
                  {canInspect && <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {(!rolls?.items || rolls.items.length === 0) && (
                  <tr>
                    <td colSpan={canInspect ? 7 : 6} className="px-4 py-8 text-center text-gray-400">
                      No rolls found
                    </td>
                  </tr>
                )}
                {rolls?.items.map((roll) => {
                  const isInspecting = inspectRollId === roll.id;
                  const needsInspection = roll.status === "pending_qc" || roll.status === "rework";
                  return (
                    <Fragment key={roll.id}>
                      <tr className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">
                          <Link to={`/app/rolls/${roll.id}`} className="text-brand-600 hover:underline font-medium">
                            {roll.code}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700">{roll.order_code}</td>
                        <td className="px-4 py-3 text-sm">
                          {roll.grade
                            ? <Badge color={gradeColor(roll.grade)}>{roll.grade}</Badge>
                            : <span className="text-gray-400">—</span>}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700">{formatCm(roll.length_cm)}</td>
                        <td className="px-4 py-3 text-sm">
                          <Badge color={needsInspection ? "yellow" : roll.status === "passed" ? "green" : roll.status === "rejected" ? "red" : "gray"}>
                            {roll.status.replace(/_/g, " ")}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {roll.inspected_at ? formatDate(roll.inspected_at) : "—"}
                        </td>
                        {canInspect && (
                          <td className="px-4 py-3 text-sm">
                            {needsInspection ? (
                              <button
                                onClick={() => openInspect(roll.id, roll.length_cm)}
                                className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                                  isInspecting
                                    ? "bg-gray-200 text-gray-700"
                                    : "bg-brand-600 text-white hover:bg-brand-700"
                                }`}
                              >
                                {isInspecting ? "Cancel" : "Inspect ▾"}
                              </button>
                            ) : (
                              <span className="text-gray-400 text-xs">—</span>
                            )}
                          </td>
                        )}
                      </tr>

                      {/* Inline inspection form */}
                      {isInspecting && (
                        <tr key={`${roll.id}-inspect`}>
                          <td colSpan={canInspect ? 7 : 6} className="bg-blue-50 px-4 py-4 border-b border-blue-100">
                            <div className="text-sm font-semibold text-blue-800 mb-3">
                              Record Inspection — {roll.code}
                            </div>
                            {formError && (
                              <div className="mb-3 rounded-md bg-red-50 border border-red-200 px-3 py-2 text-xs text-red-700">
                                {formError}
                              </div>
                            )}
                            <div className="flex flex-wrap items-end gap-3">
                              <div>
                                <label htmlFor="inspect-decision" className="block text-xs font-medium text-gray-700 mb-1">Decision *</label>
                                <select
                                  id="inspect-decision"
                                  value={decision}
                                  onChange={(e) => setDecision(e.target.value)}
                                  className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-500"
                                >
                                  <option value="pass">✓ Pass</option>
                                  <option value="rework">↩ Rework</option>
                                  <option value="reject">✕ Reject</option>
                                </select>
                              </div>
                              <div>
                                <label htmlFor="inspect-length" className="block text-xs font-medium text-gray-700 mb-1">Measured Length (m) *</label>
                                <input
                                  id="inspect-length"
                                  type="number"
                                  step="0.01"
                                  min="0.01"
                                  value={measuredLength}
                                  onChange={(e) => setMeasuredLength(e.target.value)}
                                  className="w-32 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-500"
                                />
                              </div>
                              <div className="flex-1 min-w-[160px]">
                                <label htmlFor="inspect-notes" className="block text-xs font-medium text-gray-700 mb-1">Notes (optional)</label>
                                <input
                                  id="inspect-notes"
                                  type="text"
                                  value={notes}
                                  onChange={(e) => setNotes(e.target.value)}
                                  placeholder="Defect remarks…"
                                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-500"
                                />
                              </div>
                              <button
                                disabled={inspectMutation.isPending}
                                onClick={() => handleSubmit(roll.id)}
                                className={`rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors disabled:opacity-50 ${
                                  decision === "pass" ? "bg-green-600 hover:bg-green-700"
                                  : decision === "rework" ? "bg-yellow-600 hover:bg-yellow-700"
                                  : "bg-red-600 hover:bg-red-700"
                                }`}
                              >
                                {inspectMutation.isPending ? "Saving…" : "Submit"}
                              </button>
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
        )}
        {rolls && (
          <div className="px-4 py-3 border-t border-gray-200 text-xs text-gray-500">
            Showing {rolls.items.length} of {rolls.total} rolls
          </div>
        )}
      </div>
    </div>
  );
}
