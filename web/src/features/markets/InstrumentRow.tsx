import { Link } from "react-router-dom";

import { Badge } from "../../components/ui/Badge";
import type { Instrument } from "../../models/market";

export function InstrumentRow({ instrument }: { instrument: Instrument }) {
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
      <span className="text-faint transition-transform group-hover:translate-x-0.5 group-hover:text-primary">
        ›
      </span>
    </Link>
  );
}
