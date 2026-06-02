import { Link } from "react-router-dom";

import { isApiError } from "../../api/errors";
import { Button } from "../../components/ui/Button";
import { EmptyState, ErrorPanel, Spinner } from "../../components/ui/StatePanel";
import { useRemoveWatchlistItem, useWatchlist } from "../../hooks/useWatchlist";
import { changeColor, formatCurrency, formatPercent } from "../../lib/format";

export function WatchlistPage() {
  const watchlist = useWatchlist();
  const removeItem = useRemoveWatchlistItem();

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Watchlist</h1>
        <p className="text-sm text-muted">Symbols you're tracking</p>
      </header>

      {watchlist.isLoading && <Spinner />}
      {watchlist.isError && (
        <ErrorPanel
          message={isApiError(watchlist.error) ? watchlist.error.message : "Could not load watchlist."}
        />
      )}

      {watchlist.data && watchlist.data.items.length === 0 && (
        <EmptyState
          title="Your watchlist is empty"
          hint={
            <Link to="/" className="text-primary hover:underline">
              Browse markets to add symbols
            </Link>
          }
        />
      )}

      <div className="space-y-2">
        {watchlist.data?.items.map((item) => (
          <div
            key={item.instrument.id}
            className="flex items-center justify-between rounded-lg border border-border bg-surface px-4 py-3"
          >
            <Link to={`/markets/${item.instrument.symbol}`} className="min-w-0">
              <div className="font-semibold">{item.instrument.symbol}</div>
              <p className="truncate text-sm text-muted">{item.instrument.name}</p>
            </Link>
            <div className="flex items-center gap-4">
              {item.quote && (
                <div className="text-right">
                  <div>{formatCurrency(item.quote.price)}</div>
                  <div className={`text-sm ${changeColor(item.quote.change_pct)}`}>
                    {formatPercent(item.quote.change_pct)}
                  </div>
                </div>
              )}
              <Button
                variant="ghost"
                aria-label={`Remove ${item.instrument.symbol}`}
                onClick={() => removeItem.mutate(item.instrument.id)}
              >
                ✕
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
