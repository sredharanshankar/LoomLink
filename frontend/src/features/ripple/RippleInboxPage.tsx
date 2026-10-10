import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { AlertTriangle, CheckCircle, Clock, Zap } from "lucide-react";
import { clsx } from "clsx";

interface RippleEvent {
  id: string;
  event_type: string;
  severity: "low" | "medium" | "high" | "critical";
  status: "open" | "in_review" | "resolved" | "dismissed";
  title: string;
  summary: string;
  at_risk_paise: number;
  affected_order_codes: string[];
  created_at: string;
}

interface RippleEventList {
  items: RippleEvent[];
  total: number;
}

function SeverityBadge({ s }: { s: RippleEvent["severity"] }) {
  return (
    <span className={clsx("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium", {
      "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300": s === "critical",
      "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300": s === "high",
      "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300": s === "medium",
      "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300": s === "low",
    })}>
      {s === "critical" || s === "high" ? <AlertTriangle className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
      {s}
    </span>
  );
}

export default function RippleInboxPage() {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useQuery<RippleEventList>({
    queryKey: ["ripple-events"],
    queryFn: () => api.get("/ripple/events"),
    refetchInterval: 30_000,
  });

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-3">
        <Zap className="h-6 w-6 text-amber-500" />
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white">{t("ripple", "Ripple Inbox")}</h1>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[1,2,3].map(i => <div key={i} className="h-20 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse" />)}
        </div>
      )}

      {!isLoading && isError && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
          <AlertTriangle className="mx-auto h-8 w-8 text-red-400 mb-2" />
          <p className="text-red-700 text-sm font-medium">Failed to load Ripple events.</p>
          <p className="text-red-500 text-xs mt-1">Check your connection or contact your administrator.</p>
        </div>
      )}

      {!isLoading && !isError && !data?.items?.length && (
        <div className="rounded-xl border border-dashed border-gray-200 dark:border-gray-700 p-10 text-center">
          <CheckCircle className="mx-auto h-10 w-10 text-green-400 mb-2" />
          <p className="text-gray-600 dark:text-gray-400">{t("ripple.noEvents", "No active events — mill is running smoothly.")}</p>
        </div>
      )}

      <div className="space-y-3">
        {data?.items?.map((ev) => (
          <Link
            key={ev.id}
            to={`/app/ripple/${ev.id}`}
            className="block rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 hover:border-brand-400 transition-colors"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <SeverityBadge s={ev.severity} />
                  <span className="text-xs text-gray-400">{ev.event_type.replace(/_/g, " ")}</span>
                </div>
                <p className="font-medium text-gray-900 dark:text-white text-sm">{ev.title}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">{ev.summary}</p>
                {ev.affected_order_codes?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {ev.affected_order_codes.map(c => (
                      <span key={c} className="rounded bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 text-[10px] font-mono text-gray-600 dark:text-gray-400">{c}</span>
                    ))}
                  </div>
                )}
              </div>
              {ev.at_risk_paise > 0 && (
                <div className="shrink-0 text-right">
                  <p className="text-xs text-gray-400">at risk</p>
                  <p className="font-semibold text-red-600 dark:text-red-400 text-sm">
                    ₹{Math.round(ev.at_risk_paise / 100).toLocaleString("en-IN")}
                  </p>
                </div>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
