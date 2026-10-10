import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";

interface FabricType {
  id: string;
  code: string;
  name: string;
  colour: string | null;
  width_cm: number | null;
}

export default function BuyerOrderFormPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: fabrics, isLoading } = useQuery<{ items: FabricType[] }>({
    queryKey: ["buyer-portal-fabric-types"],
    queryFn: () => api.get("/buyer/portal/fabric-types"),
  });

  const [fabricTypeId, setFabricTypeId] = useState("");
  const [quantityM, setQuantityM] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post("/buyer/portal/orders", body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["buyer-portal-orders"] });
      navigate("/app/buyer-portal");
    },
    onError: (err: Error) => {
      const msg = err.message || "";
      if (msg.toLowerCase().includes("no buyer profile")) {
        setError(
          "Your account is not linked to a buyer profile yet. " +
          "Please ask your administrator to open Settings → Users, find your account, and click "Link Buyer"."
        );
      } else {
        setError(msg || "Failed to place order. Please try again.");
      }
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!fabricTypeId || !quantityM || !dueDate) {
      setError("Please fill all required fields.");
      return;
    }
    const qty = parseFloat(quantityM);
    if (isNaN(qty) || qty <= 0) {
      setError("Quantity must be a positive number.");
      return;
    }
    const due = new Date(dueDate);
    if (due <= new Date()) {
      setError("Due date must be in the future.");
      return;
    }
    mutation.mutate({
      fabric_type_id: fabricTypeId,
      quantity_cm: Math.round(qty * 100),
      due_date: dueDate,
      priority: "normal",
      notes,
    });
  }

  if (isLoading) return <div className="p-6"><Skeleton rows={6} /></div>;

  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <PageHeader title="Place New Order" subtitle="Submit a fabric order request" />

      <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 space-y-5">
        {error && (
          <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Fabric Type <span className="text-red-500">*</span></label>
          <select
            value={fabricTypeId}
            onChange={(e) => setFabricTypeId(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select a fabric type</option>
            {fabrics?.items.map((f) => (
              <option key={f.id} value={f.id}>
                {f.code} — {f.name}{f.colour ? ` (${f.colour})` : ""}{f.width_cm ? `, ${f.width_cm}cm wide` : ""}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Quantity (metres) <span className="text-red-500">*</span></label>
          <input
            type="number"
            step="0.01"
            min="1"
            value={quantityM}
            onChange={(e) => setQuantityM(e.target.value)}
            placeholder="e.g. 500"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Required By (Due Date) <span className="text-red-500">*</span></label>
          <input
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            min={new Date(Date.now() + 86_400_000).toISOString().slice(0, 10)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Notes / Special Requirements</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            placeholder="Any special finishing requirements, colour specifications, etc."
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="inline-flex items-center justify-center rounded-md font-medium h-10 px-6 text-sm bg-blue-600 text-white hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {mutation.isPending ? "Placing Order…" : "Place Order"}
          </button>
          <button
            type="button"
            onClick={() => navigate("/app/buyer-portal")}
            className="inline-flex items-center justify-center rounded-md font-medium h-10 px-5 text-sm border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
        </div>

        <p className="text-xs text-gray-400">
          After submitting, your order will be reviewed and confirmed by our team.
          You can track its progress from your portal.
        </p>
      </form>
    </div>
  );
}
