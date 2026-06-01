import { Link, useParams } from "react-router-dom";

import { isApiError } from "../../api/errors";
import { PriceChart } from "../../components/charts/PriceChart";
import { Button } from "../../components/ui/Button";
import { Card, CardHeader } from "../../components/ui/Card";
import { EmptyState, ErrorPanel, Spinner } from "../../components/ui/StatePanel";
import { useNews } from "../../hooks/useNews";
import { useCandles, useInstrument, useQuote } from "../../hooks/useMarket";
import { useAddWatchlistItem } from "../../hooks/useWatchlist";
import { changeColor, formatCompact, formatCurrency, formatDate, formatPercent } from "../../lib/format";

export function InstrumentDetailPage() {
  const { symbol = "" } = useParams();
  const instrument = useInstrument(symbol);
  const quote = useQuote(symbol);
  const candles = useCandles(symbol);
  const news = useNews(symbol);
  const addToWatchlist = useAddWatchlistItem();

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link to="/" className="text-sm text-muted hover:underline">
            ‹ Markets
          </Link>
          <h1 className="text-2xl font-semibold">{symbol.toUpperCase()}</h1>
          <p className="text-sm text-muted">{instrument.data?.name ?? ""}</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            loading={addToWatchlist.isPending}
            onClick={() => addToWatchlist.mutate(symbol)}
          >
            {addToWatchlist.isSuccess ? "Added ✓" : "+ Watchlist"}
          </Button>
          <Link to={`/recommendations/${symbol}`}>
            <Button>AI Recommendation</Button>
          </Link>
        </div>
      </header>

      {addToWatchlist.isError && (
        <ErrorPanel
          message={
            isApiError(addToWatchlist.error)
              ? addToWatchlist.error.message
              : "Could not add to watchlist."
          }
        />
      )}

      <Card>
        {quote.isLoading && <Spinner />}
        {quote.isError && (
          <ErrorPanel
            message={isApiError(quote.error) ? quote.error.message : "Quote unavailable."}
          />
        )}
        {quote.data && (
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <div className="text-3xl font-semibold">{formatCurrency(quote.data.price)}</div>
              <div className={changeColor(quote.data.change_pct)}>
                {formatCurrency(quote.data.change)} ({formatPercent(quote.data.change_pct)})
              </div>
            </div>
            <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm sm:grid-cols-4">
              <Stat label="Open" value={formatCurrency(quote.data.open)} />
              <Stat label="High" value={formatCurrency(quote.data.high)} />
              <Stat label="Low" value={formatCurrency(quote.data.low)} />
              <Stat label="Vol" value={formatCompact(quote.data.volume)} />
            </dl>
          </div>
        )}
      </Card>

      <Card>
        <CardHeader title="Price (6 months)" />
        {candles.isLoading && <Spinner />}
        {candles.isError && (
          <ErrorPanel
            message={isApiError(candles.error) ? candles.error.message : "Chart unavailable."}
          />
        )}
        {candles.data && candles.data.candles.length > 0 ? (
          <PriceChart candles={candles.data.candles} />
        ) : (
          !candles.isLoading && <EmptyState title="No chart data" />
        )}
      </Card>

      <Card>
        <CardHeader title="News" />
        {news.isLoading && <Spinner />}
        {news.data && news.data.items.length === 0 && <EmptyState title="No recent news" />}
        <ul className="space-y-3">
          {news.data?.items.map((item) => (
            <li key={item.url}>
              <a
                href={item.url}
                target="_blank"
                rel="noreferrer"
                className="block hover:text-primary"
              >
                <p className="text-sm font-medium">{item.headline}</p>
                <p className="text-xs text-muted">
                  {item.source ?? "News"} · {formatDate(item.published_at)}
                </p>
              </a>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-muted">{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
