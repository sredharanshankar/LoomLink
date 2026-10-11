import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { AlertTriangle, ArrowLeft, CheckCircle, Wrench } from "lucide-react";
import { clsx } from "clsx";

interface Fix {
  fix_id: string;
  label: string;
  description: string;
  estimated_cost_paise: number;
  orders_rescued: string[];
  ranked: number;
}

interface RippleEvent {
  id: string;
  event_type: string;
  severity: "low" | "medium" | "high" | "critical";
  status: "open" | "in_review" | "resolved" | "dismissed";
  title: string;
  summary: string;
  at_risk_paise: number;
  affected_order_codes: string[];
  fixes: Fix[];
  created_at: string;
}

export default function RippleEventPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: ev, isLoading } = useQuery<RippleEvent>({
    queryKey: ["ripple-event", id],
    queryFn: () => api.get(`/ripple/events/${id}`),
    enabled: !!id,
  });

  const applyFix = useMutation({
    mutationFn: (fixId: string) => api.post(`/ripple/events/${id}/fixes/${fixId}/apply`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ripple-event", id] }),
  });

  const dismiss = useMutation({
    mutationFn: () => api.post(`/ripple/events/${id}/dismiss`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["ripple-events"] }); navigate("/app/ripple"); },
  });

  if (isLoading) return <div className="p-6 animate-pulse h-64 bg-gray-100 dark:bg-gray-800 rounded-xl" />;
  if (!ev) return <div className="p-6 text-gray-500">Event not found.</div>;

  const resolved = ev.status === "resolved" || ev.status === "dismissed";

  return (
    <div className="p-6 max-w-3xl space-y-6">
      <button onClick={() => navigate("/app/ripple")} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 dark:hover:text-white">
        <ArrowLeft className="h-4 w-4" /> Back to inbox
      </button>

      <div className={clsx("rounded-xl border p-5 space-y-3", {
        "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950": ev.severity === "critical",
        "border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-950": ev.severity === "high",
        "border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950": ev.severity === "medium",
        "border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950": ev.severity === "low",
      })}>
        <div className="flex items-start gap-3">
          <AlertTriangle className={clsx("h-5 w-5 mt-0.5 shrink-0", {
            "text-red-600": ev.severity === "critical",
            "text-orange-500": ev.severity === "high",
            "text-amber-500": ev.severity === "medium",
            "text-blue-500": ev.severity === "low",
          })} />
          <div>
            <h1 className="font-semibold text-gray-900 dark:text-white">{ev.title}</h1>
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{ev.summary}</p>
          </div>
          {ev.at_risk_paise > 0 && (
            <div className="ml-auto text-right shrink-0">
              <p className="text-xs text-gray-500">at risk</p>
              <p className="text-lg font-bold text-red-600 dark:text-red-400">
                ₹{Math.round(ev.at_risk_paise / 100).toLocaleString("en-IN")}
              </p>
            </div>
          )}
        </div>
      </div>

      {ev.fixes?.length > 0 && !resolved && (
        <div className="space-y-3">
          <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Wrench className="h-4 w-4 text-brand-600" />
            Suggested Fixes
          </h2>
          {ev.fixes.map((fix) => (
            <div key={fix.fix_id} className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold text-brand-700 dark:text-brand-300 bg-brand-50 dark:bg-brand-950 px-1.5 py-0.5 rounded">#{fix.ranked}</span>
                    <span className="font-medium text-gray-900 dark:text-white text-sm">{fix.label}</span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{fix.description}</p>
                  {fix.orders_rescued?.length > 0 && (
                    <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                      Saves: {fix.orders_rescued.join(", ")}
                    </p>
                  )}
                  {fix.estimated_cost_paise > 0 && (
                    <p className="text-xs text-gray-500 mt-0.5">
                      Cost ≈ ₹{Math.round(fix.estimated_cost_paise / 100).toLocaleString("en-IN")}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => applyFix.mutate(fix.fix_id)}
                  disabled={applyFix.isPending}
                  className="shrink-0 rounded-lg bg-brand-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-800 disabled:opacity-50"
                >
                  Apply
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {resolved && (
        <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
          <CheckCircle className="h-5 w-5" />
          <span className="font-medium">This event has been {ev.status}.</span>
        </div>
      )}

      {!resolved && (
        <button
          onClick={() => dismiss.mutate()}
          disabled={dismiss.isPending}
          className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 underline"
        >
          Dismiss without action
        </button>
      )}
    </div>
  );
}
