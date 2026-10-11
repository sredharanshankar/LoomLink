import { clsx } from "clsx";

interface Props {
  className?: string;
  rows?: number;
}

function SkeletonLine({ className }: { className?: string }) {
  return <div className={clsx("animate-pulse bg-gray-200 dark:bg-gray-800 rounded-md", className)} />;
}

export default function Skeleton({ className, rows = 3 }: Props) {
  return (
    <div className={clsx("space-y-3", className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonLine key={i} className={i === 0 ? "h-5 w-2/3" : "h-4 w-full"} />
      ))}
    </div>
  );
}

export function SkeletonRow() {
  return (
    <div className="animate-pulse flex items-center gap-4 py-3">
      <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded-md w-1/4" />
      <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded-md w-1/3" />
      <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded-md w-1/6 ml-auto" />
    </div>
  );
}
