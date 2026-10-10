import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { qk } from "../../lib/query-keys";
import { formatCm, formatDateTime } from "../../lib/format";
import KpiTile from "../../components/ui/KpiTile";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import { clsx } from "clsx";

/* ---------- types ---------- */

interface FloorMachine {
  id: string;
  code: string;
  name: string;
  stage: string;
  status: string;
  floor_x: number;
  floor_y: number;
  current_job_code: string | null;
  current_order_code: string | null;
  produced_qty: number;
  planned_qty: number;
}

interface FloorData {
  machines: FloorMachine[];
}

interface Job {
  id: string;
  code: string;
  order_code: string;
  stage: string;
  planned_qty: number;
  produced_qty: number;
  waste_qty: number;
  machine_id: string | null;
  status: string;
  started_at: string;
}

interface JobList {
  items: Job[];
  total: number;
}

interface TodayRow {
  stage: string;
  output_cm: number;
  waste_cm: number;
}

interface TodayData {
  items: TodayRow[];
}

/* ---------- helpers ---------- */

const STATUS_COLORS: Record<string, { bg: string; ring: string; dot: string }> = {
  running:     { bg: "bg-green-50",  ring: "ring-green-300",  dot: "bg-green-500" },
  idle:        { bg: "bg-yellow-50", ring: "ring-yellow-300", dot: "bg-yellow-500" },
  breakdown:   { bg: "bg-red-50",    ring: "ring-red-300",    dot: "bg-red-500" },
  maintenance: { bg: "bg-blue-50",   ring: "ring-blue-300",   dot: "bg-blue-500" },
};

function statusStyle(status: string) {
  return STATUS_COLORS[status] ?? { bg: "bg-gray-50", ring: "ring-gray-300", dot: "bg-gray-400" };
}

function pct(produced: number, planned: number): string {
  if (planned <= 0) return "0%";
  return `${Math.min(100, Math.round((produced / planned) * 100))}%`;
}

/* ---------- component ---------- */

export default function ProductionPage() {
  const floor = useQuery({
    queryKey: [...qk.production.machines(), "floor"],
    queryFn: () => api.get<FloorData>("/production/floor"),
    refetchInterval: 15_000,
  });

  const jobs = useQuery({
    queryKey: qk.production.jobs({ status: "running" }),
    queryFn: () => api.get<JobList>("/jobs?status=running"),
    refetchInterval: 15_000,
  });

  const today = useQuery({
    queryKey: [...qk.production.machines(), "today"],
    queryFn: () => api.get<TodayData>("/production/today"),
    refetchInterval: 30_000,
  });

  const machines = floor.data?.machines ?? [];
  const runningJobs = jobs.data?.items ?? [];
  const todayRows = today.data?.items ?? [];

  const machinesRunning = machines.filter((m) => m.status === "running").length;
  const totalOutput = todayRows.reduce((s, r) => s + r.output_cm, 0);

  /* grid dimensions */
  const maxX = machines.reduce((mx, m) => Math.max(mx, m.floor_x), 0);
  const maxY = machines.reduce((mx, m) => Math.max(mx, m.floor_y), 0);
  const cols = maxX + 1 || 1;
  const rows = maxY + 1 || 1;

  /* build a lookup for the grid */
  const grid = new Map<string, FloorMachine>();
  for (const m of machines) {
    grid.set(`${m.floor_x},${m.floor_y}`, m);
  }

  /* stage label per row: pick the most common stage in that row */
  const rowStage = new Map<number, string>();
  for (let y = 0; y <= maxY; y++) {
    const stageCounts = new Map<string, number>();
    for (const m of machines) {
      if (m.floor_y === y) stageCounts.set(m.stage, (stageCounts.get(m.stage) ?? 0) + 1);
    }
    let best = ""; let bestN = 0;
    stageCounts.forEach((n, s) => { if (n > bestN) { best = s; bestN = n; } });
    if (best) rowStage.set(y, best);
  }

  const STAGE_COLORS: Record<string, string> = {
    spinning:  "bg-violet-50",
    weaving:   "bg-sky-50",
    dyeing:    "bg-teal-50",
    finishing: "bg-amber-50",
  };

  /* build machine id -> code lookup for job table */
  const machineById = new Map<string, string>();
  for (const m of machines) {
    machineById.set(m.id, m.code);
  }

  const isLoading = floor.isLoading || jobs.isLoading || today.isLoading;

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="Production" subtitle="Live floor overview" />

      {/* KPI tiles */}
      {isLoading ? (
        <Skeleton rows={4} className="max-w-sm" />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiTile
            label="Machines running"
            value={`${machinesRunning} / ${machines.length}`}
          />
          <KpiTile
            label="Today's output"
            value={formatCm(totalOutput)}
          />
          <KpiTile
            label="Active jobs"
            value={runningJobs.length}
          />
          <KpiTile
            label="Today's waste"
            value={formatCm(todayRows.reduce((s, r) => s + r.waste_cm, 0))}
          />
        </div>
      )}

      {/* Floor grid */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Floor Map</h2>

        {isLoading ? (
          <Skeleton rows={6} />
        ) : machines.length === 0 ? (
          <p className="text-gray-400 text-center py-8">No machines configured</p>
        ) : (
          <div className="overflow-x-auto">
            <div className="flex gap-0 min-w-[520px]">
              {/* Stage label sidebar */}
              <div
                className="flex flex-col shrink-0 mr-2"
                style={{ gap: "0.75rem" }}
              >
                {Array.from({ length: rows }).map((_, y) => {
                  const stage = rowStage.get(y) ?? "";
                  return (
                    <div
                      key={y}
                      className="flex items-center justify-end pr-1 min-h-[5.5rem]"
                      style={{ minWidth: 72 }}
                    >
                      {stage && (
                        <span className="text-[10px] font-semibold uppercase tracking-widest text-gray-400">
                          {stage}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Grid */}
              <div
                className="flex-1 grid gap-3 p-3 rounded-xl border border-gray-200 bg-gray-50"
                style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
              >
                {Array.from({ length: rows }).map((_, y) =>
                  Array.from({ length: cols }).map((_, x) => {
                    const m = grid.get(`${x},${y}`);
                    const zoneBg = STAGE_COLORS[rowStage.get(y) ?? ""] ?? "";

                    if (!m) {
                      return (
                        <div
                          key={`${x},${y}`}
                          className={clsx(
                            "min-h-[5.5rem] rounded-lg border border-dashed border-gray-200",
                            zoneBg || "bg-white/60",
                          )}
                        />
                      );
                    }

                    const s = statusStyle(m.status);
                    const progress = m.planned_qty > 0
                      ? Math.min(100, Math.round((m.produced_qty / m.planned_qty) * 100))
                      : 0;

                    return (
                      <div
                        key={m.id}
                        className={clsx(
                          "rounded-lg ring-2 p-3 min-h-[5.5rem] flex flex-col justify-between shadow-sm",
                          s.bg,
                          s.ring,
                        )}
                      >
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className={clsx("w-2 h-2 rounded-full shrink-0", s.dot)} />
                            <span className="font-mono text-sm font-bold text-gray-900 truncate">
                              {m.code}
                            </span>
                          </div>
                          <p className="text-[11px] text-gray-500 truncate mt-0.5 ml-3.5">{m.name}</p>
                        </div>

                        {m.status === "running" && m.current_job_code ? (
                          <div className="mt-2">
                            <p className="text-[11px] text-indigo-700 font-medium truncate">
                              {m.current_job_code}
                              {m.current_order_code ? ` · ${m.current_order_code}` : ""}
                            </p>
                            <div className="mt-1 w-full bg-gray-200 rounded-full h-1.5">
                              <div
                                className="bg-green-500 h-1.5 rounded-full transition-all"
                                style={{ width: `${progress}%` }}
                              />
                            </div>
                            <p className="text-[10px] text-gray-400 mt-0.5 text-right">
                              {pct(m.produced_qty, m.planned_qty)}
                            </p>
                          </div>
                        ) : (
                          <p className="text-[10px] text-gray-400 uppercase tracking-wide mt-1">
                            {m.status}
                          </p>
                        )}
                      </div>
                    );
                  }),
                )}
              </div>
            </div>

            {/* Stage zone legend */}
            <div className="flex flex-wrap gap-3 mt-3 ml-20">
              {Object.entries(STAGE_COLORS).map(([stage, bg]) => (
                machines.some((m) => m.stage === stage) && (
                  <div key={stage} className={clsx("flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium text-gray-600 border border-gray-200", bg)}>
                    <span className="capitalize">{stage}</span>
                  </div>
                )
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Running jobs table */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Running Jobs</h2>
        </div>

        {isLoading ? (
          <div className="p-5">
            <Skeleton rows={5} />
          </div>
        ) : runningJobs.length === 0 ? (
          <p className="text-gray-400 text-center py-8">No jobs currently running</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50 text-gray-500 uppercase text-xs">
                <tr>
                  <th className="px-5 py-3">Job Code</th>
                  <th className="px-5 py-3">Order</th>
                  <th className="px-5 py-3">Stage</th>
                  <th className="px-5 py-3">Machine</th>
                  <th className="px-5 py-3">Progress</th>
                  <th className="px-5 py-3">Started</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {runningJobs.map((j) => {
                  const progress = j.planned_qty > 0
                    ? Math.min(100, Math.round((j.produced_qty / j.planned_qty) * 100))
                    : 0;
                  return (
                    <tr key={j.id} className="hover:bg-gray-50">
                      <td className="px-5 py-3 font-mono font-medium text-gray-900">
                        {j.code}
                      </td>
                      <td className="px-5 py-3 text-gray-700">{j.order_code}</td>
                      <td className="px-5 py-3 text-gray-700 capitalize">{j.stage}</td>
                      <td className="px-5 py-3 font-mono text-gray-700">
                        {j.machine_id ? (machineById.get(j.machine_id) ?? j.machine_id) : "—"}
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-green-500 h-2 rounded-full"
                              style={{ width: `${progress}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500 whitespace-nowrap">
                            {pct(j.produced_qty, j.planned_qty)}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-3 text-gray-500 whitespace-nowrap">
                        {formatDateTime(j.started_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs text-gray-500">
        {Object.entries(STATUS_COLORS).map(([status, s]) => (
          <div key={status} className="flex items-center gap-1.5">
            <span className={clsx("w-2.5 h-2.5 rounded-full", s.dot)} />
            <span className="capitalize">{status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
