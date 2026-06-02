import { Link } from "react-router-dom";

import { formatCurrency } from "../lib/format";
import type { RecommendationCard } from "../models/recommendation";
import { RatingBadge } from "./ui/Badge";
import { Card } from "./ui/Card";

export function RecommendationCardView({ card }: { card: RecommendationCard }) {
  const v = card.valuation;
  return (
    <Card className="h-full transition-all duration-150 hover:-translate-y-0.5 hover:border-border-strong hover:shadow-lift">
      <div className="flex items-start justify-between gap-2">
        <Link to={`/recommendations/${card.symbol}`} className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold">{card.symbol}</span>
            <RatingBadge rating={card.rating} />
          </div>
          <p className="truncate text-xs text-muted">{card.name}</p>
        </Link>
        <div className="shrink-0 text-right text-sm">
          <div className="font-semibold tabular">{card.confidence.toFixed(0)}%</div>
          <div className="text-xs capitalize text-muted">{card.time_horizon}</div>
        </div>
      </div>
      {card.reason && <p className="mt-2 line-clamp-2 text-sm text-muted">{card.reason}</p>}
      {v && (
        <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
          <Level label="Fair" value={formatCurrency(v.fair_value)} />
          <Level label="Target" value={formatCurrency(v.target_price)} className="text-bull" />
          <Level label="Stop" value={formatCurrency(v.stop_loss)} className="text-bear" />
        </div>
      )}
    </Card>
  );
}

function Level({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div>
      <div className="text-muted">{label}</div>
      <div className={`font-medium ${className ?? ""}`}>{value}</div>
    </div>
  );
}
