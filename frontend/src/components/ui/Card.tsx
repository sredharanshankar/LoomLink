import { clsx } from "clsx";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: boolean;
}

export default function Card({ children, className, padding = true }: CardProps) {
  return (
    <div className={clsx("bg-white rounded-lg border border-gray-200 shadow-sm", padding && "p-5", className)}>
      {children}
    </div>
  );
}