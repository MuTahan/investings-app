"""Assemble an AgentContext from providers, resilient to missing data."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.ai.base import (
    AgentContext,
    DataQuality,
    InstrumentInfo,
    MacroSnapshot,
    PortfolioSnapshot,
    RiskProfileInfo,
)
from app.ai.indicators.technical_math import sma
from app.core.exceptions import ProviderError
from app.core.logging import get_logger
from app.providers.router import MarketDataRouter

logger = get_logger("ai.context")


async def build_macro(market: MarketDataRouter) -> MacroSnapshot:
    """Best-effort macro regime from VIX + SPY trend. Neutral fallback on any failure."""
    vix: float | None = None
    market_trend: str | None = None
    try:
        vix = (await market.get_quote("^VIX")).price
    except ProviderError:
        pass
    try:
        to = datetime.now(UTC)
        candles = (await market.get_candles("SPY", "D", to - timedelta(days=220), to)).candles
        closes = [c.c for c in candles]
        ref = sma(closes, 100) or sma(closes, 20)
        if closes and ref:
            market_trend = "up" if closes[-1] >= ref else "down"
    except ProviderError:
        pass

    regime, score, mod = _classify(vix, market_trend)
    return MacroSnapshot(
        regime=regime,
        vix=vix,
        market_trend=market_trend,
        macro_score=score,
        regime_modifier=mod,
    )


def _classify(vix: float | None, trend: str | None) -> tuple[str, float, float]:
    if vix is not None and vix > 30:
        return "risk_off", 38.0, -4.0
    if vix is not None and vix > 22:
        return ("risk_off", 42.0, -3.0) if trend == "down" else ("neutral", 48.0, -1.0)
    if trend == "up" and (vix is None or vix < 18):
        return "risk_on", 60.0, 3.0
    if trend == "down":
        return "late_cycle", 47.0, -1.0
    return "neutral", 50.0, 0.0


class ContextBuilder:
    def __init__(self, market: MarketDataRouter) -> None:
        self._market = market

    async def build(
        self,
        *,
        instrument: InstrumentInfo,
        profile: RiskProfileInfo,
        portfolio: PortfolioSnapshot,
        macro: MacroSnapshot,
        decision_mode: str,
        use_llm: bool,
        agent_model: str,
    ) -> AgentContext:
        symbol = instrument.symbol
        to = datetime.now(UTC)

        quote = None
        candles = []
        fundamentals = None
        news = []

        try:
            quote = await self._market.get_quote(symbol)
        except ProviderError:
            logger.info("ctx_no_quote", extra={"symbol": symbol})
        try:
            candles = (
                await self._market.get_candles(symbol, "D", to - timedelta(days=400), to)
            ).candles
        except ProviderError:
            logger.info("ctx_no_candles", extra={"symbol": symbol})
        try:
            fundamentals = await self._market.get_fundamentals(symbol)
        except ProviderError:
            logger.info("ctx_no_fundamentals", extra={"symbol": symbol})
        try:
            news = await self._market.get_news(symbol, "company", 10)
        except ProviderError:
            logger.info("ctx_no_news", extra={"symbol": symbol})

        dq = DataQuality(
            has_quote=quote is not None,
            has_candles=bool(candles),
            has_fundamentals=fundamentals is not None,
            has_news=bool(news),
            n_candles=len(candles),
        )
        return AgentContext(
            instrument=instrument,
            quote=quote,
            candles=candles,
            fundamentals=fundamentals,
            news=news,
            macro=macro,
            profile=profile,
            portfolio=portfolio,
            data_quality=dq,
            decision_mode=decision_mode,
            use_llm=use_llm,
            agent_model=agent_model,
        )
