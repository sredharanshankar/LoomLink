import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";

interface Machine {
  id: string;
  code: string;
  name: string;
  stage: string;
  floor_x: number;
  floor_y: number;
  status: string;
  current_job: { code: string } | null;
}

interface FloorResponse {
  machines: Machine[];
}

const STATUS_COLORS: Record<string, { bg: string; border: string; label: string }> = {
  running: { bg: "bg-green-100", border: "border-green-400", label: "Running" },
  idle: { bg: "bg-yellow-50", border: "border-yellow-400", label: "Idle" },
  breakdown: { bg: "bg-red-100", border: "border-red-400", label: "Breakdown" },
  maintenance: { bg: "bg-blue-100", border: "border-blue-400", label: "Maintenance" },
  changeover: { bg: "bg-orange-100", border: "border-orange-400", label: "Changeover" },
};

const STAGE_ORDER = ["spinning", "weaving", "dyeing", "finishing"];

export default function FloorPage() {
  const { data, isLoading, error } = useQuery<FloorResponse>({
    queryKey: ["production", "floor"],
    queryFn: () => api.get("/production/floor"),
    refetchInterval: 10_000,
  });

  const machines = data?.machines ?? [];

  const stagesPresent = STAGE_ORDER.filter((s) =>
    machines.some((m) => m.stage === s)
  );
  const ungrouped = machines.filter((m) => !STAGE_ORDER.includes(m.stage));
  if (ungrouped.length > 0) stagesPresent.push("other");

  return (
    <div className="p-6">
      <PageHeader title="Ripple Floor" subtitle="Live machine status map" />

      {isLoading && <Skeleton rows={8} />}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          Failed to load floor data.
        </div>
      )}

      {!isLoading && !error && machines.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center text-gray-400">
          No machines configured yet. Add machines in Settings to see them here.
        </div>
      )}

      {!isLoading && machines.length > 0 && (
        <>
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
            <div
              className="relative"
              style={{
                backgroundImage:
                  "linear-gradient(to right, #f3f4f6 1px, transparent 1px), linear-gradient(to bottom, #f3f4f6 1px, transparent 1px)",
                backgroundSize: "calc(100% / 11) calc(100% / 6)",
                minHeight: 480,
              }}
            >
              {stagesPresent.map((stage, si) => {
                const stageMachines =
                  stage === "other"
                    ? ungrouped
                    : machines.filter((m) => m.stage === stage);
                if (stageMachines.length === 0) return null;
                const minY = Math.min(...stageMachines.map((m) => m.floor_y));
                const maxY = Math.max(...stageMachines.map((m) => m.floor_y));
                const topPct = (minY / 6) * 100;
                const heightPct = ((maxY - minY + 1) / 6) * 100;
                return (
                  <div
                    key={stage}
                    className="absolute left-0 flex items-center pointer-events-none"
                    style={{
                      top: `${topPct}%`,
                      height: `${heightPct}%`,
                      writingMode: "vertical-rl",
                      transform: "rotate(180deg)",
                      marginLeft: -4,
                    }}
                  >
                    <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">
                      {stage}
                    </span>
                  </div>
                );
              })}

              {machines.map((m) => {
                const sc = STATUS_COLORS[m.status] ?? STATUS_COLORS.idle;
                const leftPct = (m.floor_x / 10) * 100;
                const topPct = (m.floor_y / 5) * 100;
                return (
                  <Link
                    key={m.id}
                    to={`/app/machines/${m.id}`}
                    className={`absolute rounded-lg border-2 ${sc.bg} ${sc.border} shadow-sm hover:shadow-md transition-shadow`}
                    style={{
                      left: `${leftPct}%`,
                      top: `${topPct}%`,
                      width: "8%",
                      height: "14%",
                      minWidth: 72,
                      minHeight: 56,
                    }}
                  >
                    <div className="flex flex-col items-center justify-center h-full px-1 py-1 text-center">
                      <span className="text-xs font-bold text-gray-900 truncate w-full">
                        {m.code}
                      </span>
                      <span className="text-[10px] text-gray-600 truncate w-full">
                        {m.name}
                      </span>
                      {m.current_job && (
                        <span className="text-[10px] font-medium text-indigo-700 mt-0.5 truncate w-full">
                          {m.current_job.code}
                        </span>
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>

          <div className="flex flex-wrap gap-4">
            {Object.entries(STATUS_COLORS).map(([key, val]) => (
              <div key={key} className="flex items-center gap-2">
                <div className={`w-4 h-4 rounded border-2 ${val.bg} ${val.border}`} />
                <span className="text-sm text-gray-600">{val.label}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
