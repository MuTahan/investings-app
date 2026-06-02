import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "../../lib/cn";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Adds a subtle lift + border highlight on hover (use for clickable cards). */
  interactive?: boolean;
  /** Remove default padding (for cards that manage their own layout). */
  flush?: boolean;
}

export function Card({ className, interactive, flush, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border bg-surface shadow-card",
        !flush && "p-4 sm:p-5",
        interactive &&
          "cursor-pointer transition-all duration-150 hover:-translate-y-0.5 hover:border-border-strong hover:shadow-lift",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ title, action }: { title: ReactNode; action?: ReactNode }) {
  return (
    <div className="mb-3 flex items-center justify-between gap-3">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-muted">{title}</h2>
      {action}
    </div>
  );
}
