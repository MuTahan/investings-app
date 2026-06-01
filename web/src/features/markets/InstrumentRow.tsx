import { Link } from "react-router-dom";

import { Badge } from "../../components/ui/Badge";
import type { Instrument } from "../../models/market";

export function InstrumentRow({ instrument }: { instrument: Instrument }) {
  return (
    <Link
      to={`/markets/${instrument.symbol}`}
      className="flex items-center justify-between rounded-lg border border-border bg-surface px-4 py-3 transition-colors hover:border-primary"
    >
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-semibold">{instrument.symbol}</span>
          <Badge className="bg-surface-2 text-muted">{instrument.type.toUpperCase()}</Badge>
        </div>
        <p className="truncate text-sm text-muted">{instrument.name}</p>
      </div>
      <span className="text-muted">›</span>
    </Link>
  );
}
