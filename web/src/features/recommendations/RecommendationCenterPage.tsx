import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { isApiError } from "../../api/errors";
import { RecommendationCardView } from "../../components/RecommendationCardView";
import { Card } from "../../components/ui/Card";
import { EmptyState, ErrorPanel, Spinner } from "../../components/ui/StatePanel";
import { useRecommendationCenter } from "../../hooks/useRecommendations";
import type { RecommendationCard, RecommendationCenter } from "../../models/recommendation";

const SECTIONS: { key: keyof RecommendationCenter; label: string }[] = [
  { key: "top_picks", label: "Top AI Picks" },
  { key: "short_term", label: "Short-term opportunities" },
  { key: "long_term", label: "Long-term picks" },
  { key: "trending", label: "Trending opportunities" },
  { key: "personalized", label: "Personalized for you" },
];

export function RecommendationCenterPage() {
  const [horizon, setHorizon] = useState("");
  const [risk, setRisk] = useState("");
  const [type, setType] = useState("");
  const [minConf, setMinConf] = useState("");

  const filters = useMemo(() => {
    const f: Record<string, string> = {};
    if (horizon) f.horizon = horizon;
    if (risk) f.risk = risk;
    if (type) f.type = type;
    if (minConf) f.min_confidence = minConf;
    return f;
  }, [horizon, risk, type, minConf]);

  const center = useRecommendationCenter(filters);
  const data = center.data;
  const empty =
    data && SECTIONS.every((s) => (data[s.key] as RecommendationCard[]).length === 0);

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Recommendations</h1>
        <p className="text-sm text-muted">AI picks across your watchlist &amp; portfolio</p>
      </header>

      <Card>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Select label="Horizon" value={horizon} onChange={setHorizon} options={["short", "medium", "long"]} />
          <Select label="Risk" value={risk} onChange={setRisk} options={["low", "medium", "high"]} />
          <Select
            label="Rating"
            value={type}
            onChange={setType}
            options={["STRONG_BUY", "BUY", "HOLD", "WATCH", "AVOID"]}
          />
          <label className="block">
            <span className="mb-1 block text-sm text-muted">Min confidence</span>
            <input
              type="number"
              min="0"
              max="100"
              value={minConf}
              onChange={(e) => setMinConf(e.target.value)}
              placeholder="0"
              className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm outline-none focus:border-primary"
            />
          </label>
        </div>
      </Card>

      {center.isLoading && <Spinner />}
      {center.isError && (
        <ErrorPanel
          message={isApiError(center.error) ? center.error.message : "Could not load recommendations."}
        />
      )}

      {empty && (
        <EmptyState
          title="Nothing to recommend yet"
          hint={
            <Link to="/" className="text-primary hover:underline">
              Add symbols to your watchlist or portfolio
            </Link>
          }
        />
      )}

      {data &&
        SECTIONS.map((section) => {
          const cards = data[section.key] as RecommendationCard[];
          if (cards.length === 0) return null;
          return (
            <section key={section.key} className="space-y-2">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">
                {section.label}
              </h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {cards.map((card) => (
                  <RecommendationCardView key={card.symbol} card={card} />
                ))}
              </div>
            </section>
          );
        })}
    </div>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm text-muted">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm capitalize text-fg outline-none focus:border-primary"
      >
        <option value="">Any</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o.replace("_", " ")}
          </option>
        ))}
      </select>
    </label>
  );
}
