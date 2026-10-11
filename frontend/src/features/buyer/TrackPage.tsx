import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import Card from "../../components/ui/Card";
import Spinner from "../../components/ui/Spinner";
import StatusPill from "../../components/ui/StatusPill";

interface TrackData {
  order_number: string;
  status: string;
  fabric_type: string;
  quantity_m: number;
  updated_at: string;
}

export default function TrackPage() {
  const { tracking_token } = useParams<{ tracking_token: string }>();
  const { data, isLoading, error } = useQuery({
    queryKey: ["track", tracking_token],
    queryFn: () => api.get<TrackData>("/orders/track/" + tracking_token),
    enabled: !!tracking_token,
  });

  return (
    <Card title="Order tracking" description="Live status from the mill floor">
      {isLoading && <Spinner className="mx-auto" />}
      {error && <p className="text-sm text-red-600">Unable to load order status.</p>}
      {data && (
        <dl className="space-y-4">
          <div>
            <dt className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">Order</dt>
            <dd className="mt-0.5 font-semibold text-gray-900">{data.order_number}</dd>
          </div>
          <div>
            <dt className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">Fabric</dt>
            <dd className="mt-0.5 text-gray-700">{data.fabric_type}</dd>
          </div>
          <div>
            <dt className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">Status</dt>
            <dd className="mt-1"><StatusPill status={data.status} /></dd>
          </div>
        </dl>
      )}
    </Card>
  );
}