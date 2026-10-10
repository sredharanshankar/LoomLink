import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import { formatGrams, formatDateTime } from "../../../lib/format";
import PageHeader from "../../../components/ui/PageHeader";
import Skeleton from "../../../components/ui/Skeleton";

interface Batch {
  code: string;
  yarn_type_code: string;
  supplier_name: string;
  qty_on_hand_g: number;
  received_at: string;
}

export default function WorkerBatchPage() {
  const { id } = useParams<{ id: string }>();

  const { data: batch, isLoading } = useQuery({
    queryKey: ["batch", id],
    queryFn: () => api.get<Batch>(`/inventory/batches/${id}`),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-4"><Skeleton rows={4} /></div>;
  if (!batch) return <div className="p-4 text-center text-gray-500">Batch not found</div>;

  return (
    <div className="p-4 space-y-4">
      <PageHeader title={batch.code} subtitle="Yarn Batch" />

      <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Yarn Type</span>
          <span className="text-sm font-medium">{batch.yarn_type_code}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Supplier</span>
          <span className="text-sm font-medium">{batch.supplier_name}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">On Hand</span>
          <span className="text-sm font-medium">{formatGrams(batch.qty_on_hand_g)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Received</span>
          <span className="text-sm font-medium">{formatDateTime(batch.received_at)}</span>
        </div>
      </div>
    </div>
  );
}
