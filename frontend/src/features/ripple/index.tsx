import { lazy, Suspense, createElement, Fragment } from "react";
import type { RouteObject } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { AlertTriangle, TrendingDown, Clock } from "lucide-react";
import { clsx } from "clsx";

const RippleInboxPage = lazy(() => import("./RippleInboxPage"));
const RippleEventPage = lazy(() => import("./RippleEventPage"));
const LeakMeterPage = lazy(() => import("./LeakMeterPage"));

function Lazy({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<div className="p-6 animate-pulse h-32 bg-gray-100 dark:bg-gray-800 rounded-xl" />}>{children}</Suspense>;
}

export const rippleRoutes: RouteObject[] = [
  { path: "ripple",      element: <Lazy><RippleInboxPage /></Lazy> },
  { path: "ripple/:id",  element: <Lazy><RippleEventPage /></Lazy> },
  { path: "leak",        element: <Lazy><LeakMeterPage /></Lazy> },
  { path: "what-if",     element: <Lazy><div className="p-6 text-gray-500">What-if Simulator — coming soon</div></Lazy> },
];

// ---------------------------------------------------------------------------
// Widgets used by Dashboard and other pages
// ---------------------------------------------------------------------------

interface RippleEvent {
  id: string;
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  at_risk_paise: number;
}

export function OrderHealthBadge({
  health,
  slackMinutes,
  size = "md",
}: {
  orderId: string;
  health?: "green" | "amber" | "red" | null;
  slackMinutes?: number | null;
  size?: "sm" | "md";
}) {
  if (!health) return null;
  return (
    <span
      className={clsx("inline-flex items-center gap-1 rounded-full font-medium", {
        "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300": health === "green",
        "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300": health === "amber",
        "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300": health === "red",
        "px-2 py-0.5 text-xs": size === "sm",
        "px-2.5 py-1 text-sm": size === "md",
      })}
      aria-label={`Order health: ${health}`}
    >
      <span className={clsx("h-1.5 w-1.5 rounded-full", {
        "bg-green-500": health === "green",
        "bg-amber-500": health === "amber",
        "bg-red-500": health === "red",
      })} />
      {health}
      {slackMinutes != null && slackMinutes < 1440 && (
        <span className="opacity-70">{slackMinutes < 60 ? `${slackMinutes}m` : `${Math.round(slackMinutes / 60)}h`}</span>
      )}
    </span>
  );
}

export function PromiseDatePanel({
  draft,
  onUseDate,
}: {
  draft: { buyer_id?: string; fabric_type_id?: string; quantity_cm?: number; requested_date?: string; priority?: string };
  onUseDate?: (isoDate: string) => void;
}) {
  const { data, isLoading } = useQuery({
    queryKey: ["ripple-promise-date", draft],
    queryFn: () => api.post<{ earliest_date: string; confidence: string; warning?: string }>("/ripple/promise-date", draft),
    enabled: !!(draft.fabric_type_id && draft.quantity_cm),
    staleTime: 30_000,
  });

  if (!draft.fabric_type_id || !draft.quantity_cm) return null;
  if (isLoading) return <div className="h-10 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />;
  if (!data) return null;

  return (
    <div className="rounded-lg border border-brand-200 dark:border-brand-800 bg-brand-50 dark:bg-brand-950 p-3 text-sm">
      <p className="text-brand-700 dark:text-brand-300">
        Earliest: <strong>{data.earliest_date}</strong> ({data.confidence} confidence)
      </p>
      {data.warning && <p className="text-amber-600 dark:text-amber-400 text-xs mt-0.5">{data.warning}</p>}
      {onUseDate && (
        <button
          onClick={() => onUseDate(data.earliest_date)}
          className="mt-1.5 text-xs text-brand-700 dark:text-brand-300 underline"
        >
          Use this date
        </button>
      )}
    </div>
  );
}

export function RippleFloor({
  compact = false,
  onMachineClick,
}: {
  compact?: boolean;
  onMachineClick?: (machineId: string) => void;
}) {
  const { data } = useQuery<{ items: Array<{ id: string; code: string; status: string; stage: string; floor_x: number; floor_y: number }> }>({
    queryKey: ["machines"],
    queryFn: () => api.get("/machines?limit=20"),
    staleTime: 15_000,
  });

  const machines = data?.items ?? [];

  return (
    <div className={clsx("rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900", compact ? "p-3" : "p-5")}>
      {!compact && <h3 className="font-semibold text-gray-900 dark:text-white mb-3 text-sm">Floor Overview</h3>}
      <div className="grid grid-cols-7 gap-2">
        {machines.map((m) => (
          <button
            key={m.id}
            onClick={() => onMachineClick?.(m.id)}
            className={clsx("rounded-lg border p-2 text-center transition-colors", {
              "border-green-300 bg-green-50 dark:border-green-700 dark:bg-green-950": m.status === "running",
              "border-amber-300 bg-amber-50 dark:border-amber-700 dark:bg-amber-950": m.status === "idle",
              "border-red-300 bg-red-50 dark:border-red-700 dark:bg-red-950": m.status === "breakdown",
              "border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800": !["running","idle","breakdown"].includes(m.status),
            })}
          >
            <span className="block text-[10px] font-mono font-semibold text-gray-700 dark:text-gray-300">{m.code}</span>
            <span className={clsx("block text-[9px] mt-0.5", {
              "text-green-600 dark:text-green-400": m.status === "running",
              "text-amber-600 dark:text-amber-400": m.status === "idle",
              "text-red-600 dark:text-red-400": m.status === "breakdown",
              "text-gray-500": !["running","idle","breakdown"].includes(m.status),
            })}>{m.status}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export function RippleInboxWidget({ limit = 3 }: { limit?: number }) {
  const { data } = useQuery<{ items: RippleEvent[] }>({
    queryKey: ["ripple-events"],
    queryFn: () => api.get("/ripple/events"),
    staleTime: 30_000,
  });

  const events = data?.items?.slice(0, limit) ?? [];

  if (!events.length) return null;

  return (
    <div className="space-y-2">
      {events.map((ev) => (
        <div key={ev.id} className="flex items-center gap-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2">
          <AlertTriangle className={clsx("h-4 w-4 shrink-0", {
            "text-red-500": ev.severity === "critical" || ev.severity === "high",
            "text-amber-500": ev.severity === "medium",
            "text-blue-500": ev.severity === "low",
          })} />
          <span className="flex-1 text-sm text-gray-700 dark:text-gray-300 truncate">{ev.title}</span>
          {ev.at_risk_paise > 0 && (
            <span className="shrink-0 text-xs font-medium text-red-600 dark:text-red-400">
              ₹{Math.round(ev.at_risk_paise / 100).toLocaleString("en-IN")}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

export function LeakMeterWidget({ compact = false }: { compact?: boolean }) {
  const { data } = useQuery<{ total_paise: number; idle_paise: number; rework_paise: number }>({
    queryKey: ["leak-today"],
    queryFn: () => api.get("/leak/today"),
    staleTime: 60_000,
  });

  if (!data) return null;

  return (
    <div className={clsx("rounded-xl border border-red-100 dark:border-red-900 bg-red-50 dark:bg-red-950/40", compact ? "p-3" : "p-4")}>
      <div className="flex items-center gap-2 mb-1">
        <TrendingDown className="h-4 w-4 text-red-500" />
        <span className="text-xs font-semibold text-red-700 dark:text-red-300 uppercase tracking-wide">Today's Leak</span>
      </div>
      <p className="text-2xl font-bold text-red-600 dark:text-red-400">
        ₹{Math.round(data.total_paise / 100).toLocaleString("en-IN")}
      </p>
      {!compact && (
        <p className="text-xs text-red-500 dark:text-red-400 mt-0.5">
          Idle ₹{Math.round(data.idle_paise / 100).toLocaleString("en-IN")} · Rework ₹{Math.round(data.rework_paise / 100).toLocaleString("en-IN")}
        </p>
      )}
    </div>
  );
}

export function IdleHunterWidget({ limit = 3 }: { limit?: number }) {
  const { data } = useQuery<Array<{ machine_code: string; idle_minutes: number; suggestion: string }>>({
    queryKey: ["ripple-idle-hunter"],
    queryFn: () => api.get("/ripple/idle-hunter"),
    staleTime: 30_000,
  });

  const items = (data ?? []).slice(0, limit);
  if (!items.length) return null;

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div key={item.machine_code} className="flex items-center gap-2 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/40 px-3 py-2">
          <Clock className="h-4 w-4 shrink-0 text-amber-500" />
          <div className="flex-1 min-w-0">
            <span className="text-sm font-medium text-amber-800 dark:text-amber-200">{item.machine_code}</span>
            <span className="text-xs text-amber-600 dark:text-amber-400 ml-2">idle {item.idle_minutes}m</span>
            <p className="text-xs text-amber-700 dark:text-amber-300 truncate">{item.suggestion}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export function RippleLiveToaster(): JSX.Element {
  return createElement(Fragment);
}
