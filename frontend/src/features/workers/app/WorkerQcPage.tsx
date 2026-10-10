import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import { formatCm } from "../../../lib/format";
import PageHeader from "../../../components/ui/PageHeader";
import Badge from "../../../components/ui/Badge";
import Skeleton from "../../../components/ui/Skeleton";

interface QcItem {
  roll_id: string;
  roll_code: string;
  order_code: string;
  length_cm: number;
}

interface QcQueue {
  pending: number;
  items: QcItem[];
}

type Verdict = "pass" | "rework" | "reject";

const VERDICT_COLOR: Record<Verdict, "green" | "yellow" | "red"> = {
  pass: "green",
  rework: "yellow",
  reject: "red",
};

export default function WorkerQcPage() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<QcItem | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["qc-queue"],
    queryFn: () => api.get<QcQueue>("/quality/queues"),
  });

  const verdictMutation = useMutation({
    mutationFn: ({ rollId, verdict }: { rollId: string; verdict: Verdict }) =>
      api.post(`/quality/inspections`, { roll_id: rollId, verdict }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["qc-queue"] });
      setSelected(null);
    },
  });

  if (isLoading) return <div className="p-4"><Skeleton rows={6} /></div>;

  if (selected) {
    return (
      <div className="p-4 space-y-4">
        <PageHeader title="Inspect Roll" subtitle={selected.roll_code} />
        <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-gray-500">Order</span>
            <span className="text-sm font-medium">{selected.order_code}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-500">Length</span>
            <span className="text-sm font-medium">{formatCm(selected.length_cm)}</span>
          </div>
        </div>

        <div className="space-y-3">
          {(["pass", "rework", "reject"] as Verdict[]).map((v) => (
            <button
              key={v}
              className={`w-full rounded-lg py-4 text-lg font-semibold text-white active:opacity-80 disabled:opacity-50 ${
                v === "pass" ? "bg-green-600" : v === "rework" ? "bg-yellow-500" : "bg-red-600"
              }`}
              disabled={verdictMutation.isPending}
              onClick={() => verdictMutation.mutate({ rollId: selected.roll_id, verdict: v })}
            >
              {verdictMutation.isPending ? "Saving..." : v.charAt(0).toUpperCase() + v.slice(1)}
            </button>
          ))}
        </div>

        {verdictMutation.isError && (
          <p className="text-red-600 text-sm text-center">Failed to submit verdict</p>
        )}

        <button
          className="w-full border border-gray-300 rounded-lg py-3 text-gray-600 font-medium"
          onClick={() => setSelected(null)}
        >
          Back to Queue
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <PageHeader title="QC Inspection" subtitle={`${data?.pending ?? 0} pending`} />

      {data?.items.length === 0 && (
        <p className="text-center text-sm text-gray-400 py-8">No rolls pending inspection</p>
      )}

      <div className="space-y-2">
        {data?.items.map((item) => (
          <button
            key={item.roll_id}
            className="w-full bg-white rounded-lg border border-gray-200 p-4 flex items-center justify-between active:bg-gray-50 text-left"
            onClick={() => setSelected(item)}
          >
            <div>
              <p className="font-medium text-sm">{item.roll_code}</p>
              <p className="text-xs text-gray-500">Order {item.order_code}</p>
            </div>
            <span className="text-sm text-gray-500">{formatCm(item.length_cm)}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
