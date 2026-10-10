import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../../../lib/api";
import { formatCm, formatDateTime } from "../../../lib/format";
import PageHeader from "../../../components/ui/PageHeader";
import Skeleton from "../../../components/ui/Skeleton";
import Badge from "../../../components/ui/Badge";

interface Job {
  id: string;
  code: string;
  order_code: string;
  stage: string;
  status: string;
  planned_qty: number;
  produced_qty: number;
  waste_qty: number;
  machine_id: string | null;
  started_at: string | null;
}

const STATUS_COLOR: Record<string, "green" | "yellow" | "gray" | "blue" | "red"> = {
  running: "green",
  queued: "yellow",
  paused: "orange" as "yellow",
  completed: "blue",
  cancelled: "red",
};

export default function WorkerJobsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["worker-all-jobs"],
    queryFn: () => api.get<{ items: Job[]; total: number }>("/jobs?page=1&size=50"),
  });

  const jobs = data?.items ?? [];
  const running = jobs.filter((j) => j.status === "running");
  const queued = jobs.filter((j) => j.status === "queued");
  const completed = jobs.filter((j) => j.status === "completed");

  return (
    <div className="p-4 space-y-4">
      <PageHeader title="My Jobs" subtitle={`${running.length} running, ${queued.length} queued`} />

      {isLoading ? (
        <Skeleton rows={6} />
      ) : jobs.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-6 text-center text-gray-400">
          No jobs assigned.
        </div>
      ) : (
        <>
          {/* Running jobs */}
          {running.length > 0 && (
            <section>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Running</h3>
              <div className="space-y-2">
                {running.map((job) => (
                  <JobCard key={job.id} job={job} />
                ))}
              </div>
            </section>
          )}

          {/* Queued */}
          {queued.length > 0 && (
            <section>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 mt-4">Queued</h3>
              <div className="space-y-2">
                {queued.map((job) => (
                  <JobCard key={job.id} job={job} />
                ))}
              </div>
            </section>
          )}

          {/* Completed (last 5) */}
          {completed.length > 0 && (
            <section>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 mt-4">
                Completed ({completed.length})
              </h3>
              <div className="space-y-2">
                {completed.slice(0, 5).map((job) => (
                  <JobCard key={job.id} job={job} />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function JobCard({ job }: { job: Job }) {
  const pct = job.planned_qty > 0
    ? Math.round((job.produced_qty / job.planned_qty) * 100)
    : 0;

  return (
    <Link
      to={`/w/job/${job.id}`}
      className="block bg-white rounded-lg border border-gray-200 p-3 hover:bg-gray-50"
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-gray-900">{job.code}</span>
        <Badge color={STATUS_COLOR[job.status] ?? "gray"}>{job.status}</Badge>
      </div>
      <p className="text-xs text-gray-500">
        Order {job.order_code} · {job.stage} · {formatCm(job.produced_qty)} / {formatCm(job.planned_qty)}
      </p>
      {job.status === "running" && (
        <>
          <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2">
            <div
              className="bg-blue-600 h-1.5 rounded-full"
              style={{ width: `${Math.min(pct, 100)}%` }}
            />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-xs text-gray-400">
              {job.started_at ? `Started ${formatDateTime(job.started_at)}` : ""}
            </span>
            <span className="text-xs text-gray-500 font-medium">{pct}%</span>
          </div>
        </>
      )}
    </Link>
  );
}
