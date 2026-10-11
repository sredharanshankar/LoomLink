import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  Activity, AlertTriangle, ArrowRight, ClipboardCheck, Clock, Cog, Factory, PackageX, Plus,
  Ruler, ShoppingBag, Truck, Users, Wrench,
} from "lucide-react";
import { clsx } from "clsx";
import { useAuth } from "../../lib/auth";
import { can } from "../../lib/permissions";
import { api } from "../../lib/api";
import { formatPaise, formatCm, formatRelative } from "../../lib/format";
import { qk } from "../../lib/query-keys";
import KpiTile from "../../components/ui/KpiTile";
import PageHeader from "../../components/ui/PageHeader";
import Skeleton from "../../components/ui/Skeleton";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";

interface DashboardData {
  order_pipeline?: Record<string, number>;
  overdue_orders?: number;
  orders_due_7d?: number;
  today_output_cm?: number;
  cash_in_mtd_paise?: number;
  receivables_paise?: number;
  overdue_receivables_paise?: number;
  low_stock_count?: number;
  workers_on_floor?: number;
  jobs_running?: number;
  rolls_in_qc?: number;
  dispatches_today?: number;
  active_jobs?: { stage: string; total: number; running: number; paused: number; blocked: number }[];
  today_output?: { stage: string; produced_cm: number }[];
}

interface FloorMachine {
  id: string;
  code: string;
  name: string;
  stage: string;
  status: string;
  status_changed_at: string;
}

interface TodayRow {
  stage: string;
  output_cm: number;
  waste_cm: number;
}

const STAGES = [
  { key: "spinning", label: "Spinning", color: "#8b5cf6" },
  { key: "weaving", label: "Weaving", color: "#0ea5e9" },
  { key: "dyeing", label: "Dyeing", color: "#14b8a6" },
  { key: "finishing", label: "Finishing", color: "#f59e0b" },
];

const MACHINE_STATES = [
  { key: "running", label: "Running", bar: "bg-emerald-500" },
  { key: "idle", label: "Idle", bar: "bg-gray-300" },
  { key: "maintenance", label: "Maintenance", bar: "bg-violet-500" },
  { key: "breakdown", label: "Breakdown", bar: "bg-red-500" },
];

const linkCls = "text-sm font-medium text-brand-600 hover:text-brand-700";

function greeting() {
  const h = Number(new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata", hour: "numeric", hour12: false }));
  return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
}

function OutputChart({ rows }: { rows: { stage: string; label: string; color: string; metres: number }[] }) {
  const total = rows.reduce((s, r) => s + r.metres, 0);
  return (
    <Card
      title="Output by stage"
      description={`${total.toLocaleString("en-IN", { maximumFractionDigits: 0 })} m produced today`}
      actions={<Link to="/app/production" className={linkCls}>Production →</Link>}
      className="lg:col-span-2"
    >
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 8, right: 8, left: -12, bottom: 0 }} barCategoryGap="28%">
            <CartesianGrid vertical={false} stroke="rgb(var(--c-gray-200))" strokeDasharray="3 3" />
            <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: "rgb(var(--c-gray-500))", fontSize: 12 }} />
            <YAxis
              tickLine={false}
              axisLine={false}
              tick={{ fill: "rgb(var(--c-gray-500))", fontSize: 12 }}
              tickFormatter={(v: number) => (v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v))}
            />
            <Tooltip
              cursor={{ fill: "rgb(var(--c-gray-100))" }}
              formatter={(v: number) => [`${v.toLocaleString("en-IN", { maximumFractionDigits: 1 })} m`, "Output"]}
              contentStyle={{
                background: "rgb(var(--surface))",
                border: "1px solid rgb(var(--c-gray-200))",
                borderRadius: 10,
                boxShadow: "0 8px 20px -6px rgb(16 24 40 / 0.2)",
                fontSize: 13,
              }}
              labelStyle={{ color: "rgb(var(--c-gray-900))", fontWeight: 600 }}
              itemStyle={{ color: "rgb(var(--c-gray-700))" }}
            />
            <Bar dataKey="metres" radius={[6, 6, 0, 0]} maxBarSize={56}>
              {rows.map((r) => <Cell key={r.stage} fill={r.color} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

function MachineHealth({ machines }: { machines: FloorMachine[] }) {
  const counts: Record<string, number> = Object.fromEntries(
    MACHINE_STATES.map((s) => [s.key, machines.filter((m) => m.status === s.key).length]),
  );
  const attention = machines.filter((m) => m.status === "breakdown" || m.status === "maintenance");
  const total = machines.length || 1;
  const utilised = Math.round((counts.running / total) * 100);

  return (
    <Card
      title="Machine health"
      description={`${counts.running} of ${machines.length} machines running`}
      actions={<Badge color={utilised >= 60 ? "green" : utilised >= 40 ? "yellow" : "red"}>{utilised}% utilised</Badge>}
    >
      <div className="flex h-2.5 gap-0.5 overflow-hidden rounded-full">
        {MACHINE_STATES.map((s) =>
          counts[s.key] ? (
            <div key={s.key} className={clsx("h-full first:rounded-l-full last:rounded-r-full", s.bar)} style={{ width: `${(counts[s.key] / total) * 100}%` }} />
          ) : null,
        )}
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2.5">
        {MACHINE_STATES.map((s) => (
          <div key={s.key} className="flex items-center justify-between text-sm">
            <dt className="flex items-center gap-2 text-gray-600">
              <span className={clsx("h-2 w-2 rounded-full", s.bar)} />
              {s.label}
            </dt>
            <dd className="tabular font-semibold text-gray-900">{counts[s.key]}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-5 border-t border-gray-100 pt-4">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-gray-500">Needs attention</p>
        {attention.length === 0 ? (
          <p className="text-sm text-gray-500">All machines are healthy.</p>
        ) : (
          <ul className="space-y-1">
            {attention.map((m) => (
              <li key={m.id}>
                <Link to={`/app/machines/${m.id}`} className="group -mx-2 flex items-center gap-3 rounded-lg px-2 py-1.5 transition-colors hover:bg-gray-50">
                  <span
                    className={clsx(
                      "flex h-7 w-7 shrink-0 items-center justify-center rounded-md",
                      m.status === "breakdown" ? "bg-red-50 text-red-600" : "bg-violet-50 text-violet-600",
                    )}
                  >
                    {m.status === "breakdown" ? <AlertTriangle className="h-3.5 w-3.5" /> : <Wrench className="h-3.5 w-3.5" />}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-gray-900">{m.code} · {m.name}</span>
                    <span className="block text-xs text-gray-500">
                      <span className="capitalize">{m.status}</span> · {formatRelative(m.status_changed_at)}
                    </span>
                  </span>
                  <ArrowRight className="h-4 w-4 text-gray-300 transition-transform group-hover:translate-x-0.5" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Card>
  );
}

function OrderPipeline({ data }: { data: DashboardData }) {
  const p = data.order_pipeline ?? {};
  const stages = [
    { key: "draft", label: "Draft", bar: "bg-gray-300" },
    { key: "pending_approval", label: "Awaiting approval", bar: "bg-orange-500" },
    { key: "confirmed", label: "Confirmed", bar: "bg-sky-500" },
    { key: "in_production", label: "In production", bar: "bg-brand-500" },
    { key: "qc", label: "In QC", bar: "bg-amber-500" },
    { key: "ready", label: "Ready to ship", bar: "bg-emerald-500" },
  ].filter((s) => p[s.key] != null);
  const max = Math.max(1, ...stages.map((s) => p[s.key] ?? 0));

  return (
    <Card
      title="Order pipeline"
      description={`${data.orders_due_7d ?? 0} due in the next 7 days`}
      actions={<Link to="/app/orders" className={linkCls}>Orders →</Link>}
    >
      <div className="space-y-3.5">
        {stages.map((s) => (
          <div key={s.key}>
            <div className="mb-1.5 flex justify-between text-sm">
              <span className="text-gray-600">{s.label}</span>
              <span className="tabular font-semibold text-gray-900">{p[s.key]}</span>
            </div>
            <div className="h-1.5 rounded-full bg-gray-100">
              <div className={clsx("h-full rounded-full", s.bar)} style={{ width: `${((p[s.key] ?? 0) / max) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
      {(data.overdue_orders ?? 0) > 0 && (
        <div className="mt-5 flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-inset ring-red-600/15">
          <Clock className="h-4 w-4 shrink-0" />
          <span><strong className="font-semibold">{data.overdue_orders}</strong> orders past their due date</span>
        </div>
      )}
    </Card>
  );
}

function CashCard({ data }: { data: DashboardData }) {
  const rows = [
    { label: "Collected this month", value: data.cash_in_mtd_paise, tone: "text-emerald-600" },
    { label: "Receivables", value: data.receivables_paise, tone: "text-gray-900" },
    { label: "Overdue receivables", value: data.overdue_receivables_paise, tone: "text-red-600" },
  ].filter((r): r is { label: string; value: number; tone: string } => r.value != null);
  return (
    <Card title="Cash position" description="Month to date" actions={<Link to="/app/finance" className={linkCls}>Finance →</Link>}>
      <dl className="divide-y divide-gray-100">
        {rows.map((r) => (
          <div key={r.label} className="flex items-baseline justify-between gap-4 py-3 first:pt-0 last:pb-0">
            <dt className="text-sm text-gray-600">{r.label}</dt>
            <dd className={clsx("tabular text-lg font-semibold tracking-tight", r.tone)}>{formatPaise(r.value)}</dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}

function ActionItems({ data }: { data: DashboardData }) {
  const items = [
    { show: (data.rolls_in_qc ?? 0) > 0, icon: ClipboardCheck, tone: "bg-amber-50 text-amber-600", to: "/app/quality",
      title: `${data.rolls_in_qc} rolls awaiting inspection`, body: "Quality control queue" },
    { show: (data.low_stock_count ?? 0) > 0, icon: PackageX, tone: "bg-red-50 text-red-600", to: "/app/inventory",
      title: `${data.low_stock_count} yarn types low on stock`, body: "Reorder before production stalls" },
    { show: (data.overdue_orders ?? 0) > 0, icon: Clock, tone: "bg-orange-50 text-orange-600", to: "/app/orders",
      title: `${data.overdue_orders} overdue orders`, body: "Review promised dates with buyers" },
    { show: true, icon: Truck, tone: "bg-sky-50 text-sky-600", to: "/app/dispatch",
      title: `${data.dispatches_today ?? 0} dispatches today`, body: "Outbound shipments" },
  ].filter((i) => i.show);

  return (
    <Card title="Action items" description="What needs a decision today" padding={false}>
      <ul className="divide-y divide-gray-100">
        {items.map(({ icon: Icon, tone, to, title, body }) => (
          <li key={title}>
            <Link to={to} className="group flex items-center gap-3 px-5 py-3.5 transition-colors hover:bg-gray-50">
              <span className={clsx("flex h-9 w-9 shrink-0 items-center justify-center rounded-lg", tone)}>
                <Icon className="h-[18px] w-[18px]" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-medium text-gray-900">{title}</span>
                <span className="block text-xs text-gray-500">{body}</span>
              </span>
              <ArrowRight className="h-4 w-4 text-gray-300 transition-transform group-hover:translate-x-0.5 group-hover:text-gray-500" />
            </Link>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function TileSkeletons() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => <div key={i} className="card p-5"><Skeleton rows={2} /></div>)}
    </div>
  );
}

export default function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();

  const isBuyer = user?.role === "buyer";
  const isOwnerView = user?.role === "owner" || user?.role === "manager" || user?.role === "accounts";
  const canSeeFloor = can(user?.role, "production:read");

  const { data, isLoading } = useQuery({
    queryKey: qk.dashboard(),
    queryFn: () => api.get<DashboardData>(isOwnerView ? "/dashboard/owner" : "/dashboard/production"),
    enabled: !isBuyer,
    refetchInterval: 30_000,
  });

  const floor = useQuery({
    queryKey: [...qk.production.machines(), "floor"],
    queryFn: () => api.get<{ machines: FloorMachine[] }>("/production/floor"),
    enabled: canSeeFloor,
    refetchInterval: 15_000,
  });

  const today = useQuery({
    queryKey: [...qk.production.machines(), "today"],
    queryFn: () => api.get<{ items: TodayRow[] }>("/production/today"),
    enabled: canSeeFloor,
    refetchInterval: 30_000,
  });

  const firstName = user?.full_name?.split(" ")[0] ?? "";
  const dateLabel = new Date().toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata", weekday: "long", day: "numeric", month: "long" });

  const chartRows = STAGES.map((s) => ({
    stage: s.key,
    label: s.label,
    color: s.color,
    metres:
      (today.data?.items.find((r) => r.stage === s.key)?.output_cm ??
        data?.today_output?.find((r) => r.stage === s.key)?.produced_cm ??
        0) / 100,
  }));

  if (isBuyer) {
    return (
      <div className="p-6 lg:p-8">
        <PageHeader eyebrow={dateLabel} title={`${greeting()}, ${firstName}`} subtitle="Track your orders as they move through the mill." />
        <Card>
          <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="font-semibold text-gray-900">Your orders</p>
              <p className="text-sm text-gray-500">Production status, rolls and dispatches in one place.</p>
            </div>
            <Link to="/app/buyer-portal" className="btn-primary">
              View my orders <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader
        eyebrow={dateLabel}
        title={`${greeting()}, ${firstName}`}
        subtitle={t("dashboardSubtitle", "Here is what is happening across the mill right now.")}
        actions={
          <>
            {canSeeFloor && (
              <Link to="/app/floor" className="btn-secondary">
                <Factory className="h-4 w-4" /> Floor view
              </Link>
            )}
            {can(user?.role, "orders:write") && (
              <Link to="/app/orders/new" className="btn-primary">
                <Plus className="h-4 w-4" /> New order
              </Link>
            )}
          </>
        }
      />

      {isLoading ? (
        <TileSkeletons />
      ) : isOwnerView ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KpiTile
            label="Today's output"
            value={formatCm(today.data ? today.data.items.reduce((s, r) => s + r.output_cm, 0) : data?.today_output_cm ?? 0)}
            icon={Ruler}
            tone="brand"
            sub="Across all stages"
          />
          <KpiTile label="Jobs running" value={data?.jobs_running ?? 0} icon={Activity} tone="emerald" sub={`${data?.workers_on_floor ?? 0} workers on the floor`} />
          <KpiTile
            label="Orders due in 7 days"
            value={data?.orders_due_7d ?? 0}
            icon={ShoppingBag}
            tone="sky"
            trend={(data?.overdue_orders ?? 0) > 0 ? "down" : "neutral"}
            sub={(data?.overdue_orders ?? 0) > 0 ? `${data?.overdue_orders} already overdue` : "None overdue"}
          />
          <KpiTile label="Rolls in QC" value={data?.rolls_in_qc ?? 0} icon={ClipboardCheck} tone="amber" sub="Awaiting inspection" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {(data?.active_jobs ?? []).map((j) => (
            <KpiTile
              key={j.stage}
              label={j.stage.charAt(0).toUpperCase() + j.stage.slice(1)}
              value={`${j.running} running`}
              icon={Cog}
              tone={j.blocked ? "red" : "brand"}
              sub={`${j.total} total${j.paused ? ` · ${j.paused} paused` : ""}${j.blocked ? ` · ${j.blocked} blocked` : ""}`}
            />
          ))}
          {data?.workers_on_floor != null && <KpiTile label="Workers on floor" value={data.workers_on_floor} icon={Users} tone="emerald" />}
        </div>
      )}

      {canSeeFloor && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {today.isLoading ? <div className="card p-5 lg:col-span-2"><Skeleton rows={6} /></div> : <OutputChart rows={chartRows} />}
          {floor.isLoading ? <div className="card p-5"><Skeleton rows={6} /></div> : <MachineHealth machines={floor.data?.machines ?? []} />}
        </div>
      )}

      {isOwnerView && data && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <OrderPipeline data={data} />
          {can(user?.role, "finance:read") && <CashCard data={data} />}
          <ActionItems data={data} />
        </div>
      )}
    </div>
  );
}
