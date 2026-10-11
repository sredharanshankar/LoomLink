import { forwardRef } from "react";
import { clsx } from "clsx";

type Variant = "primary" | "secondary" | "danger" | "ghost" | "success";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

const BASE =
  "inline-flex items-center justify-center gap-2 rounded-lg font-medium whitespace-nowrap select-none transition-all duration-150 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 focus-visible:ring-offset-surface disabled:opacity-50 disabled:pointer-events-none";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-brand-600 text-white shadow-sm shadow-brand-600/20 hover:bg-brand-700",
  secondary: "bg-white border border-gray-300 text-gray-700 shadow-sm hover:bg-gray-50 hover:border-gray-400/70",
  danger: "bg-red-600 text-white shadow-sm shadow-red-600/20 hover:bg-red-700",
  success: "bg-emerald-600 text-white shadow-sm shadow-emerald-600/20 hover:bg-emerald-700",
  ghost: "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
};

const SIZES: Record<Size, string> = {
  sm: "h-8 px-3 text-[13px]",
  md: "h-10 px-4 text-sm",
  lg: "h-11 px-6 text-[15px]",
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", loading, children, className, disabled, ...props }, ref) => (
    <button
      ref={ref}
      className={clsx(BASE, VARIANTS[variant], SIZES[size], className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      )}
      {children}
    </button>
  )
);
Button.displayName = "Button";
export default Button;
