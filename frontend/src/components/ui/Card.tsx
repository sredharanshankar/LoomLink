import { clsx } from "clsx";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: boolean;
  title?: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
}

export default function Card({ children, className, padding = true, title, description, actions }: CardProps) {
  return (
    <div className={clsx("card", className)}>
      {(title || actions) && (
        <div className="flex items-start justify-between gap-4 px-5 pt-4 pb-3 border-b border-gray-100">
          <div className="min-w-0">
            {title && <h2 className="text-[15px] font-semibold text-gray-900">{title}</h2>}
            {description && <p className="mt-0.5 text-sm text-gray-500">{description}</p>}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className={clsx(padding && "p-5")}>{children}</div>
    </div>
  );
}
