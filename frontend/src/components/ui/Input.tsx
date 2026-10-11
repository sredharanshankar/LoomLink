import { forwardRef } from "react";
import { clsx } from "clsx";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  icon?: React.ElementType;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, icon: Icon, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-[13px] font-medium text-gray-700">
            {label}
          </label>
        )}
        <div className="relative">
          {Icon && <Icon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />}
          <input
            ref={ref}
            id={inputId}
            aria-invalid={!!error || undefined}
            className={clsx(
              "input-base h-10",
              Icon && "pl-9",
              error && "border-red-500 focus:border-red-500 focus:ring-red-500/15",
              className,
            )}
            {...props}
          />
        </div>
        {error ? <p className="text-xs text-red-600">{error}</p> : hint && <p className="text-xs text-gray-500">{hint}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";
export default Input;
