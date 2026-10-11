import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";

interface YarnType {
  id: string;
  code: string;
  material: string;
  count_label: string;
  colour: string;
  standard_rate_paise_per_kg: number;
}

interface Supplier {
  id: string;
  code: string;
  name: string;
}

export default function ReceiveYarnPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: yarnTypes, isLoading: ytLoading } = useQuery({
    queryKey: ["yarn-types"],
    queryFn: () => api.get<{ items: YarnType[] }>("/yarn-types"),
  });

  const { data: suppliers, isLoading: supLoading } = useQuery({
    queryKey: ["suppliers"],
    queryFn: () => api.get<{ items: Supplier[] }>("/suppliers"),
  });

  const [yarnTypeId, setYarnTypeId] = useState("");
  const [supplierId, setSupplierId] = useState("");
  const [qtyKg, setQtyKg] = useState("");
  const [ratePaisePerKg, setRatePaisePerKg] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const mutation = useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      api.post("/inventory/receipts", body),
    onSuccess: () => {
      setSuccess("Yarn received successfully!");
      setError("");
      queryClient.invalidateQueries({ queryKey: ["inventory-stock"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-alerts"] });
      setTimeout(() => navigate("/app/inventory"), 1500);
    },
    onError: (err: Error) => {
      setError(err.message || "Failed to receive yarn");
      setSuccess("");
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!yarnTypeId || !supplierId || !qtyKg) {
      setError("Please fill all required fields.");
      return;
    }

    const qtyG = Math.round(parseFloat(qtyKg) * 1000);
    const rate = ratePaisePerKg
      ? parseInt(ratePaisePerKg, 10)
      : yarnTypes?.items.find((y) => y.id === yarnTypeId)?.standard_rate_paise_per_kg ?? 0;

    mutation.mutate({
      yarn_type_id: yarnTypeId,
      supplier_id: supplierId,
      received_g: qtyG,
      rate_paise_per_kg: rate,
    });
  }

  const isLoading = ytLoading || supLoading;

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="Receive Yarn" subtitle="Record incoming yarn stock" />

      {isLoading ? (
        <Skeleton rows={5} className="max-w-md" />
      ) : (
        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 max-w-lg space-y-4"
        >
          {error && (
            <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              {error}
            </div>
          )}
          {success && (
            <div className="rounded-md bg-green-50 border border-green-200 p-3 text-sm text-green-700">
              {success}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Yarn Type *
            </label>
            <select
              value={yarnTypeId}
              onChange={(e) => setYarnTypeId(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select yarn type</option>
              {yarnTypes?.items.map((y) => (
                <option key={y.id} value={y.id}>
                  {y.code} — {y.material} {y.count_label} ({y.colour})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Supplier *
            </label>
            <select
              value={supplierId}
              onChange={(e) => setSupplierId(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select supplier</option>
              {suppliers?.items.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.code} — {s.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Quantity (kg) *
            </label>
            <input
              type="number"
              step="0.1"
              min="0.1"
              value={qtyKg}
              onChange={(e) => setQtyKg(e.target.value)}
              placeholder="e.g. 120"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Rate (paise/kg)
            </label>
            <input
              type="number"
              min="0"
              value={ratePaisePerKg}
              onChange={(e) => setRatePaisePerKg(e.target.value)}
              placeholder="Leave blank for standard rate"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-400">Leave blank to use the yarn type&apos;s standard rate.</p>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={mutation.isPending}
              className="inline-flex items-center justify-center rounded-md font-medium h-10 px-5 text-sm bg-blue-700 text-white hover:bg-blue-800 transition-colors disabled:opacity-50"
            >
              {mutation.isPending ? "Receiving…" : "Receive Yarn"}
            </button>
            <button
              type="button"
              onClick={() => navigate("/app/inventory")}
              className="inline-flex items-center justify-center rounded-md font-medium h-10 px-5 text-sm border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
