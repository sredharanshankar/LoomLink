import { Outlet } from "react-router-dom";
import { Activity, ShieldCheck, Zap } from "lucide-react";
import Logo from "../ui/Logo";

const HIGHLIGHTS = [
  { icon: Activity, title: "Live floor visibility", body: "Every loom, jigger and stenter, tracked metre by metre." },
  { icon: Zap, title: "Ripple impact alerts", body: "See which orders a breakdown puts at risk, before buyers ask." },
  { icon: ShieldCheck, title: "Roll-level traceability", body: "From yarn batch to dispatched roll, with a passport for each." },
];

export default function PublicShell() {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="theme-light relative hidden w-[46%] max-w-[640px] flex-col justify-between overflow-hidden bg-[#0b0f1e] p-12 text-white lg:flex">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.35]"
          style={{
            backgroundImage:
              "repeating-linear-gradient(90deg, rgba(129,140,248,0.10) 0 1px, transparent 1px 22px), repeating-linear-gradient(0deg, rgba(129,140,248,0.07) 0 1px, transparent 1px 22px)",
            maskImage: "radial-gradient(80% 70% at 30% 30%, black, transparent)",
          }}
        />
        <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-indigo-500/25 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-40 right-0 h-96 w-96 rounded-full bg-violet-500/20 blur-3xl" />

        <Logo className="relative" />

        <div className="relative">
          <h2 className="max-w-md text-4xl font-semibold leading-[1.15] tracking-tight">
            The operating system for your{" "}
            <span className="bg-gradient-to-r from-indigo-300 to-violet-300 bg-clip-text text-transparent">textile mill</span>.
          </h2>
          <p className="mt-4 max-w-md text-[15px] leading-relaxed text-white/60">
            Orders, yarn, production, quality, dispatch and payroll, connected in one place.
          </p>

          <ul className="mt-10 space-y-5">
            {HIGHLIGHTS.map(({ icon: Icon, title, body }) => (
              <li key={title} className="flex gap-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/[0.06] ring-1 ring-inset ring-white/10">
                  <Icon className="h-5 w-5 text-indigo-300" />
                </span>
                <div>
                  <p className="text-sm font-medium text-white">{title}</p>
                  <p className="mt-0.5 text-sm text-white/50">{body}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-xs text-white/35">© {new Date().getFullYear()} Everest Textile Mills · LoomLink</p>
      </aside>

      <main className="flex flex-1 flex-col items-center justify-center p-6 sm:p-10">
        <Logo className="mb-10 text-gray-900 lg:hidden" />
        <div className="w-full max-w-sm animate-fade-up">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
