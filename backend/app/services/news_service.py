from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ProviderError
from app.db.models.news import NewsItem
from app.providers.router import MarketDataRouter
from app.repositories.instrument_repo import InstrumentRepository
from app.repositories.news_repo import NewsRepository
from app.schemas.news import NewsItemOut


class NewsService:
    def __init__(self, session: AsyncSession, market: MarketDataRouter) -> None:
        self._repo = NewsRepository(session)
        self._instruments = InstrumentRepository(session)
        self._market = market

    async def list(self, symbol: str | None, category: str, limit: int = 20) -> list[NewsItemOut]:
        instrument = await self._instruments.get_by_symbol(symbol) if symbol else None
        try:
            articles = await self._market.get_news(symbol, category, limit)
        except ProviderError:
            articles = []

        if articles:
            await self._persist(articles, instrument_id=instrument.id if instrument else None)
            return [
                NewsItemOut(
                    headline=a.headline,
                    summary=a.summary,
                    url=a.url,
                    source=a.source,
                    published_at=a.published_at,
                    category=a.category,
                )
                for a in articles
            ]

        # Fallback to anything we've previously stored.
        stored = await self._repo.list_for_instrument(
            instrument.id if instrument else None, category if not symbol else None, limit
        )
        return [
            NewsItemOut(
                headline=n.headline,
                summary=n.summary,
                url=n.url,
                source=n.source,
                published_at=n.published_at,
                sentiment=float(n.sentiment) if n.sentiment is not None else None,
                category=n.category,
            )
            for n in stored
        ]

    async def _persist(self, articles, instrument_id) -> None:
        for a in articles:
            await self._repo.upsert(
                NewsItem(
                    instrument_id=instrument_id,
                    headline=a.headline,
                    summary=a.summary,
                    url=a.url,
                    source=a.source,
                    published_at=a.published_at,
                    category=a.category,
                )
            )
