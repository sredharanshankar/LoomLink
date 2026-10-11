import { clsx } from "clsx";
import { TrendingUp, TrendingDown } from "lucide-react";

type Tone = "brand" | "emerald" | "amber" | "red" | "sky" | "violet" | "gray";

const TONES: Record<Tone, string> = {
  brand: "bg-brand-50 text-brand-600 ring-brand-600/10",
  emerald: "bg-emerald-50 text-emerald-600 ring-emerald-600/10",
  amber: "bg-amber-50 text-amber-600 ring-amber-600/10",
  red: "bg-red-50 text-red-600 ring-red-600/10",
  sky: "bg-sky-50 text-sky-600 ring-sky-600/10",
  violet: "bg-violet-50 text-violet-600 ring-violet-600/10",
  gray: "bg-gray-100 text-gray-600 ring-gray-600/10",
};

interface Props {
  label: string;
  value: string | number;
  sub?: string;
  trend?: "up" | "down" | "neutral";
  icon?: React.ElementType;
  tone?: Tone;
  className?: string;
}

export default function KpiTile({ label, value, sub, trend, icon: Icon, tone = "brand", className }: Props) {
  return (
    <div
      className={clsx(
        "card group relative overflow-hidden p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lift",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-[13px] font-medium text-gray-500">{label}</p>
        {Icon && (
          <span className={clsx("flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ring-1 ring-inset", TONES[tone])}>
            <Icon className="h-[18px] w-[18px]" strokeWidth={2} />
          </span>
        )}
      </div>
      <p className="tabular mt-2 text-[28px] font-semibold leading-none tracking-tight text-gray-900">{value}</p>
      {(sub || (trend && trend !== "neutral")) && (
        <p
          className={clsx(
            "mt-3 flex items-center gap-1 text-xs font-medium",
            trend === "up" ? "text-emerald-600" : trend === "down" ? "text-red-600" : "text-gray-500",
          )}
        >
          {trend === "up" && <TrendingUp className="h-3.5 w-3.5" />}
          {trend === "down" && <TrendingDown className="h-3.5 w-3.5" />}
          {sub ?? (trend === "up" ? "Healthy" : "Needs attention")}
        </p>
      )}
    </div>
  );
}
