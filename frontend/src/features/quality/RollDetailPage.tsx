import { useParams } from "react-router-dom";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatCm, formatDateTime } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";
import { useAuth } from "../../lib/auth";
import { can } from "../../lib/permissions";

interface Inspection {
  id: string;
  decision: string;
  measured_length_cm: number | null;
  notes: string | null;
  created_at: string;
  inspector_id: string | null;
}

interface Roll {
  id: string;
  code: string;
  order_id: string;
  order_code?: string;
  length_cm: number;
  status: string;
  grade?: string;
  defects?: unknown[];
  inspections?: Inspection[];
  inspected_at?: string | null;
  inspected_by?: string | null;
}

interface InspectBody {
  decision: string;
  measured_length_cm: number;
  notes?: string;
}

const GRADE_COLORS: Record<string, "green" | "yellow" | "red" | "gray"> = {
  A: "green",
  B: "yellow",
  C: "red",
};

function formatStatus(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function RollDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [decision, setDecision] = useState("pass");
  const [measuredLength, setMeasuredLength] = useState("");
  const [notes, setNotes] = useState("");
  const [formError, setFormError] = useState("");

  const { data: roll, isLoading, isError } = useQuery<Roll>({
    queryKey: ["roll", id],
    queryFn: () => api.get(`/rolls/${id}`),
    enabled: !!id,
  });

  const inspectMutation = useMutation({
    mutationFn: (body: InspectBody) => api.post(`/rolls/${id}/inspections`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roll", id] });
      setMeasuredLength("");
      setNotes("");
      setFormError("");
    },
    onError: (err: Error) => setFormError(err.message || "Inspection failed"),
  });

  function handleInspect(e: React.FormEvent) {
    e.preventDefault();
    setFormError("");
    if (!measuredLength) { setFormError("Measured length is required."); return; }
    const cm = Math.round(parseFloat(measuredLength) * 100);
    if (isNaN(cm) || cm <= 0) { setFormError("Enter a valid length in metres."); return; }
    inspectMutation.mutate({ decision, measured_length_cm: cm, notes: notes || undefined });
  }

  if (isLoading) return <div className="p-6"><Skeleton rows={6} /></div>;

  if (isError || !roll) {
    return (
      <div className="p-6">
        <div className="bg-red-50 text-red-700 rounded-lg border border-red-200 p-4">
          Failed to load roll details.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <PageHeader title="Roll" subtitle={roll.code} />

      <div className="bg-white rounded-lg border border-gray-200 p-5 mb-6">
        <dl className="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-4">
          <div>
            <dt className="text-sm text-gray-500">Order</dt>
            <dd className="text-sm font-medium text-gray-900">{roll.order_code ?? roll.order_id}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Length</dt>
            <dd className="text-sm font-medium text-gray-900">{formatCm(roll.length_cm)}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Status</dt>
            <dd className="text-sm">
              <Badge color="gray">{formatStatus(roll.status)}</Badge>
            </dd>
          </div>
          {roll.grade && (
            <div>
              <dt className="text-sm text-gray-500">Grade</dt>
              <dd className="text-sm">
                <Badge color={GRADE_COLORS[roll.grade] ?? "gray"}>{roll.grade}</Badge>
              </dd>
            </div>
          )}
          {roll.inspected_at && (
            <div>
              <dt className="text-sm text-gray-500">Inspected At</dt>
              <dd className="text-sm font-medium text-gray-900">{formatDateTime(roll.inspected_at)}</dd>
            </div>
          )}
          {roll.inspected_by && (
            <div>
              <dt className="text-sm text-gray-500">Inspected By</dt>
              <dd className="text-sm font-medium text-gray-900">{roll.inspected_by}</dd>
            </div>
          )}
        </dl>
      </div>

      {/* Inspection form — shown only when roll needs QC and user can inspect */}
      {(roll.status === "pending_qc" || roll.status === "rework") && can(user?.role, "quality:write") && (
        <div className="bg-blue-50 rounded-lg border border-blue-200 p-5 mb-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-4">Record Inspection</h2>
          <form onSubmit={handleInspect} className="space-y-4">
            {formError && (
              <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">{formError}</div>
            )}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Decision *</label>
                <select
                  value={decision}
                  onChange={(e) => setDecision(e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="pass">Pass</option>
                  <option value="rework">Rework</option>
                  <option value="reject">Reject</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Measured Length (metres) *</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={measuredLength}
                  onChange={(e) => setMeasuredLength(e.target.value)}
                  placeholder={roll.length_cm ? `Expected ${(roll.length_cm / 100).toFixed(2)} m` : "e.g. 50.00"}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Optional remarks"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={inspectMutation.isPending}
              className="inline-flex items-center justify-center rounded-md font-medium h-10 px-5 text-sm bg-brand-700 text-white hover:bg-brand-800 transition-colors disabled:opacity-50"
            >
              {inspectMutation.isPending ? "Saving…" : "Submit Inspection"}
            </button>
          </form>
        </div>
      )}

      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Inspections</h2>
        {(roll.inspections ?? []).length === 0 ? (
          <div className="bg-green-50 text-green-700 rounded-lg border border-green-200 p-4">
            No inspections recorded yet.
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Decision</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Measured Length</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Notes</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {(roll.inspections ?? []).map((insp) => (
                  <tr key={insp.id}>
                    <td className="px-4 py-3 text-sm">
                      <Badge color={insp.decision === "pass" ? "green" : insp.decision === "rework" ? "yellow" : "red"}>
                        {formatStatus(insp.decision)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {insp.measured_length_cm != null ? formatCm(insp.measured_length_cm) : "—"}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">{insp.notes ?? "—"}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{formatDateTime(insp.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
