import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { formatPaise } from "../../lib/format";
import { qk } from "../../lib/query-keys";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import Badge from "../../components/ui/Badge";

interface Worker {
  id: string;
  employee_code: string;
  name: string;
  role: string;
  shift_code: string;
  daily_wage_paise: number;
  is_active: boolean;
}

export default function WorkersPage() {
  const { data, isLoading } = useQuery({
    queryKey: qk.workers.list(),
    queryFn: () => api.get<{ items: Worker[]; total: number }>("/workers?page=1&size=50"),
  });

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="Workers" subtitle={`${data?.total ?? 0} workers`} />

      {isLoading ? (
        <Skeleton rows={8} />
      ) : (
        <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Code</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Name</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Role</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Shift</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500">Daily Wage</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items.map((w) => (
                <tr key={w.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-gray-700">{w.employee_code}</td>
                  <td className="px-4 py-3">
                    <Link to={`/app/workers/${w.id}`} className="text-blue-600 hover:underline font-medium">
                      {w.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-700">{w.role}</td>
                  <td className="px-4 py-3 text-gray-700">{w.shift_code}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{formatPaise(w.daily_wage_paise)}</td>
                  <td className="px-4 py-3">
                    <Badge color={w.is_active ? "green" : "gray"}>
                      {w.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </td>
                </tr>
              ))}
              {data?.items.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No workers</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
