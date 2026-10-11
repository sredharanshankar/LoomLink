import { clsx } from "clsx";

type Color = "gray" | "green" | "yellow" | "red" | "blue" | "purple" | "orange";

const COLORS: Record<Color, string> = {
  gray:   "bg-gray-100   text-gray-700   dark:bg-gray-800   dark:text-gray-300",
  green:  "bg-green-100  text-green-700  dark:bg-green-900/50  dark:text-green-400",
  yellow: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300",
  red:    "bg-red-100    text-red-700    dark:bg-red-900/40    dark:text-red-400",
  blue:   "bg-blue-100   text-blue-700   dark:bg-blue-900/40   dark:text-blue-400",
  purple: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-400",
  orange: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-400",
};

interface BadgeProps {
  color?: Color;
  children: React.ReactNode;
  className?: string;
}

export default function Badge({ color = "gray", children, className }: BadgeProps) {
  return (
    <span className={clsx(
      "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
      COLORS[color],
      className
    )}>
      {children}
    </span>
  );
}