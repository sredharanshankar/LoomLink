import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatCm, formatDateTime } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";

interface Defect {
  type: string;
  position_cm: number;
  severity: string;
}

interface Roll {
  id: string;
  code: string;
  order_code: string;
  length_cm: number;
  status: string;
  grade: string;
  defects: Defect[];
  inspected_at: string | null;
  inspected_by: string | null;
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

  const { data: roll, isLoading, isError } = useQuery<Roll>({
    queryKey: ["roll", id],
    queryFn: () => api.get(`/rolls/${id}`),
    enabled: !!id,
  });

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
            <dd className="text-sm font-medium text-gray-900">{roll.order_code}</dd>
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
          <div>
            <dt className="text-sm text-gray-500">Grade</dt>
            <dd className="text-sm">
              <Badge color={GRADE_COLORS[roll.grade] ?? "gray"}>{roll.grade}</Badge>
            </dd>
          </div>
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

      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Defects</h2>
        {roll.defects.length === 0 ? (
          <div className="bg-green-50 text-green-700 rounded-lg border border-green-200 p-4">
            No defects found.
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Position</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Severity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {roll.defects.map((defect, i) => (
                  <tr key={i}>
                    <td className="px-4 py-3 text-sm text-gray-700">{defect.type}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{formatCm(defect.position_cm)}</td>
                    <td className="px-4 py-3 text-sm">
                      <Badge color={defect.severity === "major" ? "red" : defect.severity === "minor" ? "yellow" : "gray"}>
                        {formatStatus(defect.severity)}
                      </Badge>
                    </td>
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
