import { clsx } from "clsx";

const COLOR: Record<string, string> = {
  running: "bg-green-100 text-green-800",
  in_progress: "bg-green-100 text-green-800",
  confirmed: "bg-blue-100 text-blue-800",
  in_production: "bg-indigo-100 text-indigo-800",
  passed: "bg-green-100 text-green-800",
  green: "bg-green-100 text-green-800",
  active: "bg-green-100 text-green-800",

  idle: "bg-slate-100 text-slate-700",
  queued: "bg-slate-100 text-slate-700",
  draft: "bg-slate-100 text-slate-700",
  pending_qc: "bg-yellow-100 text-yellow-800",
  paused: "bg-yellow-100 text-yellow-800",
  rework: "bg-yellow-100 text-yellow-800",
  amber: "bg-yellow-100 text-yellow-800",
  low_stock: "bg-yellow-100 text-yellow-800",

  breakdown: "bg-red-100 text-red-800",
  rejected: "bg-red-100 text-red-800",
  cancelled: "bg-red-100 text-red-800",
  red: "bg-red-100 text-red-800",
  overdue: "bg-red-100 text-red-800",

  maintenance: "bg-purple-100 text-purple-800",
  changeover: "bg-orange-100 text-orange-800",

  completed: "bg-teal-100 text-teal-800",
  dispatched: "bg-teal-100 text-teal-800",
  closed: "bg-gray-100 text-gray-600",
  depleted: "bg-gray-100 text-gray-600",
  quarantined: "bg-orange-100 text-orange-800",
  exhausted: "bg-gray-100 text-gray-500",
  offline: "bg-gray-800 text-gray-100",
};

interface Props {
  status: string;
  label?: string;
  size?: "sm" | "md";
}

export default function StatusPill({ status, label, size = "md" }: Props) {
  const color = COLOR[status ?? ""] ?? "bg-gray-100 text-gray-700";
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full font-medium",
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-0.5 text-sm",
        color
      )}
    >
      {label ?? (status ?? "unknown").replace(/_/g, " ")}
    </span>
  );
}
