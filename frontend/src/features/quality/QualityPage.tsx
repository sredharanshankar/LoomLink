import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
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

export default function QualityPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const canInspect = can(user?.role, "quality:write");

  const { data: queues, isLoading: queuesLoading } = useQuery({
    queryKey: qk.quality.queues(),
    queryFn: () => api.get<QueueData>("/quality/queues"),
  });

  const { data: rolls, isLoading: rollsLoading } = useQuery({
    queryKey: qk.quality.rolls(),
    queryFn: () => api.get<RollsResponse>("/rolls?page=1&size=50"),
  });

  const { data: defects } = useQuery({
    queryKey: qk.quality.defectPatterns(),
    queryFn: () => api.get<DefectPatternsResponse>("/quality/defect-patterns") as Promise<DefectPatternsResponse>,
  });

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
      {rollsLoading ? (
        <Skeleton rows={6} />
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Roll Code</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Order</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Grade</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Length</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Inspected</th>
                  {canInspect && <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Action</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {rolls?.items.length === 0 && (
                  <tr>
                    <td colSpan={canInspect ? 7 : 6} className="px-4 py-8 text-center text-gray-400">
                      No rolls found
                    </td>
                  </tr>
                )}
                {rolls?.items.map((roll) => (
                  <tr key={roll.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="px-4 py-3 text-sm">
                      <Link to={`/app/rolls/${roll.id}`} className="text-blue-600 hover:underline font-medium">
                        {roll.code}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{roll.order_code}</td>
                    <td className="px-4 py-3 text-sm">
                      {roll.grade
                        ? <Badge color={gradeColor(roll.grade)}>{roll.grade}</Badge>
                        : <span className="text-gray-400">—</span>}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{formatCm(roll.length_cm)}</td>
                    <td className="px-4 py-3 text-sm">
                      <Badge color={roll.status === "pending_qc" || roll.status === "rework" ? "yellow" : roll.status === "passed" ? "green" : roll.status === "rejected" ? "red" : "gray"}>
                        {roll.status.replace(/_/g, " ")}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                      {roll.inspected_at ? formatDate(roll.inspected_at) : "—"}
                    </td>
                    {canInspect && (
                      <td className="px-4 py-3 text-sm">
                        {(roll.status === "pending_qc" || roll.status === "rework") ? (
                          <button
                            onClick={() => navigate(`/app/rolls/${roll.id}`)}
                            className="inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                          >
                            Inspect →
                          </button>
                        ) : (
                          <span className="text-gray-400 text-xs">—</span>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {rolls && (
            <div className="px-4 py-3 border-t border-gray-200 text-xs text-gray-500">
              Showing {rolls.items.length} of {rolls.total} rolls
            </div>
          )}
        </div>
      )}
    </div>
  );
}
