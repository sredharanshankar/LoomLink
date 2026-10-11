import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import { formatDateTime } from "../../../lib/format";
import PageHeader from "../../../components/ui/PageHeader";
import Badge from "../../../components/ui/Badge";
import Skeleton from "../../../components/ui/Skeleton";
import ScanButton from "../../../components/ui/ScanButton";

interface ScannedItem {
  roll_code: string;
  scanned_at: string;
}

interface Dispatch {
  id: string;
  code: string;
  order_code: string;
  status: string;
  buyer_name: string;
  planned_rolls: number;
  scanned_items: ScannedItem[];
}

export default function WorkerDispatchPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [rollCode, setRollCode] = useState("");

  const { data: dispatch, isLoading } = useQuery({
    queryKey: ["dispatch", id],
    queryFn: () => api.get<Dispatch>(`/dispatches/${id}`),
    enabled: !!id,
  });

  const scanMutation = useMutation({
    mutationFn: (code: string) => api.post(`/dispatches/${id}/scan`, { roll_code: code }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dispatch", id] });
      setRollCode("");
    },
  });

  if (isLoading) return <div className="p-4"><Skeleton rows={5} /></div>;
  if (!dispatch) return <div className="p-4 text-center text-gray-500">Dispatch not found</div>;

  const scannedCount = dispatch.scanned_items?.length ?? 0;

  return (
    <div className="p-4 space-y-4">
      <PageHeader title={dispatch.code} subtitle={`Order ${dispatch.order_code}`} />

      <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">Status</span>
          <Badge color={dispatch.status === "completed" ? "green" : "blue"}>{dispatch.status}</Badge>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Buyer</span>
          <span className="text-sm font-medium">{dispatch.buyer_name}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Scanned</span>
          <span className="text-sm font-medium">{scannedCount} / {dispatch.planned_rolls}</span>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <label className="block text-sm font-medium text-gray-700">Scan Roll Code</label>
        <ScanButton
          label="Scan Roll QR"
          className="w-full justify-center"
          onScan={(code) => {
            setRollCode(code);
            scanMutation.mutate(code);
          }}
        />
        <div className="flex gap-2">
          <input
            type="text"
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm"
            placeholder="Or enter roll code manually"
            value={rollCode}
            onChange={(e) => setRollCode(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && rollCode && scanMutation.mutate(rollCode)}
          />
          <button
            className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium active:bg-brand-700 disabled:opacity-50"
            disabled={!rollCode || scanMutation.isPending}
            onClick={() => scanMutation.mutate(rollCode)}
          >
            Go
          </button>
        </div>
        {scanMutation.isError && (
          <p className="text-red-600 text-sm text-center">
            {(scanMutation.error as Error)?.message?.includes("400")
              ? "Roll blocked — wrong buyer, unpassed, or already dispatched"
              : "Scan failed — try again"}
          </p>
        )}
      </div>

      {scannedCount > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-2">
          <h2 className="text-sm font-semibold text-gray-700 mb-2">Scanned Items</h2>
          {dispatch.scanned_items.map((item, i) => (
            <div key={i} className="flex justify-between items-center border-b border-gray-100 pb-2 last:border-0 last:pb-0">
              <span className="text-sm font-medium">{item.roll_code}</span>
              <span className="text-xs text-gray-400">{formatDateTime(item.scanned_at)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
