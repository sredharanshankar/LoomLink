import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { clsx } from "clsx";
import { AlertTriangle, Wrench } from "lucide-react";
import { api } from "../../lib/api";
import { qk } from "../../lib/query-keys";
import { formatRelative } from "../../lib/format";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import EmptyState from "../../components/ui/EmptyState";

interface Machine {
  id: string;
  code: string;
  name: string;
  stage: string;
  floor_x: number;
  floor_y: number;
  status: string;
  status_changed_at: string;
  current_job_code: string | null;
  current_order_code: string | null;
  produced_qty: number;
  planned_qty: number;
}

const STATUS: Record<string, { label: string; dot: string; tile: string }> = {
  running: { label: "Running", dot: "bg-emerald-500", tile: "border-emerald-500/40 bg-emerald-50/60" },
  idle: { label: "Idle", dot: "bg-gray-400", tile: "border-gray-200 bg-white" },
  maintenance: { label: "Maintenance", dot: "bg-violet-500", tile: "border-violet-500/40 bg-violet-50/70" },
  breakdown: { label: "Breakdown", dot: "bg-red-500", tile: "border-red-500/50 bg-red-50/80" },
  changeover: { label: "Changeover", dot: "bg-orange-500", tile: "border-orange-500/40 bg-orange-50/70" },
};

const STAGE_ACCENT: Record<string, { label: string; bar: string }> = {
  spinning: { label: "Spinning", bar: "bg-violet-500" },
  weaving: { label: "Weaving", bar: "bg-sky-500" },
  dyeing: { label: "Dyeing", bar: "bg-teal-500" },
  finishing: { label: "Finishing", bar: "bg-amber-500" },
};

function MachineTile({ m, col, row }: { m: Machine; col: number; row: number }) {
  const s = STATUS[m.status] ?? STATUS.idle;
  const stage = STAGE_ACCENT[m.stage];
  const pct = m.planned_qty > 0 ? Math.min(100, Math.round((m.produced_qty / m.planned_qty) * 100)) : 0;

  return (
    <Link
      to={`/app/machines/${m.id}`}
      style={{ gridColumn: col, gridRow: row }}
      className={clsx(
        "group relative flex min-h-[112px] flex-col overflow-hidden rounded-xl border p-3 pl-4 shadow-card transition-all duration-150 hover:-translate-y-0.5 hover:shadow-lift",
        s.tile,
      )}
    >
      <span className={clsx("absolute inset-y-0 left-0 w-1", stage?.bar ?? "bg-gray-300")} />
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[13px] font-bold tracking-tight text-gray-900">{m.code}</span>
        <span className="relative flex h-2 w-2" title={s.label}>
          {(m.status === "running" || m.status === "breakdown") && (
            <span className={clsx("absolute inline-flex h-full w-full animate-ping rounded-full opacity-60", s.dot)} />
          )}
          <span className={clsx("relative inline-flex h-2 w-2 rounded-full", s.dot)} />
        </span>
      </div>
      <p className="truncate text-xs text-gray-500">{m.name}</p>

      <div className="mt-auto pt-2">
        {m.status === "running" && m.current_job_code ? (
          <>
            <p className="truncate text-[11px] font-medium text-brand-700">{m.current_order_code ?? m.current_job_code}</p>
            <div className="mt-1 flex items-center gap-2">
              <div className="h-1.5 flex-1 rounded-full bg-gray-200/80">
                <div className="h-full rounded-full bg-emerald-500" style={{ width: `${pct}%` }} />
              </div>
              <span className="tabular text-[10px] font-medium text-gray-500">{pct}%</span>
            </div>
          </>
        ) : m.status === "breakdown" || m.status === "maintenance" ? (
          <p className={clsx("flex items-center gap-1 text-[11px] font-medium", m.status === "breakdown" ? "text-red-700" : "text-violet-700")}>
            {m.status === "breakdown" ? <AlertTriangle className="h-3 w-3" /> : <Wrench className="h-3 w-3" />}
            {s.label} · {formatRelative(m.status_changed_at)}
          </p>
        ) : (
          <p className="text-[11px] font-medium text-gray-400">{s.label}</p>
        )}
      </div>
    </Link>
  );
}

export default function FloorPage() {
  const { data, isLoading, error } = useQuery<{ machines: Machine[] }>({
    queryKey: [...qk.production.machines(), "floor"],
    queryFn: () => api.get("/production/floor"),
    refetchInterval: 10_000,
  });

  const machines = data?.machines ?? [];
  // Collapse empty floor coordinates so tiles keep their relative layout without dead columns.
  const xs = [...new Set(machines.map((m) => m.floor_x))].sort((a, b) => a - b);
  const ys = [...new Set(machines.map((m) => m.floor_y))].sort((a, b) => a - b);
  const cols = Math.max(1, xs.length);
  const rows = Math.max(1, ys.length);
  const counts = Object.keys(STATUS).map((k) => ({ key: k, ...STATUS[k], n: machines.filter((m) => m.status === k).length }));
  const stagesPresent = Object.entries(STAGE_ACCENT).filter(([k]) => machines.some((m) => m.stage === k));

  return (
    <div className="p-6 lg:p-8">
      <PageHeader title="Production floor" subtitle="Live machine map · refreshes every 10 seconds" />

      {isLoading && <div className="card p-6"><Skeleton rows={8} /></div>}
      {error && (
        <div className="rounded-xl bg-red-50 p-4 text-sm text-red-700 ring-1 ring-inset ring-red-600/15">Failed to load floor data.</div>
      )}

      {!isLoading && !error && machines.length === 0 && (
        <div className="card">
          <EmptyState title="No machines configured yet" description="Add machines in Settings to see them on the floor map." />
        </div>
      )}

      {!isLoading && machines.length > 0 && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            {counts.filter((c) => c.n > 0 || c.key !== "changeover").map((c) => (
              <span key={c.key} className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-1.5 text-sm shadow-card ring-1 ring-gray-200">
                <span className={clsx("h-2 w-2 rounded-full", c.dot)} />
                <span className="text-gray-600">{c.label}</span>
                <span className="tabular font-semibold text-gray-900">{c.n}</span>
              </span>
            ))}
            <span className="ml-auto hidden items-center gap-3 text-xs text-gray-500 sm:flex">
              {stagesPresent.map(([k, v]) => (
                <span key={k} className="inline-flex items-center gap-1.5">
                  <span className={clsx("h-3 w-1 rounded-full", v.bar)} />
                  {v.label}
                </span>
              ))}
            </span>
          </div>

          <div className="card overflow-x-auto p-4 sm:p-6">
            <div
              className="bg-grid grid gap-3 rounded-lg p-3"
              style={{
                gridTemplateColumns: `repeat(${cols}, minmax(180px, 1fr))`,
                gridTemplateRows: `repeat(${rows}, minmax(112px, auto))`,
              }}
            >
              {machines.map((m) => (
                <MachineTile key={m.id} m={m} col={xs.indexOf(m.floor_x) + 1} row={ys.indexOf(m.floor_y) + 1} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
