import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useAuth } from "../../../lib/auth";
import { api } from "../../../lib/api";
import { formatDateTime } from "../../../lib/format";
import PageHeader from "../../../components/ui/PageHeader";
import Skeleton from "../../../components/ui/Skeleton";
import Badge from "../../../components/ui/Badge";

interface AttendanceRecord {
  id: string;
  date: string;
  shift_code: string;
  check_in_at: string | null;
  check_out_at: string | null;
  status: string;
}

interface Job {
  id: string;
  code: string;
  order_code: string;
  stage: string;
  status: string;
  planned_qty: number;
  produced_qty: number;
  machine_id: string | null;
}

export default function WorkerHomePage() {
  const { user } = useAuth();

  const { data: attendance, isLoading: attLoading } = useQuery({
    queryKey: ["worker-attendance"],
    queryFn: () => api.get<{ items: AttendanceRecord[] }>("/attendance?page=1&size=1"),
  });

  const { data: jobs, isLoading: jobsLoading } = useQuery({
    queryKey: ["worker-jobs-running"],
    queryFn: () => api.get<{ items: Job[] }>("/jobs?status=running&page=1&size=5"),
  });

  const isLoading = attLoading || jobsLoading;
  const todayAtt = attendance?.items?.[0];
  const runningJobs = jobs?.items ?? [];

  return (
    <div className="p-4 space-y-4">
      <PageHeader title={`Hello, ${user?.full_name ?? "Worker"}`} subtitle="Your shift overview" />

      {isLoading ? (
        <Skeleton rows={4} />
      ) : (
        <>
          {/* Attendance card */}
          <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-2">
            <h3 className="text-sm font-medium text-gray-500">Today&apos;s Attendance</h3>
            {todayAtt ? (
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-900">
                    Shift {todayAtt.shift_code} — checked in{" "}
                    {todayAtt.check_in_at ? formatDateTime(todayAtt.check_in_at) : "—"}
                  </p>
                </div>
                <Badge color={todayAtt.status === "present" ? "green" : "yellow"}>
                  {todayAtt.status}
                </Badge>
              </div>
            ) : (
              <p className="text-sm text-gray-400">No attendance record today.</p>
            )}
          </div>

          {/* Active jobs */}
          <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-500">Active Jobs</h3>
              <Link to="/w/jobs" className="text-xs text-blue-600 hover:underline">
                View all →
              </Link>
            </div>
            {runningJobs.length === 0 ? (
              <p className="text-sm text-gray-400">No active jobs right now.</p>
            ) : (
              <div className="space-y-2">
                {runningJobs.map((job) => {
                  const pct = job.planned_qty > 0
                    ? Math.round((job.produced_qty / job.planned_qty) * 100)
                    : 0;
                  return (
                    <Link
                      key={job.id}
                      to={`/w/job/${job.id}`}
                      className="block rounded-md border border-gray-100 p-3 hover:bg-gray-50"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-900">
                          {job.code}
                        </span>
                        <Badge color="green">{job.stage}</Badge>
                      </div>
                      <p className="text-xs text-gray-500 mb-2">Order {job.order_code}</p>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all"
                          style={{ width: `${Math.min(pct, 100)}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1 text-right">{pct}%</p>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>

          {/* Quick actions */}
          <div className="grid grid-cols-2 gap-3">
            <Link
              to="/w/scan"
              className="flex items-center justify-center rounded-lg border border-gray-200 bg-white p-4 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              📷 Scan
            </Link>
            <Link
              to="/w/me"
              className="flex items-center justify-center rounded-lg border border-gray-200 bg-white p-4 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              👤 My Profile
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
