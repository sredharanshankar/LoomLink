import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatGrams, formatPaise, formatDateTime } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import KpiTile from "../../components/ui/KpiTile";
import Skeleton from "../../components/ui/Skeleton";

interface Batch {
  id: string;
  code: string;
  yarn_type_code: string;
  supplier_name: string;
  qty_received_g: number;
  qty_on_hand_g: number;
  rate_paise_per_kg: number;
  received_at: string;
}

export default function BatchDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: batch, isLoading, isError } = useQuery<Batch>({
    queryKey: ["batch", id],
    queryFn: () => api.get(`/inventory/batches/${id}`),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-6"><Skeleton rows={6} /></div>;

  if (isError || !batch) {
    return (
      <div className="p-6">
        <div className="bg-red-50 text-red-700 rounded-lg border border-red-200 p-4">
          Failed to load batch details.
        </div>
      </div>
    );
  }

  const usedG = batch.qty_received_g - batch.qty_on_hand_g;
  const usedPct = batch.qty_received_g > 0 ? Math.round((usedG / batch.qty_received_g) * 100) : 0;

  return (
    <div className="p-6">
      <PageHeader title="Yarn Batch" subtitle={batch.code} />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <KpiTile label="Received" value={formatGrams(batch.qty_received_g)} />
        <KpiTile label="On Hand" value={formatGrams(batch.qty_on_hand_g)} sub={`${usedPct}% used`} />
        <KpiTile label="Rate" value={formatPaise(batch.rate_paise_per_kg, { showPaise: true })} sub="per kg" />
        <KpiTile label="Received At" value={formatDateTime(batch.received_at)} />
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-5 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Details</h2>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
          <div>
            <dt className="text-sm text-gray-500">Yarn Type</dt>
            <dd className="text-sm font-medium text-gray-900">{batch.yarn_type_code}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Supplier</dt>
            <dd className="text-sm font-medium text-gray-900">{batch.supplier_name}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Quantity Received</dt>
            <dd className="text-sm font-medium text-gray-900">{formatGrams(batch.qty_received_g)}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Quantity On Hand</dt>
            <dd className="text-sm font-medium text-gray-900">{formatGrams(batch.qty_on_hand_g)}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
