"""Trending stocks over a curated universe.

Free-tier honest: computed from quote data only (price/%-change/intraday range), so it's
cheap and needs no premium order-flow. 'Most bought/sold' are approximated by price
direction; richer signals can be added behind the same shape later. The whole snapshot is
cached so repeated dashboard loads don't burn API quota.
"""

from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ProviderError
from app.core.logging import get_logger
from app.domain.enums import Signal
from app.providers.container import ProviderContainer
from app.repositories.instrument_repo import InstrumentRepository
from app.schemas.trending import TrendingItem

logger = get_logger("trending")

_CACHE_KEY = "trending:snapshot"
_CACHE_TTL = 300  # 5 minutes

CATEGORIES = ("trending", "most_bought", "most_sold", "high_momentum", "high_opportunity")


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _scores(change_pct: float, price: float | None, low: float | None, high: float | None) -> dict:
    cp = change_pct
    trend_score = round(_clamp(50 + cp * 5, 0, 100), 1)
    activity = abs(cp)
    momentum = cp
    # intraday position 0 (at day low) .. 1 (at day high); buying an up-day dip scores higher
    if price is not None and low is not None and high is not None and high > low:
        pos = _clamp((price - low) / (high - low), 0, 1)
    else:
        pos = 0.5
    opportunity = cp * (1 - 0.5 * pos) if cp > 0 else cp * 0.5
    return {
        "trend_score": trend_score,
        "_activity": activity,
        "_momentum": momentum,
        "_opportunity": opportunity,
    }


def _sentiment(change_pct: float) -> Signal:
    if change_pct > 0.5:
        return Signal.BULLISH
    if change_pct < -0.5:
        return Signal.BEARISH
    return Signal.NEUTRAL


def _summary(change_pct: float) -> str:
    direction = "Up" if change_pct >= 0 else "Down"
    if abs(change_pct) >= 3:
        intensity = "sharply "
    elif abs(change_pct) >= 1:
        intensity = ""
    else:
        intensity = "modestly "
    return f"{direction} {intensity}{abs(change_pct):.1f}% today"


class TrendingService:
    def __init__(self, session: AsyncSession, providers: ProviderContainer) -> None:
        self._instruments = InstrumentRepository(session)
        self._providers = providers

    async def get(self, category: str, limit: int = 12) -> list[TrendingItem]:
        if category not in CATEGORIES:
            category = "trending"
        snapshot = await self._snapshot()
        ranked = self._rank(snapshot, category)
        return [
            TrendingItem(
                id=row["id"],
                symbol=row["symbol"],
                name=row["name"],
                type=row["type"],
                price=row["price"],
                change_pct=row["change_pct"],
                sentiment=row["sentiment"],
                trend_score=row["trend_score"],
                summary=row["summary"],
            )
            for row in ranked[:limit]
        ]

    def _rank(self, snapshot: list[dict], category: str) -> list[dict]:
        if category == "most_bought":
            rows = [r for r in snapshot if (r["change_pct"] or 0) > 0]
            return sorted(rows, key=lambda r: r["change_pct"], reverse=True)
        if category == "most_sold":
            rows = [r for r in snapshot if (r["change_pct"] or 0) < 0]
            return sorted(rows, key=lambda r: r["change_pct"])
        if category == "high_momentum":
            rows = [r for r in snapshot if (r["change_pct"] or 0) > 0]
            return sorted(rows, key=lambda r: r["_momentum"], reverse=True)
        if category == "high_opportunity":
            rows = [r for r in snapshot if (r["change_pct"] or 0) > 0]
            return sorted(rows, key=lambda r: r["_opportunity"], reverse=True)
        return sorted(snapshot, key=lambda r: r["_activity"], reverse=True)  # trending

    async def _snapshot(self) -> list[dict]:
        cached = await self._providers.cache.get(_CACHE_KEY)
        if cached:
            return cached
        instruments = await self._instruments.list_active()
        quotes = await asyncio.gather(
            *(self._quote(i.symbol) for i in instruments), return_exceptions=True
        )
        rows: list[dict] = []
        for inst, quote in zip(instruments, quotes, strict=False):
            if isinstance(quote, Exception) or quote is None:
                continue
            cp = quote.change_pct if quote.change_pct is not None else 0.0
            scores = _scores(cp, quote.price, quote.low, quote.high)
            rows.append(
                {
                    "id": str(inst.id),
                    "symbol": inst.symbol,
                    "name": inst.name,
                    "type": inst.type,
                    "price": quote.price,
                    "change_pct": round(cp, 2),
                    "sentiment": _sentiment(cp).value,
                    "summary": _summary(cp),
                    **scores,
                }
            )
        await self._providers.cache.set(_CACHE_KEY, rows, _CACHE_TTL)
        return rows

    async def _quote(self, symbol: str):
        try:
            return await self._providers.market.get_quote(symbol)
        except ProviderError:
            return None
