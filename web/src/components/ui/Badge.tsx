import type { ReactNode } from "react";

import type { Rating } from "../../models/enums";
import { cn } from "../../lib/cn";

export function Badge({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold",
        className,
      )}
    >
      {children}
    </span>
  );
}

const RATING_STYLES: Record<Rating, string> = {
  STRONG_BUY: "bg-bull/15 text-bull ring-1 ring-inset ring-bull/30",
  BUY: "bg-bull/10 text-bull ring-1 ring-inset ring-bull/20",
  HOLD: "bg-surface-3 text-muted ring-1 ring-inset ring-border-strong",
  WATCH: "bg-warn/15 text-warn ring-1 ring-inset ring-warn/30",
  AVOID: "bg-bear/15 text-bear ring-1 ring-inset ring-bear/30",
};

const RATING_DOT: Record<Rating, string> = {
  STRONG_BUY: "bg-bull",
  BUY: "bg-bull",
  HOLD: "bg-muted",
  WATCH: "bg-warn",
  AVOID: "bg-bear",
};

export function RatingBadge({ rating }: { rating: Rating }) {
  return (
    <Badge className={RATING_STYLES[rating]}>
      <span className={cn("h-1.5 w-1.5 rounded-full", RATING_DOT[rating])} aria-hidden />
      {rating.replace("_", " ")}
    </Badge>
  );
}
