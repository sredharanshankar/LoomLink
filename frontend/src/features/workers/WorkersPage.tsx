import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { formatPaise } from "../../lib/format";
import { qk } from "../../lib/query-keys";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import Badge from "../../components/ui/Badge";
import EmptyState from "../../components/ui/EmptyState";

interface Worker {
  id: string;
  code: string;
  name: string;
  department: string | null;
  skill_stages: string[];
  wage_type: "daily" | "piece" | "monthly" | string;
  wage_rate_paise: number | null;
  piece_rate_paise_per_m: number | null;
  default_shift: string | null;
  preferred_language: string | null;
  is_active: boolean;
}

const LANGUAGE: Record<string, string> = { en: "English", hi: "Hindi", te: "Telugu", ta: "Tamil" };

const AVATAR_TONES = [
  "bg-brand-100 text-brand-700",
  "bg-emerald-100 text-emerald-700",
  "bg-amber-100 text-amber-800",
  "bg-sky-100 text-sky-700",
  "bg-violet-100 text-violet-700",
  "bg-rose-100 text-rose-700",
];

function wageLabel(w: Worker) {
  if (w.wage_type === "piece" && w.piece_rate_paise_per_m != null) return `${formatPaise(w.piece_rate_paise_per_m, { showPaise: true })} / m`;
  if (w.wage_rate_paise == null) return "—";
  const unit = w.wage_type === "monthly" ? "month" : "day";
  return `${formatPaise(w.wage_rate_paise)} / ${unit}`;
}

export default function WorkersPage() {
  const { data, isLoading } = useQuery({
    queryKey: qk.workers.list(),
    queryFn: () => api.get<{ items: Worker[]; total: number }>("/workers?page=1&size=50"),
  });

  const items = data?.items ?? [];
  const active = items.filter((w) => w.is_active).length;

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader title="Workers" subtitle={data ? `${data.total} people · ${active} active` : undefined} />

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-5"><Skeleton rows={8} /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50/80">
                  <th className="table-header-cell">Worker</th>
                  <th className="table-header-cell">Skills</th>
                  <th className="table-header-cell">Shift</th>
                  <th className="table-header-cell">Language</th>
                  <th className="table-header-cell text-right">Wage</th>
                  <th className="table-header-cell">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((w, i) => (
                  <tr key={w.id} className="transition-colors hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${AVATAR_TONES[i % AVATAR_TONES.length]}`}>
                          {w.name.slice(0, 2).toUpperCase()}
                        </span>
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-gray-900">{w.name}</p>
                          <p className="font-mono text-xs text-gray-500">{w.code}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {w.skill_stages.length ? (
                          w.skill_stages.map((s) => (
                            <span key={s} className="rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium capitalize text-gray-700">{s}</span>
                          ))
                        ) : (
                          <span className="text-sm text-gray-400">—</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">{w.default_shift ? `Shift ${w.default_shift}` : "—"}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {w.preferred_language ? LANGUAGE[w.preferred_language] ?? w.preferred_language : "—"}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-medium text-gray-900">{wageLabel(w)}</td>
                    <td className="px-4 py-3">
                      <Badge color={w.is_active ? "green" : "gray"}>{w.is_active ? "Active" : "Inactive"}</Badge>
                    </td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr><td colSpan={6}><EmptyState title="No workers yet" /></td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
