from __future__ import annotations

import json

from app.ai.base import Agent, AgentContext, AgentResult, Compute
from app.ai.indicators import risk_math
from app.core.logging import get_logger
from app.domain.enums import AgentName, RiskLevel, Signal
from app.providers.base import LLMProvider

logger = get_logger("ai.agent.risk")

_ORDER = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]


class RiskAgent(Agent):
    """Gatekeeper. Emits a risk level (not a 0-100 score). The LLM may only escalate."""

    name = AgentName.RISK

    def compute(self, ctx: AgentContext) -> Compute:  # not used directly; kept for ABC
        raise NotImplementedError

    def _assess(self, ctx: AgentContext) -> risk_math.RiskAssessment:
        return risk_math.compute(
            candles=ctx.candles,
            fundamentals=ctx.fundamentals,
            portfolio=ctx.portfolio,
            symbol=ctx.instrument.symbol,
            sector=ctx.instrument.sector,
            max_position_pct=ctx.profile.max_position_pct,
        )

    async def run(self, ctx: AgentContext, llm: LLMProvider) -> AgentResult:
        a = self._assess(ctx)
        level = a.level
        explanation = "; ".join(a.warnings) if a.warnings else "Risk appears contained."
        justification = None

        if ctx.use_llm:
            try:
                verdict = await llm.complete_json(self._prompt(ctx, a), model=ctx.agent_model)
                reasoning = verdict.get("reasoning")
                if isinstance(reasoning, str) and reasoning.strip():
                    explanation = reasoning
                if verdict.get("escalate") is True and level is not RiskLevel.HIGH:
                    level = _ORDER[min(_ORDER.index(level) + 1, len(_ORDER) - 1)]
                    justification = "Escalated by risk review."
            except Exception as exc:  # noqa: BLE001
                logger.info("risk_llm_fallback", extra={"error": str(exc)})

        return AgentResult(
            agent=self.name,
            confidence=round(a.confidence, 2),
            score=None,
            base_score=None,
            signal=Signal.NEUTRAL,
            risk_level=level,
            warnings=a.warnings,
            payload=a.evidence,
            explanation=explanation,
            adjustment_justification=justification,
        )

    def _prompt(self, ctx: AgentContext, a: risk_math.RiskAssessment) -> str:
        return (
            "You are a risk officer reviewing an equity recommendation.\n"
            f"Symbol: {ctx.instrument.symbol}\n"
            f"Deterministic risk level: {a.level.value}\n"
            f"Risk evidence (JSON): {json.dumps(a.evidence, default=str)}\n"
            f"Warnings: {a.warnings}\n\n"
            "Summarize the key risks in one or two sentences. You may ONLY escalate the "
            "risk level (never lower it) if the evidence clearly warrants it. Reply with ONLY "
            'this JSON: {"reasoning": "<text>", "escalate": <true|false>}'
        )
