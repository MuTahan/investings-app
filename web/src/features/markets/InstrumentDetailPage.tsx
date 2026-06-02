import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { isApiError } from "../../api/errors";
import { PriceChart } from "../../components/charts/PriceChart";
import { RatingBadge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card, CardHeader } from "../../components/ui/Card";
import { EmptyState, ErrorPanel, Spinner } from "../../components/ui/StatePanel";
import { useCandles, useInstrument, useQuote } from "../../hooks/useMarket";
import { useNews } from "../../hooks/useNews";
import { useRecommendation } from "../../hooks/useRecommendations";
import { useAddWatchlistItem } from "../../hooks/useWatchlist";
import { cn } from "../../lib/cn";
import {
  changeColor,
  formatCompact,
  formatCurrency,
  formatDate,
  formatPercent,
} from "../../lib/format";

function ytdDays(): number {
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 1);
  return Math.max(1, Math.ceil((now.getTime() - start.getTime()) / 86_400_000));
}

// Free tier is daily EOD only; intraday (1D/1W) needs premium data.
const PERIODS: { label: string; days: number }[] = [
  { label: "1M", days: 30 },
  { label: "3M", days: 90 },
  { label: "6M", days: 180 },
  { label: "YTD", days: ytdDays() },
  { label: "1Y", days: 365 },
  { label: "5Y", days: 1825 },
  { label: "Max", days: 3650 },
];

export function InstrumentDetailPage() {
  const { symbol = "" } = useParams();
  const [period, setPeriod] = useState("6M");
  const days = PERIODS.find((p) => p.label === period)?.days ?? 180;

  const instrument = useInstrument(symbol);
  const quote = useQuote(symbol);
  const candles = useCandles(symbol, "D", days);
  const news = useNews(symbol);
  const reco = useRecommendation(symbol);
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
            <Button>Full AI analysis</Button>
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
          <ErrorPanel message={isApiError(quote.error) ? quote.error.message : "Quote unavailable."} />
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
        <CardHeader
          title="Price"
          action={
            <div className="flex flex-wrap gap-1">
              {PERIODS.map((p) => (
                <button
                  key={p.label}
                  onClick={() => setPeriod(p.label)}
                  className={cn(
                    "rounded px-2 py-0.5 text-xs font-medium",
                    period === p.label ? "bg-primary text-white" : "text-muted hover:text-slate-200",
                  )}
                >
                  {p.label}
                </button>
              ))}
            </div>
          }
        />
        {candles.isLoading && <Spinner />}
        {candles.isError && (
          <ErrorPanel message={isApiError(candles.error) ? candles.error.message : "Chart unavailable."} />
        )}
        {candles.data && candles.data.candles.length > 0 ? (
          <PriceChart candles={candles.data.candles} />
        ) : (
          !candles.isLoading && <EmptyState title="No chart data" />
        )}
        <p className="mt-1 text-xs text-muted">Daily prices · intraday needs premium data.</p>
      </Card>

      <Card>
        <CardHeader
          title="AI analysis"
          action={
            <Link to={`/recommendations/${symbol}`} className="text-xs text-primary hover:underline">
              Details ›
            </Link>
          }
        />
        {reco.isLoading && <Spinner />}
        {reco.isError && (
          <p className="text-sm text-muted">
            Analysis unavailable.{" "}
            <Link to={`/recommendations/${symbol}`} className="text-primary hover:underline">
              Open full analysis
            </Link>
          </p>
        )}
        {reco.data && (
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <RatingBadge rating={reco.data.rating} />
              <span className="text-sm text-muted">
                {reco.data.confidence.toFixed(0)}% confidence · {reco.data.time_horizon} term
              </span>
            </div>
            {reco.data.suggested_action && <p className="text-sm">{reco.data.suggested_action}</p>}
            {reco.data.valuation && (
              <div className="grid grid-cols-3 gap-2 pt-1 text-xs">
                <Stat label="Fair value" value={formatCurrency(reco.data.valuation.fair_value)} />
                <Stat label="Target" value={formatCurrency(reco.data.valuation.target_price)} />
                <Stat label="Stop" value={formatCurrency(reco.data.valuation.stop_loss)} />
              </div>
            )}
          </div>
        )}
      </Card>

      <Card>
        <CardHeader title="News timeline" />
        {news.isLoading && <Spinner />}
        {news.data && news.data.items.length === 0 && <EmptyState title="No recent news" />}
        <ul className="space-y-3 border-l border-border pl-4">
          {news.data?.items.map((item) => (
            <li key={item.url} className="relative">
              <span className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full bg-primary" />
              <a href={item.url} target="_blank" rel="noreferrer" className="block hover:text-primary">
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
