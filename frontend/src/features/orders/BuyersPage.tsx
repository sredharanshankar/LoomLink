import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { formatPaise } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";

interface Buyer {
  id: string;
  code: string;
  name: string;
  contact_person: string;
  phone: string;
  email: string;
  outstanding_paise: number;
  orders_count: number;
}

interface BuyersResponse {
  items: Buyer[];
}

export default function BuyersPage() {
  const { data, isLoading, error } = useQuery<BuyersResponse>({
    queryKey: ["buyers"],
    queryFn: () => api.get("/buyers"),
  });

  const buyers = data?.items ?? [];

  return (
    <div className="p-6">
      <PageHeader title="Buyers" />

      {isLoading && <Skeleton rows={6} />}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          Failed to load buyers.
        </div>
      )}

      {!isLoading && !error && buyers.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-400">
          No buyers found.
        </div>
      )}

      {!isLoading && buyers.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Code</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Contact</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Phone</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Outstanding</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Orders</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {buyers.map((b) => (
                  <tr key={b.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-sm">
                      <Link to={`/app/buyers/${b.id}`} className="text-indigo-600 hover:text-indigo-800 font-medium">
                        {b.code}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">{b.name}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{b.contact_person}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{b.phone}</td>
                    <td className="px-4 py-3 text-sm text-right font-medium text-gray-900">{formatPaise(b.outstanding_paise)}</td>
                    <td className="px-4 py-3 text-sm text-right text-gray-600">{b.orders_count}</td>
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
