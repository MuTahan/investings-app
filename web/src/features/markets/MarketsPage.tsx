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
        <h1 className="text-2xl font-bold tracking-tight">Markets</h1>
        <p className="text-sm text-muted">US stocks &amp; ETFs · AI-rated</p>
      </header>

      <Input
        placeholder="Search symbol or company…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        aria-label="Search instruments"
        leftIcon={
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <circle cx="11" cy="11" r="7" />
            <path d="M21 21l-4-4" />
          </svg>
        }
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
            <h2 className="text-xs font-semibold uppercase tracking-wider text-muted">Popular</h2>
            <div className="flex flex-wrap gap-2">
              {POPULAR.map((symbol) => (
                <Link
                  key={symbol}
                  to={`/markets/${symbol}`}
                  className="rounded-lg border border-border bg-surface px-3 py-1.5 text-sm font-semibold shadow-card transition-colors hover:border-primary hover:text-primary"
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
      <h2 className="text-xs font-semibold uppercase tracking-wider text-muted">Trending</h2>
      <div className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1 sm:flex-wrap sm:overflow-visible">
        {TRENDING_CATEGORIES.map((c) => (
          <button
            key={c.key}
            onClick={() => setCategory(c.key)}
            className={cn(
              "shrink-0 rounded-full px-3 py-1.5 text-xs font-semibold transition-colors",
              category === c.key
                ? "bg-primary text-primary-fg shadow-sm"
                : "bg-surface-2 text-muted ring-1 ring-inset ring-border hover:text-fg",
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
            className="group flex items-center justify-between gap-3 rounded-xl border border-border bg-surface px-4 py-3 shadow-card transition-all duration-150 hover:-translate-y-0.5 hover:border-border-strong hover:shadow-lift"
          >
            <div className="min-w-0">
              <div className="font-semibold">{item.symbol}</div>
              <p className="truncate text-xs text-muted">{item.summary}</p>
            </div>
            <div className={cn("shrink-0 text-right text-sm font-semibold tabular", changeColor(item.change_pct))}>
              {formatPercent(item.change_pct)}
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
