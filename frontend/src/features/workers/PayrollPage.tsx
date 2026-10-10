import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatPaise } from "../../lib/format";
import { qk } from "../../lib/query-keys";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import StatusPill from "../../components/ui/StatusPill";

interface PayrollRun {
  id: string;
  period: string;
  status: string;
  total_paise: number;
  worker_count: number;
}

interface Worker {
  id: string;
  employee_code: string;
  name: string;
  role: string;
  daily_wage_paise: number;
}

export default function PayrollPage() {
  const { data: runs, isLoading: loadingRuns } = useQuery({
    queryKey: ["payroll-runs"],
    queryFn: () => api.get<{ items: PayrollRun[]; total: number }>("/payroll/runs"),
  });

  const { data: workers, isLoading: loadingWorkers } = useQuery({
    queryKey: qk.workers.list(),
    queryFn: () => api.get<{ items: Worker[]; total: number }>("/workers"),
  });

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="Payroll" subtitle={`${runs?.total ?? 0} payroll runs`} />

      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Payroll Runs</h2>
        {loadingRuns ? (
          <Skeleton rows={4} />
        ) : (
          <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Period</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Total</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Workers</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {runs?.items.map((r) => (
                  <tr key={r.id}>
                    <td className="px-4 py-3 text-gray-900 font-medium">{r.period}</td>
                    <td className="px-4 py-3"><StatusPill status={r.status} size="sm" /></td>
                    <td className="px-4 py-3 text-right tabular-nums">{formatPaise(r.total_paise)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{r.worker_count}</td>
                  </tr>
                ))}
                {runs?.items.length === 0 && (
                  <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">No payroll runs</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Worker Wages</h2>
        {loadingWorkers ? (
          <Skeleton rows={6} />
        ) : (
          <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Code</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Name</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Role</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Daily Wage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {workers?.items.map((w) => (
                  <tr key={w.id}>
                    <td className="px-4 py-3 font-mono text-gray-700">{w.employee_code}</td>
                    <td className="px-4 py-3 text-gray-900">{w.name}</td>
                    <td className="px-4 py-3 text-gray-700">{w.role}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{formatPaise(w.daily_wage_paise)}</td>
                  </tr>
                ))}
                {workers?.items.length === 0 && (
                  <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">No workers</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
