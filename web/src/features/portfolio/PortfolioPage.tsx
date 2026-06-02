import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import { isApiError } from "../../api/errors";
import { Button } from "../../components/ui/Button";
import { Card, CardHeader } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { EmptyState, ErrorPanel, Spinner } from "../../components/ui/StatePanel";
import { useAddHolding, useDeleteHolding, usePortfolio } from "../../hooks/usePortfolio";
import { changeColor, formatCurrency, formatPercent } from "../../lib/format";

export function PortfolioPage() {
  const portfolio = usePortfolio();
  const addHolding = useAddHolding();
  const deleteHolding = useDeleteHolding();

  const [symbol, setSymbol] = useState("");
  const [quantity, setQuantity] = useState("");
  const [avgCost, setAvgCost] = useState("");

  const onAdd = (e: FormEvent) => {
    e.preventDefault();
    addHolding.mutate(
      { symbol, quantity: Number(quantity), avg_cost: Number(avgCost) },
      {
        onSuccess: () => {
          setSymbol("");
          setQuantity("");
          setAvgCost("");
        },
      },
    );
  };

  const summary = portfolio.data?.summary;

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Portfolio</h1>
        <p className="text-sm text-muted">Your holdings and performance</p>
      </header>

      {portfolio.isLoading && <Spinner />}
      {portfolio.isError && (
        <ErrorPanel
          message={isApiError(portfolio.error) ? portfolio.error.message : "Could not load portfolio."}
        />
      )}

      {summary && (
        <Card>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Metric label="Market value" value={formatCurrency(summary.market_value)} />
            <Metric
              label="Unrealized P/L"
              value={formatCurrency(summary.unrealized_pl)}
              className={changeColor(summary.unrealized_pl)}
              sub={formatPercent(summary.unrealized_pl_pct)}
            />
            <Metric label="Cost basis" value={formatCurrency(summary.cost_basis)} />
            <Metric label="Diversification" value={`${summary.diversification_score.toFixed(0)}/100`} />
          </div>
          {Object.keys(summary.sector_exposure).length > 0 && (
            <div className="mt-4 border-t border-border pt-3">
              <p className="mb-2 text-xs uppercase tracking-wide text-muted">Sector exposure</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(summary.sector_exposure)
                  .sort((a, b) => b[1] - a[1])
                  .map(([sector, weight]) => (
                    <span
                      key={sector}
                      className="rounded-full bg-surface-2 px-2.5 py-0.5 text-xs text-fg-soft"
                    >
                      {sector} {(weight * 100).toFixed(0)}%
                    </span>
                  ))}
              </div>
            </div>
          )}
        </Card>
      )}

      <Card>
        <CardHeader title="Add holding" />
        <form onSubmit={onAdd} className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Input
            placeholder="Symbol"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            required
          />
          <Input
            placeholder="Quantity"
            type="number"
            step="any"
            min="0"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            required
          />
          <Input
            placeholder="Avg cost"
            type="number"
            step="any"
            min="0"
            value={avgCost}
            onChange={(e) => setAvgCost(e.target.value)}
            required
          />
          <Button type="submit" loading={addHolding.isPending}>
            Add
          </Button>
        </form>
        {addHolding.isError && (
          <div className="mt-3">
            <ErrorPanel
              message={isApiError(addHolding.error) ? addHolding.error.message : "Could not add holding."}
            />
          </div>
        )}
      </Card>

      {portfolio.data && portfolio.data.holdings.length === 0 && (
        <EmptyState title="No holdings yet" hint="Add one above to see your performance." />
      )}

      <div className="space-y-2">
        {portfolio.data?.holdings.map((h) => (
          <div
            key={h.id}
            className="flex items-center justify-between rounded-lg border border-border bg-surface px-4 py-3"
          >
            <Link to={`/markets/${h.instrument.symbol}`} className="min-w-0">
              <div className="font-semibold">{h.instrument.symbol}</div>
              <p className="text-sm text-muted">
                {h.quantity} @ {formatCurrency(h.avg_cost)}
              </p>
            </Link>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div>{formatCurrency(h.market_value)}</div>
                <div className={`text-sm ${changeColor(h.unrealized_pl_pct)}`}>
                  {formatPercent(h.unrealized_pl_pct)}
                </div>
              </div>
              <Button
                variant="ghost"
                aria-label={`Remove ${h.instrument.symbol}`}
                onClick={() => deleteHolding.mutate(h.id)}
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

function Metric({
  label,
  value,
  sub,
  className,
}: {
  label: string;
  value: string;
  sub?: string;
  className?: string;
}) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className={`text-lg font-semibold ${className ?? ""}`}>{value}</p>
      {sub && <p className={`text-sm ${className ?? "text-muted"}`}>{sub}</p>}
    </div>
  );
}
