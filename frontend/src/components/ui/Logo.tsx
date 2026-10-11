import { useId } from "react";
import { clsx } from "clsx";

export function LogoMark({ className }: { className?: string }) {
  const gradientId = useId();
  return (
    <svg viewBox="0 0 32 32" className={clsx("h-8 w-8", className)} aria-hidden="true">
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#818cf8" />
          <stop offset="1" stopColor="#4f46e5" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8" fill={`url(#${CSS.escape(gradientId)})`} />
      {/* warp threads */}
      <g stroke="white" strokeWidth="2.4" strokeLinecap="round" opacity="0.95">
        <path d="M11 8v16" />
        <path d="M16 8v16" />
        <path d="M21 8v16" />
      </g>
      {/* weft threads, interlaced over/under */}
      <g stroke="#c7d2fe" strokeWidth="2.4" strokeLinecap="round">
        <path d="M8 12.5h1.6M12.4 12.5h2.2M17.4 12.5h2.2M22.4 12.5H24" />
        <path d="M8 19.5h1.6M12.4 19.5h2.2M17.4 19.5h2.2M22.4 19.5H24" />
      </g>
    </svg>
  );
}

export default function Logo({ subtitle = true, className }: { subtitle?: boolean; className?: string }) {
  return (
    <div className={clsx("flex items-center gap-2.5", className)}>
      <LogoMark />
      <div className="leading-tight">
        <p className="text-[15px] font-semibold tracking-tight">LoomLink</p>
        {subtitle && <p className="text-[11px] opacity-60">Everest Textile Mills</p>}
      </div>
    </div>
  );
}
