import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import Card from "../../components/ui/Card";
import Spinner from "../../components/ui/Spinner";

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
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <div className="mb-4">
          <h1 className="text-2xl font-bold text-brand-900">LoomLink</h1>
          <p className="text-sm text-gray-500">Order Tracking</p>
        </div>
        {isLoading && <Spinner className="mx-auto" />}
        {error && <p className="text-red-600 text-sm">Unable to load order status.</p>}
        {data && (
          <div className="space-y-3">
            <div><p className="text-xs text-gray-500 uppercase tracking-wide">Order</p><p className="font-semibold text-gray-900">{data.order_number}</p></div>
            <div><p className="text-xs text-gray-500 uppercase tracking-wide">Fabric</p><p className="text-gray-700">{data.fabric_type}</p></div>
            <div><p className="text-xs text-gray-500 uppercase tracking-wide">Status</p><p className="text-gray-700 capitalize">{data.status.replace(/_/g, " ")}</p></div>
          </div>
        )}
      </Card>
    </div>
  );
}