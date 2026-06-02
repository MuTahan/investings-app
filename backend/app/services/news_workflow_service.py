"""AI news workflow: news -> impact -> affected stock -> committee -> recommendation.

For a symbol: score recent headlines for impact, aggregate net sentiment, fold in the
committee's recommendation, and produce an actionable report (what's happening, predicted
short/long impact, recommended action, confidence). Deterministic + cheap; reuses cached
news and the freshness-gated committee.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.news_impact import label, score_headline
from app.config import Settings
from app.core.exceptions import NotFound
from app.db.models.user import User
from app.domain.enums import Recommendation
from app.providers.container import ProviderContainer
from app.repositories.instrument_repo import InstrumentRepository
from app.schemas.news import NewsImpactItem, NewsImpactReport
from app.services.news_service import NewsService
from app.services.recommendation_service import RecommendationService

_BUY = {Recommendation.BUY, Recommendation.STRONG_BUY}
_BEAR = {Recommendation.WATCH, Recommendation.AVOID}


class NewsWorkflowService:
    def __init__(
        self, session: AsyncSession, providers: ProviderContainer, settings: Settings
    ) -> None:
        self._instruments = InstrumentRepository(session)
        self._news = NewsService(session, providers.market)
        self._recos = RecommendationService(session, providers, settings)

    async def analyze(self, user: User, symbol: str) -> NewsImpactReport:
        instrument = await self._instruments.get_by_symbol(symbol)
        if instrument is None:
            raise NotFound(f"Unknown symbol '{symbol}'.")

        articles = await self._news.list(symbol, "company", 12)
        items: list[NewsImpactItem] = []
        scores: list[int] = []
        for a in articles:
            s = score_headline(a.headline)
            scores.append(s)
            items.append(
                NewsImpactItem(
                    headline=a.headline,
                    url=a.url,
                    source=a.source,
                    published_at=a.published_at,
                    impact_score=s,
                    impact_label=label(s),
                )
            )

        net = round(sum(scores) / len(scores), 1) if scores else 0.0
        rec = await self._recos.get(user, symbol)
        long_term = (
            "bullish" if rec.rating in _BUY else "bearish" if rec.rating in _BEAR else "neutral"
        )
        summary = (
            f"{len(articles)} recent headlines, net {label(net)} sentiment ({net:+.0f}); "
            f"the committee rates {symbol.upper()} {rec.rating.value.replace('_', ' ')} "
            f"at {rec.confidence:.0f}% confidence."
        )
        return NewsImpactReport(
            symbol=symbol.upper(),
            article_count=len(articles),
            net_sentiment=net,
            sentiment_label=label(net),
            predicted_short_term=label(net),
            predicted_long_term=long_term,
            recommended_action=rec.rating,
            confidence=rec.confidence,
            summary=summary,
            items=items[:8],
        )

    @staticmethod
    def top_impact(articles_scores: list[int]) -> int:
        """Largest absolute impact among scored headlines (used to trigger alerts)."""
        return max((abs(s) for s in articles_scores), default=0)
