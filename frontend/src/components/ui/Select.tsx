import { forwardRef } from "react";
import { clsx } from "clsx";

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
  placeholder?: string;
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, placeholder, className, ...props }, ref) => (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-[13px] font-medium text-gray-700">{label}</label>}
      <select
        ref={ref}
        className={clsx("input-base h-10 pr-8", error && "border-red-500", className)}
        {...props}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  )
);
Select.displayName = "Select";
export default Select;
