import { useState } from "react";
import { Link } from "react-router-dom";

import { Input } from "../../components/ui/Input";
import { EmptyState, ErrorPanel, Spinner } from "../../components/ui/StatePanel";
import { useSearch } from "../../hooks/useMarket";
import { isApiError } from "../../api/errors";
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
      )}
    </div>
  );
}
