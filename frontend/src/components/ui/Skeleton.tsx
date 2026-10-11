import { clsx } from "clsx";

interface Props {
  className?: string;
  rows?: number;
}

function SkeletonLine({ className }: { className?: string }) {
  return (
    <div className={clsx("relative overflow-hidden rounded-md bg-gray-100", className)}>
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-gray-200/70 to-transparent" />
    </div>
  );
}

export default function Skeleton({ className, rows = 3 }: Props) {
  return (
    <div className={clsx("space-y-3", className)} aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonLine key={i} className={i === 0 ? "h-5 w-2/3" : "h-4 w-full"} />
      ))}
    </div>
  );
}

export function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 py-3">
      <SkeletonLine className="h-4 w-1/4" />
      <SkeletonLine className="h-4 w-1/3" />
      <SkeletonLine className="ml-auto h-4 w-1/6" />
    </div>
  );
}
