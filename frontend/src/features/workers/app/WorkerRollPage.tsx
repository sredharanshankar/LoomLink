import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import { formatCm } from "../../../lib/format";
import PageHeader from "../../../components/ui/PageHeader";
import Badge from "../../../components/ui/Badge";
import Skeleton from "../../../components/ui/Skeleton";

interface Roll {
  code: string;
  order_code: string;
  length_cm: number;
  status: string;
  grade: string;
}

const STATUS_COLOR: Record<string, "green" | "yellow" | "gray" | "red" | "blue"> = {
  ready: "green",
  inspecting: "yellow",
  dispatched: "blue",
  rejected: "red",
};

const GRADE_COLOR: Record<string, "green" | "yellow" | "red" | "gray"> = {
  A: "green",
  B: "yellow",
  C: "red",
};

export default function WorkerRollPage() {
  const { id } = useParams<{ id: string }>();

  const { data: roll, isLoading } = useQuery({
    queryKey: ["roll", id],
    queryFn: () => api.get<Roll>(`/rolls/${id}`),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-4"><Skeleton rows={4} /></div>;
  if (!roll) return <div className="p-4 text-center text-gray-500">Roll not found</div>;

  return (
    <div className="p-4 space-y-4">
      <PageHeader title={roll.code} subtitle={`Order ${roll.order_code}`} />

      <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">Status</span>
          <Badge color={STATUS_COLOR[roll.status] ?? "gray"}>{roll.status}</Badge>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">Grade</span>
          <Badge color={GRADE_COLOR[roll.grade] ?? "gray"}>{roll.grade}</Badge>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Length</span>
          <span className="text-sm font-medium">{formatCm(roll.length_cm)}</span>
        </div>
      </div>
    </div>
  );
}
