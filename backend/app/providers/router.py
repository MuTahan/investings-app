"""Capability routing with fallback + read-through caching + rate limiting."""

from __future__ import annotations

from datetime import datetime

from app.config import Settings
from app.core.exceptions import ProviderError
from app.core.logging import get_logger
from app.providers.base import (
    CandleSeries,
    Fundamentals,
    MarketDataProvider,
    NewsArticle,
    QuoteData,
    SymbolHit,
)
from app.providers.cache import Cache
from app.providers.rate_limit import RateLimiterRegistry

logger = get_logger("providers.router")


class MarketDataRouter:
    """Routes a capability across an ordered list of vendors, with cache + fallback."""

    def __init__(
        self,
        settings: Settings,
        cache: Cache,
        rate_limiter: RateLimiterRegistry,
        chains: dict[str, list[MarketDataProvider]],
    ) -> None:
        self._settings = settings
        self._cache = cache
        self._rl = rate_limiter
        self._chains = chains

    async def _route(self, capability: str, caller):
        chain = self._chains.get(capability, [])
        if not chain:
            raise ProviderError(f"No provider configured for '{capability}'")
        last_error: Exception | None = None
        for provider in chain:
            if not await self._rl.allow(provider.name):
                logger.info("rate_limited_skip", extra={"vendor": provider.name, "cap": capability})
                continue
            try:
                return await caller(provider)
            except ProviderError as exc:
                last_error = exc
                logger.info(
                    "provider_fallback",
                    extra={"vendor": provider.name, "cap": capability, "error": str(exc)},
                )
                continue
        raise ProviderError(f"All providers failed for '{capability}': {last_error}")

    async def get_quote(self, symbol: str) -> QuoteData:
        key = f"quote:{symbol.upper()}"
        cached = await self._cache.get(key)
        if cached:
            return QuoteData.model_validate(cached)
        result = await self._route("quote", lambda p: p.get_quote(symbol))
        await self._cache.set(key, result.model_dump(mode="json"), self._settings.cache_ttl_quote)
        return result

    async def get_candles(
        self, symbol: str, resolution: str, frm: datetime, to: datetime
    ) -> CandleSeries:
        key = f"candles:{symbol.upper()}:{resolution}:{frm.date()}:{to.date()}"
        cached = await self._cache.get(key)
        if cached:
            return CandleSeries.model_validate(cached)
        result = await self._route("candles", lambda p: p.get_candles(symbol, resolution, frm, to))
        await self._cache.set(key, result.model_dump(mode="json"), self._settings.cache_ttl_candles)
        return result

    async def get_fundamentals(self, symbol: str) -> Fundamentals:
        key = f"fundamentals:{symbol.upper()}"
        cached = await self._cache.get(key)
        if cached:
            return Fundamentals.model_validate(cached)
        result = await self._route("fundamentals", lambda p: p.get_fundamentals(symbol))
        await self._cache.set(
            key, result.model_dump(mode="json"), self._settings.cache_ttl_fundamentals
        )
        return result

    async def search_symbols(self, query: str, limit: int = 20) -> list[SymbolHit]:
        key = f"search:{query.lower()}:{limit}"
        cached = await self._cache.get(key)
        if cached is not None:
            return [SymbolHit.model_validate(h) for h in cached]
        result = await self._route("search", lambda p: p.search_symbols(query, limit))
        await self._cache.set(
            key, [h.model_dump(mode="json") for h in result], self._settings.cache_ttl_news
        )
        return result

    async def get_news(
        self, symbol: str | None, category: str = "company", limit: int = 20
    ) -> list[NewsArticle]:
        key = f"news:{symbol or 'macro'}:{category}:{limit}"
        cached = await self._cache.get(key)
        if cached is not None:
            return [NewsArticle.model_validate(a) for a in cached]
        result = await self._route("news", lambda p: p.get_news(symbol, category, limit))
        await self._cache.set(
            key, [a.model_dump(mode="json") for a in result], self._settings.cache_ttl_news
        )
        return result
