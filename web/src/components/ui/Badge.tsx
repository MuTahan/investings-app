import type { ReactNode } from "react";

import type { Rating } from "../../models/enums";
import { cn } from "../../lib/cn";

export function Badge({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
        className,
      )}
    >
      {children}
    </span>
  );
}

const RATING_STYLES: Record<Rating, string> = {
  STRONG_BUY: "bg-bull/20 text-bull",
  BUY: "bg-bull/15 text-bull",
  HOLD: "bg-slate-500/20 text-slate-300",
  WATCH: "bg-amber-500/20 text-amber-400",
  AVOID: "bg-bear/20 text-bear",
};

export function RatingBadge({ rating }: { rating: Rating }) {
  return <Badge className={RATING_STYLES[rating]}>{rating.replace("_", " ")}</Badge>;
}
