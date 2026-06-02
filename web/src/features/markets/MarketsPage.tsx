import { useState } from "react";
import { Link } from "react-router-dom";

import { isApiError } from "../../api/errors";
import { Input } from "../../components/ui/Input";
import { EmptyState, ErrorPanel, Spinner } from "../../components/ui/StatePanel";
import { useSearch, useTrending } from "../../hooks/useMarket";
import { changeColor, formatPercent } from "../../lib/format";
import { TRENDING_CATEGORIES } from "../../models/trending";
import { cn } from "../../lib/cn";
import { InstrumentRow } from "./InstrumentRow";

const POPULAR = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "SPY", "QQQ", "VOO"];

export function MarketsPage() {
  const [query, setQuery] = useState("");
  const showingSearch = query.trim().length >= 1;
  const search = useSearch(query);

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-semibold">Markets</h1>
        <p className="text-sm text-muted">US stocks &amp; ETFs</p>
      </header>

      <Input
        placeholder="Search symbol or company…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        aria-label="Search instruments"
      />

      {showingSearch ? (
        <section className="space-y-2">
          {search.isLoading && <Spinner />}
          {search.isError && (
            <ErrorPanel message={isApiError(search.error) ? search.error.message : "Search failed."} />
          )}
          {search.data && search.data.results.length === 0 && (
            <EmptyState title="No matches" hint="Try a different symbol or name." />
          )}
          {search.data?.results.map((instrument) => (
            <InstrumentRow key={instrument.id} instrument={instrument} />
          ))}
        </section>
      ) : (
        <>
          <TrendingSection />
          <section className="space-y-2">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">Popular</h2>
            <div className="flex flex-wrap gap-2">
              {POPULAR.map((symbol) => (
                <Link
                  key={symbol}
                  to={`/markets/${symbol}`}
                  className="rounded-lg border border-border bg-surface px-3 py-1.5 text-sm font-medium hover:border-primary"
                >
                  {symbol}
                </Link>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function TrendingSection() {
  const [category, setCategory] = useState<string>(TRENDING_CATEGORIES[0].key);
  const trending = useTrending(category);

  return (
    <section className="space-y-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">Trending</h2>
      <div className="flex flex-wrap gap-2">
        {TRENDING_CATEGORIES.map((c) => (
          <button
            key={c.key}
            onClick={() => setCategory(c.key)}
            className={cn(
              "rounded-full px-3 py-1 text-xs font-medium transition-colors",
              category === c.key ? "bg-primary text-white" : "bg-surface-2 text-muted hover:text-slate-200",
            )}
          >
            {c.label}
          </button>
        ))}
      </div>

      {trending.isLoading && <Spinner />}
      {trending.isError && (
        <ErrorPanel
          message={isApiError(trending.error) ? trending.error.message : "Could not load trending."}
        />
      )}
      {trending.data && trending.data.items.length === 0 && (
        <EmptyState title="Nothing trending here right now" />
      )}

      <div className="grid gap-2 sm:grid-cols-2">
        {trending.data?.items.map((item) => (
          <Link
            key={item.id}
            to={`/markets/${item.symbol}`}
            className="flex items-center justify-between rounded-lg border border-border bg-surface px-4 py-3 hover:border-primary"
          >
            <div className="min-w-0">
              <div className="font-semibold">{item.symbol}</div>
              <p className="truncate text-xs text-muted">{item.summary}</p>
            </div>
            <div className={cn("text-right text-sm", changeColor(item.change_pct))}>
              {formatPercent(item.change_pct)}
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
