import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import { useAuth } from "../../lib/auth";
import { can } from "../../lib/permissions";

interface Buyer { id: string; code: string; name: string }
interface FabricType { id: string; code: string; name: string; default_price_paise_per_m: number }

export default function NewOrderPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    if (user && !can(user.role, "orders:write")) {
      navigate("/app/orders", { replace: true });
    }
  }, [user, navigate]);
  const queryClient = useQueryClient();
  const { data: buyers, isLoading: bLoad } = useQuery({ queryKey: ["buyers"], queryFn: () => api.get<{ items: Buyer[] }>("/buyers") });
  const { data: fabrics, isLoading: fLoad } = useQuery({ queryKey: ["fabric-types"], queryFn: () => api.get<{ items: FabricType[] }>("/fabric-types") });

  const [buyerId, setBuyerId] = useState("");
  const [fabricTypeId, setFabricTypeId] = useState("");
  const [quantityM, setQuantityM] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [pricePaisePerM, setPricePaisePerM] = useState("");
  const [priority, setPriority] = useState("normal");
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post<{ id: string }>("/orders", body),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      navigate(`/app/orders/${data.id}`);
    },
    onError: (err: Error) => setError(err.message || "Failed to create order"),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!buyerId || !fabricTypeId || !quantityM || !dueDate) { setError("Please fill all required fields."); return; }
    const fab = fabrics?.items.find((f) => f.id === fabricTypeId);
    mutation.mutate({
      buyer_id: buyerId,
      fabric_type_id: fabricTypeId,
      quantity_cm: Math.round(parseFloat(quantityM) * 100),
      due_date: dueDate,
      price_paise_per_m: pricePaisePerM ? parseInt(pricePaisePerM, 10) : fab?.default_price_paise_per_m ?? 0,
      priority,
    });
  }

  if (bLoad || fLoad) return <div className="p-6"><Skeleton rows={6} /></div>;

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="New Order" subtitle="Create a buyer order" />
      <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 max-w-lg space-y-4">
        {error && <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Buyer *</label>
          <select value={buyerId} onChange={(e) => setBuyerId(e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select buyer</option>
            {buyers?.items.map((b) => <option key={b.id} value={b.id}>{b.code} — {b.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Fabric Type *</label>
          <select value={fabricTypeId} onChange={(e) => setFabricTypeId(e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Select fabric</option>
            {fabrics?.items.map((f) => <option key={f.id} value={f.id}>{f.code} — {f.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Quantity (metres) *</label>
          <input type="number" step="0.01" min="0.01" value={quantityM} onChange={(e) => setQuantityM(e.target.value)} placeholder="e.g. 1200" className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Due Date *</label>
          <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Price (paise/m)</label>
          <input type="number" min="0" value={pricePaisePerM} onChange={(e) => setPricePaisePerM(e.target.value)} placeholder="Leave blank for default" className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
          <select value={priority} onChange={(e) => setPriority(e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="normal">Normal</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
        </div>
        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={mutation.isPending} className="inline-flex items-center justify-center rounded-md font-medium h-10 px-5 text-sm bg-blue-700 text-white hover:bg-blue-800 transition-colors disabled:opacity-50">
            {mutation.isPending ? "Creating…" : "Create Order"}
          </button>
          <button type="button" onClick={() => navigate("/app/orders")} className="inline-flex items-center justify-center rounded-md font-medium h-10 px-5 text-sm border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors">Cancel</button>
        </div>
      </form>
    </div>
  );
}
