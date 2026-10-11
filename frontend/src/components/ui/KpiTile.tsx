import { clsx } from "clsx";

interface Props {
  label: string;
  value: string | number;
  sub?: string;
  trend?: "up" | "down" | "neutral";
  className?: string;
}

export default function KpiTile({ label, value, sub, trend, className }: Props) {
  return (
    <div className={clsx(
      "bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm p-5 transition-shadow hover:shadow-md",
      className
    )}>
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</p>
      <p className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white mt-1.5">{value}</p>
      {sub && (
        <p className={clsx(
          "text-xs mt-1.5 font-medium",
          trend === "up"   ? "text-emerald-600 dark:text-emerald-400" :
          trend === "down" ? "text-red-500 dark:text-red-400" :
                             "text-gray-500 dark:text-gray-400"
        )}>
          {sub}
        </p>
      )}
    </div>
  );
}
