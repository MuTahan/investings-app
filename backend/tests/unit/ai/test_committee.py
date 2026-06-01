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
from app.ai.committee import InvestmentCommittee
from app.domain.enums import Recommendation
from app.providers.base import Candle, Fundamentals, NewsArticle


class StubLLM:
    name = "stub"

    async def complete_text(self, prompt, *, model, max_tokens=600):
        return ""

    async def complete_json(self, prompt, *, model, max_tokens=800):
        return {}


def _candles(prices: list[float]) -> list[Candle]:
    return [
        Candle(t=datetime(2026, 1, 1, tzinfo=UTC), o=p, h=p + 1, l=p - 1, c=p, v=1000)
        for p in prices
    ]


def _context(*, prices, fundamentals, news, sector="Technology", portfolio=None) -> AgentContext:
    candles = _candles(prices)
    return AgentContext(
        instrument=InstrumentInfo(symbol="AAPL", name="Apple", type="stock", sector=sector),
        quote=None,
        candles=candles,
        fundamentals=fundamentals,
        news=news,
        macro=MacroSnapshot(regime="neutral", macro_score=50.0, regime_modifier=0.0),
        profile=RiskProfileInfo(risk_tolerance="moderate", time_horizon="long"),
        portfolio=portfolio or PortfolioSnapshot(),
        data_quality=DataQuality(has_candles=True, n_candles=len(candles)),
        decision_mode="empowered",
        use_llm=False,  # deterministic core path (the test oracle)
    )


async def test_committee_is_deterministic_and_complete():
    committee = InvestmentCommittee()
    ctx = _context(
        prices=[100 + i * 0.5 for i in range(250)],
        fundamentals=Fundamentals(
            symbol="AAPL", pe=18, op_margin=0.30, revenue_growth=0.2, eps_growth=0.2
        ),
        news=[NewsArticle(headline="Company beats and surges to record", url="https://x/1")],
    )

    first = await committee.evaluate(ctx, StubLLM(), chair_model="m")
    second = await committee.evaluate(ctx, StubLLM(), chair_model="m")

    assert first.rating == second.rating
    assert first.composite_score == second.composite_score
    assert first.rating == first.anchor_rating  # deterministic mode: final == anchor
    assert isinstance(first.rating, Recommendation)
    assert len(first.agent_breakdown) == 6
    assert first.decision_mode == "deterministic"
    assert first.reasons and first.risks


async def test_committee_bullish_inputs_lean_positive():
    committee = InvestmentCommittee()
    ctx = _context(
        prices=[100 + i * 0.5 for i in range(250)],
        fundamentals=Fundamentals(
            symbol="AAPL", pe=16, op_margin=0.35, revenue_growth=0.25, eps_growth=0.25
        ),
        news=[
            NewsArticle(headline="Analyst upgrade; shares jump and beat record", url="https://x/2")
        ],
    )
    result = await committee.evaluate(ctx, StubLLM(), chair_model="m")
    assert result.composite_score >= 55
    assert result.rating in {Recommendation.HOLD, Recommendation.BUY, Recommendation.STRONG_BUY}


async def test_high_risk_caps_rating():
    committee = InvestmentCommittee()
    # large alternating swings -> high volatility; rich valuation + high beta -> risk HIGH
    ctx = _context(
        prices=[100 if i % 2 == 0 else 118 for i in range(40)],
        fundamentals=Fundamentals(
            symbol="AAPL", pe=55, op_margin=0.35, revenue_growth=0.3, beta=2.2
        ),
        news=[NewsArticle(headline="Shares surge and beat to record high", url="https://x/3")],
    )
    result = await committee.evaluate(ctx, StubLLM(), chair_model="m")
    risk = next(a for a in result.agent_breakdown if a.agent.value == "risk")
    assert risk.risk_level is not None and risk.risk_level.value == "high"
    # high risk can never reach STRONG_BUY/BUY
    assert result.rating not in {Recommendation.STRONG_BUY, Recommendation.BUY}
