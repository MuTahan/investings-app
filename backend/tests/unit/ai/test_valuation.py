from __future__ import annotations

from datetime import UTC, datetime

from app.ai.base import (
    AgentContext,
    DataQuality,
    InstrumentInfo,
    MacroSnapshot,
    PortfolioSnapshot,
    RiskProfileInfo,
)
from app.ai.valuation import estimate
from app.domain.enums import Recommendation, TimeHorizon
from app.providers.base import Candle, Fundamentals, QuoteData


def _ctx(prices: list[float], pe: float = 20.0, itype: str = "stock") -> AgentContext:
    candles = [
        Candle(t=datetime(2026, 1, 1, tzinfo=UTC), o=p, h=p + 1, l=p - 1, c=p, v=1000)
        for p in prices
    ]
    return AgentContext(
        instrument=InstrumentInfo(symbol="AAPL", name="Apple", type=itype, sector="Technology"),
        quote=QuoteData(symbol="AAPL", price=prices[-1]),
        candles=candles,
        fundamentals=Fundamentals(symbol="AAPL", pe=pe),
        news=[],
        macro=MacroSnapshot(),
        profile=RiskProfileInfo(),
        portfolio=PortfolioSnapshot(),
        data_quality=DataQuality(),
        use_llm=False,
    )


def test_levels_are_ordered_for_a_bullish_view():
    v = estimate(
        _ctx([100 + i * 0.5 for i in range(250)], pe=18), Recommendation.BUY, TimeHorizon.LONG
    )
    assert v.fair_value is not None
    assert v.stop_loss < v.entry_low <= v.entry_high
    assert v.target_price > v.entry_high
    assert v.holding_period == "6 to 18+ months"


def test_high_pe_tilts_fair_value_down_no_margin_of_safety():
    v = estimate(
        _ctx([200 + i * 0.1 for i in range(250)], pe=60), Recommendation.HOLD, TimeHorizon.MEDIUM
    )
    assert v.valuation_gap_pct is not None and v.valuation_gap_pct <= 0  # overvalued
    assert v.margin_of_safety_pct == 0.0


def test_missing_price_returns_holding_period_only():
    ctx = _ctx([100], pe=20)
    ctx.quote = None
    ctx.candles = []
    v = estimate(ctx, Recommendation.HOLD, TimeHorizon.LONG)
    assert v.fair_value is None
    assert v.holding_period
