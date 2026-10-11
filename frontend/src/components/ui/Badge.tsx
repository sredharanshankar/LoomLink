import { clsx } from "clsx";

export type BadgeColor =
  | "gray" | "green" | "yellow" | "amber" | "red" | "blue" | "purple" | "orange" | "teal" | "brand";

const COLORS: Record<BadgeColor, { pill: string; dot: string }> = {
  gray:   { pill: "bg-gray-100 text-gray-700 ring-gray-500/15",         dot: "bg-gray-400" },
  green:  { pill: "bg-emerald-50 text-emerald-700 ring-emerald-600/20", dot: "bg-emerald-500" },
  yellow: { pill: "bg-amber-50 text-amber-800 ring-amber-600/25",       dot: "bg-amber-500" },
  amber:  { pill: "bg-amber-50 text-amber-800 ring-amber-600/25",       dot: "bg-amber-500" },
  red:    { pill: "bg-red-50 text-red-700 ring-red-600/20",             dot: "bg-red-500" },
  blue:   { pill: "bg-sky-50 text-sky-700 ring-sky-600/20",             dot: "bg-sky-500" },
  purple: { pill: "bg-violet-50 text-violet-700 ring-violet-600/20",    dot: "bg-violet-500" },
  orange: { pill: "bg-orange-50 text-orange-700 ring-orange-600/20",    dot: "bg-orange-500" },
  teal:   { pill: "bg-teal-50 text-teal-700 ring-teal-600/20",          dot: "bg-teal-500" },
  brand:  { pill: "bg-brand-50 text-brand-700 ring-brand-600/20",       dot: "bg-brand-500" },
};

interface BadgeProps {
  color?: BadgeColor;
  dot?: boolean;
  pulse?: boolean;
  children: React.ReactNode;
  className?: string;
}

const ACRONYMS = /\b(qc|po|gst|id)\b/gi;

function humanize(text: string) {
  const s = text.replace(/_/g, " ").replace(ACRONYMS, (m) => m.toUpperCase());
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export default function Badge({ color = "gray", dot = true, pulse, children, className }: BadgeProps) {
  const c = COLORS[color] ?? COLORS.gray;
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
        c.pill,
        className,
      )}
    >
      {dot && (
        <span className="relative flex h-1.5 w-1.5">
          {pulse && <span className={clsx("absolute inline-flex h-full w-full animate-ping rounded-full opacity-60", c.dot)} />}
          <span className={clsx("relative inline-flex h-1.5 w-1.5 rounded-full", c.dot)} />
        </span>
      )}
      {typeof children === "string" ? humanize(children) : children}
    </span>
  );
}
