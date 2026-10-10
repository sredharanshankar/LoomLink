import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";

interface Supplier {
  id: string;
  code: string;
  name: string;
  contact_person: string;
  phone: string;
  yarn_types_supplied: string[];
}

interface SuppliersResponse {
  items: Supplier[];
}

export default function SuppliersPage() {
  const { data, isLoading, error } = useQuery<SuppliersResponse>({
    queryKey: ["suppliers"],
    queryFn: () => api.get("/suppliers"),
  });

  const suppliers = data?.items ?? [];

  return (
    <div className="p-6">
      <PageHeader title="Suppliers" />

      {isLoading && <Skeleton rows={6} />}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          Failed to load suppliers.
        </div>
      )}

      {!isLoading && !error && suppliers.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-400">
          No suppliers found.
        </div>
      )}

      {!isLoading && suppliers.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Code</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Contact</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Phone</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Yarn Types</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {suppliers.map((s) => (
                  <tr key={s.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{s.code}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{s.name}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{s.contact_person}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{s.phone}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{s.yarn_types_supplied.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
