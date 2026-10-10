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
    <div className={clsx("bg-white rounded-lg border border-gray-200 shadow-sm p-5", className)}>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
      {sub && (
        <p className={clsx("text-xs mt-1", trend === "up" ? "text-green-600" : trend === "down" ? "text-red-600" : "text-gray-500")}>
          {sub}
        </p>
      )}
    </div>
  );
}
