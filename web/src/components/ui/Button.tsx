import type { ButtonHTMLAttributes } from "react";

import { cn } from "../../lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-primary text-primary-fg shadow-sm hover:bg-primary-hover active:scale-[0.98]",
  secondary:
    "bg-surface-2 text-fg ring-1 ring-inset ring-border hover:bg-surface-3 active:scale-[0.98]",
  ghost: "bg-transparent text-fg-soft hover:bg-surface-2 hover:text-fg active:scale-[0.98]",
  danger: "bg-bear text-white shadow-sm hover:brightness-110 active:scale-[0.98]",
};

const SIZES: Record<Size, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex select-none items-center justify-center gap-2 rounded-lg font-semibold transition-[background-color,transform,filter,box-shadow] duration-150 disabled:pointer-events-none disabled:opacity-50",
        SIZES[size],
        VARIANTS[variant],
        className,
      )}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && (
        <span
          aria-hidden
          className="h-4 w-4 animate-spin rounded-full border-2 border-transparent border-t-current"
        />
      )}
      {children}
    </button>
  );
}
