import { clsx } from "clsx";

export default function Spinner({ size = "md", className }: { size?: "sm" | "md" | "lg"; className?: string }) {
  const sz = { sm: "h-4 w-4", md: "h-6 w-6", lg: "h-10 w-10" }[size];
  return (
    <svg
      className={clsx("animate-spin text-brand-600", sz, className)}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
  );
}