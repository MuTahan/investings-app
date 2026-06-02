import type { ReactNode } from "react";

import { cn } from "../../lib/cn";

export function Spinner() {
  return (
    <div className="flex justify-center py-10" role="status" aria-label="Loading">
      <span className="h-6 w-6 animate-spin rounded-full border-2 border-border border-t-primary" />
    </div>
  );
}

/** A single shimmer placeholder block. Compose several to mimic real layout. */
export function Skeleton({ className }: { className?: string }) {
  return <span className={cn("skeleton block", className)} aria-hidden />;
}

export function ErrorPanel({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="flex items-start gap-2.5 rounded-xl border border-bear/30 bg-bear/10 px-4 py-3 text-sm text-bear"
    >
      <svg
        className="mt-0.5 h-4 w-4 shrink-0"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden
      >
        <circle cx="12" cy="12" r="10" />
        <path d="M12 8v4M12 16h.01" />
      </svg>
      <span>{message}</span>
    </div>
  );
}

export function EmptyState({ title, hint, icon }: { title: string; hint?: ReactNode; icon?: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-border-strong px-4 py-12 text-center">
      {icon && <div className="mx-auto mb-3 flex justify-center text-faint">{icon}</div>}
      <p className="text-sm font-medium text-fg-soft">{title}</p>
      {hint && <p className="mt-1 text-sm text-muted">{hint}</p>}
    </div>
  );
}
