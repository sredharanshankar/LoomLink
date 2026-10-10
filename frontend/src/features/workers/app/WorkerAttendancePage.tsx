import { useQuery } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import { formatDateTime } from "../../../lib/format";
import PageHeader from "../../../components/ui/PageHeader";
import Badge from "../../../components/ui/Badge";
import Skeleton from "../../../components/ui/Skeleton";

interface AttendanceRecord {
  id: string;
  date: string;
  check_in: string | null;
  check_out: string | null;
  status: string;
}

interface AttendanceResponse {
  items: AttendanceRecord[];
  total: number;
}

const STATUS_COLOR: Record<string, "green" | "yellow" | "red" | "gray"> = {
  present: "green",
  late: "yellow",
  absent: "red",
  half_day: "yellow",
};

export default function WorkerAttendancePage() {
  const { data, isLoading } = useQuery({
    queryKey: ["attendance"],
    queryFn: () => api.get<AttendanceResponse>("/attendance?page=1&size=10"),
  });

  if (isLoading) return <div className="p-4"><Skeleton rows={6} /></div>;

  return (
    <div className="p-4 space-y-4">
      <PageHeader title="Attendance" subtitle="Recent check-ins" />

      {data?.items.length === 0 && (
        <p className="text-center text-sm text-gray-400 py-8">No attendance records</p>
      )}

      <div className="space-y-2">
        {data?.items.map((record) => (
          <div key={record.id} className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">{record.date}</span>
              <Badge color={STATUS_COLOR[record.status] ?? "gray"}>{record.status}</Badge>
            </div>
            <div className="flex gap-4 text-xs text-gray-500">
              {record.check_in && <span>In: {formatDateTime(record.check_in)}</span>}
              {record.check_out && <span>Out: {formatDateTime(record.check_out)}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
