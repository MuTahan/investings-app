import { Link, useParams } from "react-router-dom";

import { isApiError } from "../../api/errors";
import { RatingBadge } from "../../components/ui/Badge";
import { Card, CardHeader } from "../../components/ui/Card";
import { EmptyState, ErrorPanel, Spinner } from "../../components/ui/StatePanel";
import { useRecommendation } from "../../hooks/useRecommendations";
import type { RecommendationDetail } from "../../models/recommendation";
import { formatDate } from "../../lib/format";

export function RecommendationPage() {
  const { symbol = "" } = useParams();
  const reco = useRecommendation(symbol);

  return (
    <div className="space-y-5">
      <header>
        <Link to={`/markets/${symbol}`} className="text-sm text-muted hover:underline">
          ‹ {symbol.toUpperCase()}
        </Link>
        <h1 className="text-2xl font-semibold">AI Recommendation</h1>
      </header>

      {reco.isLoading && <Spinner />}

      {reco.isError &&
        (isApiError(reco.error) && reco.error.code === "not_implemented" ? (
          <Card>
            <EmptyState
              title="The AI Investment Committee arrives in Phase 4"
              hint="Six specialist agents (news, technical, fundamental, macro, risk, portfolio-fit) anchored to deterministic math, with a Claude 'Chair' issuing the final call — fully explained and personalized to your risk profile."
            />
          </Card>
        ) : (
          <ErrorPanel
            message={isApiError(reco.error) ? reco.error.message : "Could not load recommendation."}
          />
        ))}

      {reco.data && <RecommendationView reco={reco.data} />}
    </div>
  );
}

function RecommendationView({ reco }: { reco: RecommendationDetail }) {
  return (
    <div className="space-y-4">
      <Card>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <RatingBadge rating={reco.rating} />
            <span className="text-sm text-muted">
              {reco.confidence.toFixed(0)}% confidence · {reco.time_horizon} term
            </span>
          </div>
          <span className="text-xs text-muted">{formatDate(reco.generated_at)}</span>
        </div>
        {reco.suggested_action && <p className="mt-3 text-sm">{reco.suggested_action}</p>}
        {reco.chair_rationale && (
          <p className="mt-2 border-l-2 border-primary pl-3 text-sm text-muted">
            {reco.chair_rationale}
          </p>
        )}
      </Card>

      {reco.reasons.length > 0 && (
        <Card>
          <CardHeader title="Why" />
          <ul className="space-y-2">
            {reco.reasons.map((r) => (
              <li key={r.label}>
                <p className="text-sm font-medium">{r.label}</p>
                <p className="text-sm text-muted">{r.detail}</p>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {reco.risks.length > 0 && (
        <Card>
          <CardHeader title="Risks" />
          <ul className="space-y-2">
            {reco.risks.map((r) => (
              <li key={r.label}>
                <p className="text-sm font-medium text-amber-400">
                  {r.label} <span className="text-xs text-muted">({r.severity})</span>
                </p>
                <p className="text-sm text-muted">{r.detail}</p>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card>
        <CardHeader title="Agent breakdown" />
        <div className="space-y-2">
          {reco.agent_breakdown.map((a) => (
            <div key={a.agent} className="rounded-lg border border-border p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium capitalize">{a.agent.replace("_", " ")}</span>
                <span className="text-sm text-muted">
                  {a.score != null ? a.score.toFixed(0) : a.risk_level ?? "—"}
                  {a.signal ? ` · ${a.signal}` : ""}
                </span>
              </div>
              {a.explanation && <p className="mt-1 text-sm text-muted">{a.explanation}</p>}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
