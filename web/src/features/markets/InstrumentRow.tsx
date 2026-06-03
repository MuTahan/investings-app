import { Link } from "react-router-dom";

import { Badge } from "../../components/ui/Badge";
import { useQuote } from "../../hooks/useMarket";
import { changeColor, formatCurrency, formatPercent } from "../../lib/format";
import type { Instrument } from "../../models/market";

export function InstrumentRow({ instrument }: { instrument: Instrument }) {
  const quote = useQuote(instrument.symbol);
  return (
    <Link
      to={`/markets/${instrument.symbol}`}
      className="group flex items-center justify-between gap-3 rounded-xl border border-border bg-surface px-4 py-3 shadow-card transition-all duration-150 hover:-translate-y-0.5 hover:border-border-strong hover:shadow-lift"
    >
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-semibold">{instrument.symbol}</span>
          <Badge className="bg-surface-2 text-muted ring-1 ring-inset ring-border">
            {instrument.type.toUpperCase()}
          </Badge>
        </div>
        <p className="truncate text-sm text-muted">{instrument.name}</p>
      </div>
      <div className="flex items-center gap-3">
        {quote.data ? (
          <div className="text-right">
            <div className="text-sm font-semibold tabular">{formatCurrency(quote.data.price)}</div>
            <div className={`text-xs font-medium tabular ${changeColor(quote.data.change_pct)}`}>
              {formatPercent(quote.data.change_pct)}
            </div>
          </div>
        ) : quote.isLoading ? (
          <span className="skeleton h-8 w-16 rounded-md" aria-hidden />
        ) : null}
        <span className="text-faint transition-transform group-hover:translate-x-0.5 group-hover:text-primary">
          ›
        </span>
      </div>
    </Link>
  );
}
