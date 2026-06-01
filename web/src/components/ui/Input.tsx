import type { InputHTMLAttributes } from "react";
import { forwardRef } from "react";

import { cn } from "../../lib/cn";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, id, className, ...props },
  ref,
) {
  return (
    <label className="block">
      {label && <span className="mb-1 block text-sm text-muted">{label}</span>}
      <input
        ref={ref}
        id={id}
        className={cn(
          "w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-slate-100 outline-none placeholder:text-muted focus:border-primary",
          className,
        )}
        {...props}
      />
    </label>
  );
});
