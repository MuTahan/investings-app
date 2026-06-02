import type { InputHTMLAttributes, ReactNode } from "react";
import { forwardRef, useId } from "react";

import { cn } from "../../lib/cn";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  /** Optional decorative icon rendered on the left (e.g. a search glyph). */
  leftIcon?: ReactNode;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, hint, leftIcon, id, className, ...props },
  ref,
) {
  const autoId = useId();
  const inputId = id ?? autoId;
  return (
    <div className="block">
      {label && (
        <label htmlFor={inputId} className="mb-1.5 block text-sm font-medium text-fg-soft">
          {label}
        </label>
      )}
      <div className="relative">
        {leftIcon && (
          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted">
            {leftIcon}
          </span>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            "w-full rounded-lg border border-border bg-surface-2 px-3 py-2.5 text-sm text-fg outline-none transition-colors placeholder:text-faint",
            "focus:border-primary focus:ring-2 focus:ring-primary/30",
            leftIcon ? "pl-9" : "",
            className,
          )}
          {...props}
        />
      </div>
      {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
    </div>
  );
});
