import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import { qk } from "../../lib/query-keys";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import StatusPill from "../../components/ui/StatusPill";

interface AttendanceRecord {
  id: string;
  worker_name: string;
  date: string;
  shift_code: string;
  check_in_at: string | null;
  check_out_at: string | null;
  status: string;
}

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function AttendancePage() {
  const [date, setDate] = useState(todayISO);

  const { data, isLoading } = useQuery({
    queryKey: qk.workers.attendance(date),
    queryFn: () =>
      api.get<{ items: AttendanceRecord[]; total: number }>(
        `/attendance?page=1&size=50&date=${date}`
      ),
  });

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="Attendance"
        subtitle={`${data?.total ?? 0} records`}
        actions={
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
        }
      />

      {isLoading ? (
        <Skeleton rows={8} />
      ) : (
        <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Worker</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Date</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Shift</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Check In</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Check Out</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items.map((a) => (
                <tr key={a.id}>
                  <td className="px-4 py-3 text-gray-900">{a.worker_name}</td>
                  <td className="px-4 py-3 text-gray-700">{a.date}</td>
                  <td className="px-4 py-3 text-gray-700">{a.shift_code}</td>
                  <td className="px-4 py-3 text-gray-700">{a.check_in_at ? formatDateTime(a.check_in_at) : "-"}</td>
                  <td className="px-4 py-3 text-gray-700">{a.check_out_at ? formatDateTime(a.check_out_at) : "-"}</td>
                  <td className="px-4 py-3"><StatusPill status={a.status} size="sm" /></td>
                </tr>
              ))}
              {data?.items.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No records for {date}</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
