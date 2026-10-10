import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { TrendingDown } from "lucide-react";
import { clsx } from "clsx";

interface LeakBreakdown {
  idle_paise: number;
  rework_paise: number;
  waste_paise: number;
  overtime_paise: number;
  total_paise: number;
}

function fmt(p: number) {
  return "₹" + Math.round(p / 100).toLocaleString("en-IN");
}

function Bar({ label, paise, total, color }: { label: string; paise: number; total: number; color: string }) {
  const pct = total > 0 ? Math.round((paise / total) * 100) : 0;
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-700 dark:text-gray-300">{label}</span>
        <span className="font-medium text-gray-900 dark:text-white">{fmt(paise)}</span>
      </div>
      <div className="h-2 rounded-full bg-gray-100 dark:bg-gray-800">
        <div className={clsx("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function LeakMeterPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery<LeakBreakdown>({
    queryKey: ["leak-today"],
    queryFn: () => api.get("/leak/today"),
    refetchInterval: 60_000,
  });

  return (
    <div className="p-6 max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <TrendingDown className="h-6 w-6 text-red-500" />
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white">{t("leak", "Leak Meter")}</h1>
      </div>

      {isLoading && <div className="h-48 rounded-xl bg-gray-100 dark:bg-gray-800 animate-pulse" />}

      {data && (
        <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6 space-y-5">
          <div className="text-center">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Today's leak</p>
            <p className="text-4xl font-bold text-red-600 dark:text-red-400 mt-1">{fmt(data.total_paise)}</p>
          </div>

          <div className="space-y-4">
            <Bar label="Idle machine time" paise={data.idle_paise} total={data.total_paise} color="bg-amber-400" />
            <Bar label="Rework cost" paise={data.rework_paise} total={data.total_paise} color="bg-orange-500" />
            <Bar label="Material waste" paise={data.waste_paise} total={data.total_paise} color="bg-red-500" />
            <Bar label="Overtime premium" paise={data.overtime_paise} total={data.total_paise} color="bg-purple-500" />
          </div>
        </div>
      )}
    </div>
  );
}
