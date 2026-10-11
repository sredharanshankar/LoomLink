import Badge, { type BadgeColor } from "./Badge";

const TONE: Record<string, BadgeColor> = {
  running: "green", in_progress: "green", passed: "green", green: "green", active: "green",
  confirmed: "blue", in_production: "brand",
  idle: "gray", queued: "gray", draft: "gray", closed: "gray", depleted: "gray", exhausted: "gray", offline: "gray",
  pending_qc: "yellow", paused: "yellow", rework: "yellow", amber: "yellow", low_stock: "yellow",
  breakdown: "red", rejected: "red", cancelled: "red", red: "red", overdue: "red",
  maintenance: "purple",
  changeover: "orange", quarantined: "orange",
  completed: "teal", dispatched: "teal",
};

const LIVE = new Set(["running", "in_progress", "breakdown"]);

interface Props {
  status: string;
  label?: string;
  size?: "sm" | "md";
}

export default function StatusPill({ status, label, size = "md" }: Props) {
  const key = status ?? "";
  return (
    <Badge color={TONE[key] ?? "gray"} pulse={LIVE.has(key)} className={size === "md" ? "text-[13px]" : undefined}>
      {label ?? (key || "unknown").replace(/_/g, " ")}
    </Badge>
  );
}
