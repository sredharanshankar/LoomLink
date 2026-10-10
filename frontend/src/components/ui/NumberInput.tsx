import { forwardRef } from "react";
import { clsx } from "clsx";

interface NumberInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  unit?: string;
  error?: string;
}

const NumberInput = forwardRef<HTMLInputElement, NumberInputProps>(
  ({ label, unit, error, className, ...props }, ref) => (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm font-medium text-gray-700">{label}</label>}
      <div className="relative flex items-center">
        <input
          ref={ref}
          type="number"
          className={clsx(
            "h-10 rounded-md border px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-600 w-full",
            unit ? "pr-12" : "",
            error ? "border-red-500" : "border-gray-300",
            className
          )}
          {...props}
        />
        {unit && (
          <span className="absolute right-3 text-sm text-gray-500 pointer-events-none">{unit}</span>
        )}
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  )
);
NumberInput.displayName = "NumberInput";
export default NumberInput;
