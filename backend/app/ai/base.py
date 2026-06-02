"""Core AI orchestration types: context, agent results, and the Agent base class.

Agents depend only on these types + an LLMProvider — never on the DB or HTTP — so they
are trivially unit-testable. See docs/06-ai-agents.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.domain.enums import AgentName, RiskLevel, Signal
from app.providers.base import Candle, Fundamentals, LLMProvider, NewsArticle, QuoteData

logger = get_logger("ai.agent")


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


# ---------------- context value objects ----------------
@dataclass
class InstrumentInfo:
    symbol: str
    name: str
    type: str  # stock | etf
    sector: str | None = None


@dataclass
class HoldingInfo:
    symbol: str
    sector: str | None
    value: float
    weight: float  # 0..1


@dataclass
class PortfolioSnapshot:
    holdings: list[HoldingInfo] = field(default_factory=list)
    sector_exposure: dict[str, float] = field(default_factory=dict)  # sector -> weight 0..1
    total_value: float = 0.0

    def holds(self, symbol: str) -> HoldingInfo | None:
        for h in self.holdings:
            if h.symbol == symbol.upper():
                return h
        return None


@dataclass
class RiskProfileInfo:
    risk_tolerance: str = "moderate"
    time_horizon: str = "long"
    objectives: list[str] = field(default_factory=list)
    max_position_pct: float | None = None


@dataclass
class MacroSnapshot:
    regime: str = "neutral"
    vix: float | None = None
    rate_trend: str | None = None
    market_trend: str | None = None  # SPY above/below long MA
    macro_score: float = 50.0
    regime_modifier: float = 0.0  # small +/- nudge applied by the committee


@dataclass
class DataQuality:
    has_quote: bool = False
    has_candles: bool = False
    has_fundamentals: bool = False
    has_news: bool = False
    n_candles: int = 0


@dataclass
class AgentContext:
    instrument: InstrumentInfo
    quote: QuoteData | None
    candles: list[Candle]
    fundamentals: Fundamentals | None
    news: list[NewsArticle]
    macro: MacroSnapshot
    profile: RiskProfileInfo
    portfolio: PortfolioSnapshot
    data_quality: DataQuality
    decision_mode: str = "empowered"
    # use_llm gates the Committee Chair; agents_use_llm gates the 6 agents.
    # chair_assisted -> use_llm=True, agents_use_llm=False (1 LLM call/recommendation).
    # empowered      -> both True (7 LLM calls). deterministic -> both False.
    use_llm: bool = False
    agents_use_llm: bool = False
    agent_model: str = "claude-haiku-4-5"


# ---------------- agent output ----------------
@dataclass
class AgentResult:
    agent: AgentName
    confidence: float
    base_score: float | None = None
    score: float | None = None
    adjustment_delta: float = 0.0
    signal: Signal | None = None
    payload: dict = field(default_factory=dict)
    explanation: str | None = None
    adjustment_justification: str | None = None
    # risk agent
    risk_level: RiskLevel | None = None
    warnings: list[str] = field(default_factory=list)
    # portfolio-fit agent
    diversification_fit: float | None = None
    recommendation_modifier: float = 0.0


def signal_from_score(score: float) -> Signal:
    if score >= 60:
        return Signal.BULLISH
    if score <= 40:
        return Signal.BEARISH
    return Signal.NEUTRAL


# ---------------- agent base ----------------
@dataclass
class Compute:
    """Deterministic agent output before any LLM adjustment."""

    base_score: float
    signal: Signal
    confidence: float
    evidence: dict
    explanation: str


class Agent(ABC):
    name: AgentName
    MAX_DELTA: float = 10.0

    @abstractmethod
    def compute(self, ctx: AgentContext) -> Compute:
        """Pure, deterministic core — the anchor."""

    def prompt(self, ctx: AgentContext, c: Compute) -> str:  # overridden per agent
        raise NotImplementedError

    async def run(self, ctx: AgentContext, llm: LLMProvider) -> AgentResult:
        c = self.compute(ctx)
        if not ctx.agents_use_llm:
            return AgentResult(
                agent=self.name,
                base_score=round(c.base_score, 2),
                score=round(c.base_score, 2),
                confidence=round(c.confidence, 2),
                signal=c.signal,
                payload=c.evidence,
                explanation=c.explanation,
            )
        try:
            verdict = await llm.complete_json(self.prompt(ctx, c), model=ctx.agent_model)
        except Exception as exc:  # noqa: BLE001 - degrade to anchor on any LLM failure
            logger.info("agent_llm_fallback", extra={"agent": self.name.value, "error": str(exc)})
            verdict = {}
        return self._apply_verdict(c, verdict)

    def _apply_verdict(self, c: Compute, verdict: dict) -> AgentResult:
        raw = verdict.get("score")
        if isinstance(raw, (int, float)):
            score = clamp(float(raw), c.base_score - self.MAX_DELTA, c.base_score + self.MAX_DELTA)
            score = clamp(score, 0, 100)
        else:
            score = c.base_score
        reasoning = verdict.get("reasoning")
        explanation = (
            reasoning if isinstance(reasoning, str) and reasoning.strip() else c.explanation
        )
        justification = verdict.get("justification")
        signal = c.signal if score == c.base_score else signal_from_score(score)
        return AgentResult(
            agent=self.name,
            base_score=round(c.base_score, 2),
            score=round(score, 2),
            adjustment_delta=round(score - c.base_score, 2),
            confidence=round(c.confidence, 2),
            signal=signal,
            payload=c.evidence,
            explanation=explanation,
            adjustment_justification=justification if isinstance(justification, str) else None,
        )
