import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import PageHeader from "../../../components/ui/PageHeader";

interface ReceiptPayload {
  yarn_type_code: string;
  supplier_code: string;
  qty_g: number;
  rate_paise: number;
}

export default function WorkerReceivePage() {
  const [yarnType, setYarnType] = useState("");
  const [supplier, setSupplier] = useState("");
  const [qtyKg, setQtyKg] = useState("");
  const [ratePerKg, setRatePerKg] = useState("");
  const [success, setSuccess] = useState(false);

  const mutation = useMutation({
    mutationFn: (payload: ReceiptPayload) => api.post("/inventory/receipts", payload),
    onSuccess: () => {
      setSuccess(true);
      setYarnType("");
      setSupplier("");
      setQtyKg("");
      setRatePerKg("");
      setTimeout(() => setSuccess(false), 3000);
    },
  });

  const canSubmit = yarnType && supplier && qtyKg && ratePerKg && !mutation.isPending;

  function handleSubmit() {
    const qtyG = Math.round(parseFloat(qtyKg) * 1000);
    const ratePaise = Math.round(parseFloat(ratePerKg) * 100);
    mutation.mutate({ yarn_type_code: yarnType, supplier_code: supplier, qty_g: qtyG, rate_paise: ratePaise });
  }

  return (
    <div className="p-4 space-y-4">
      <PageHeader title="Receive Yarn" />

      <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Yarn Type Code</label>
          <input
            type="text"
            className="w-full border border-gray-300 rounded-lg px-4 py-3 text-lg"
            placeholder="e.g. COTTON-40S"
            value={yarnType}
            onChange={(e) => setYarnType(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Supplier Code</label>
          <input
            type="text"
            className="w-full border border-gray-300 rounded-lg px-4 py-3 text-lg"
            placeholder="e.g. SUP-001"
            value={supplier}
            onChange={(e) => setSupplier(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Quantity (kg)</label>
          <input
            type="number"
            inputMode="decimal"
            className="w-full border border-gray-300 rounded-lg px-4 py-3 text-lg"
            placeholder="0.00"
            value={qtyKg}
            onChange={(e) => setQtyKg(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Rate per kg (₹)</label>
          <input
            type="number"
            inputMode="decimal"
            className="w-full border border-gray-300 rounded-lg px-4 py-3 text-lg"
            placeholder="0.00"
            value={ratePerKg}
            onChange={(e) => setRatePerKg(e.target.value)}
          />
        </div>
      </div>

      <button
        className="w-full bg-blue-600 text-white rounded-lg py-4 text-lg font-semibold active:bg-blue-700 disabled:opacity-50"
        disabled={!canSubmit}
        onClick={handleSubmit}
      >
        {mutation.isPending ? "Submitting..." : "Receive Yarn"}
      </button>

      {success && (
        <p className="text-green-600 text-sm text-center font-medium">Yarn received successfully</p>
      )}
      {mutation.isError && (
        <p className="text-red-600 text-sm text-center">Failed to submit receipt</p>
      )}
    </div>
  );
}
