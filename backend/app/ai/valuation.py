"""Deterministic valuation + trade-level estimates.

Heuristic (not a DCF): fair value is anchored to the long-run trend (200-day MA) with
a modest valuation tilt from P/E mean-reversion; entry/target/stop levels are sized from
ATR (volatility). These are decision aids, not financial advice. Designed to be cheap,
reproducible, and swappable for a richer model later.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from app.ai.base import AgentContext, clamp
from app.ai.indicators import technical_math
from app.domain.enums import Recommendation, TimeHorizon

_BASELINE_PE = 20.0  # market-ish anchor for the P/E mean-reversion tilt
_MAX_TILT = 0.15  # cap how far valuation pulls fair value off the trend mean

_HOLDING = {
    TimeHorizon.SHORT: "days to a few weeks",
    TimeHorizon.MEDIUM: "weeks to a few months",
    TimeHorizon.LONG: "6 to 18+ months",
}


@dataclass
class ValuationEstimate:
    fair_value: float | None = None
    valuation_gap_pct: float | None = None  # +ve = undervalued (upside to fair value)
    margin_of_safety_pct: float | None = None  # +ve only when price < fair value
    entry_low: float | None = None
    entry_high: float | None = None
    target_price: float | None = None
    stop_loss: float | None = None
    holding_period: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def _current_price(ctx: AgentContext) -> float | None:
    if ctx.quote and ctx.quote.price:
        return float(ctx.quote.price)
    if ctx.candles:
        return float(ctx.candles[-1].c)
    return None


def _fair_value(ctx: AgentContext, price: float, anchor: float | None) -> float:
    base = anchor or price  # long-run trend mean if available, else current price
    pe = ctx.fundamentals.pe if ctx.fundamentals else None
    if ctx.instrument.type != "etf" and pe and pe > 0:
        tilt = clamp((_BASELINE_PE - pe) / _BASELINE_PE, -_MAX_TILT, _MAX_TILT)
    else:
        tilt = 0.0  # ETFs / no earnings: stay on the trend mean
    fair = base * (1 + tilt)
    return clamp(fair, price * 0.6, price * 1.5)  # keep the estimate sane


def estimate(ctx: AgentContext, rating: Recommendation, horizon: TimeHorizon) -> ValuationEstimate:
    holding = _HOLDING.get(horizon, "varies")
    price = _current_price(ctx)
    if price is None or price <= 0:
        return ValuationEstimate(holding_period=holding)

    closes = [c.c for c in ctx.candles]
    anchor = technical_math.sma(closes, 200) or technical_math.sma(closes, 50)
    atr = technical_math.atr(ctx.candles) or price * 0.02  # ~2% vol fallback

    fair = _fair_value(ctx, price, anchor)
    gap = round((fair - price) / price * 100, 1)
    mos = round((fair - price) / fair * 100, 1) if fair > price else 0.0

    entry_low = round(price - 1.2 * atr, 2)
    entry_high = round(price + 0.3 * atr, 2)
    stop = round(max(price - 1.8 * atr, 0.0), 2)
    if rating in (Recommendation.WATCH, Recommendation.AVOID):
        target = round(fair, 2)  # no momentum target on a bearish view
    else:
        target = round(max(fair, price + 2.5 * atr), 2)

    return ValuationEstimate(
        fair_value=round(fair, 2),
        valuation_gap_pct=gap,
        margin_of_safety_pct=mos,
        entry_low=entry_low,
        entry_high=entry_high,
        target_price=target,
        stop_loss=stop,
        holding_period=holding,
    )
