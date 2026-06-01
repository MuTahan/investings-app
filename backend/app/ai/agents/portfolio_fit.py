from __future__ import annotations

from app.ai.base import Agent, AgentContext, AgentResult, Compute, clamp, signal_from_score
from app.ai.prompts import agent_reasoning_prompt
from app.core.logging import get_logger
from app.domain.enums import AgentName
from app.providers.base import LLMProvider

logger = get_logger("ai.agent.fit")


class PortfolioFitAgent(Agent):
    """Personalization. Produces fit_score + diversification_fit + a bounded modifier."""

    name = AgentName.PORTFOLIO_FIT

    def compute(self, ctx: AgentContext) -> Compute:  # used to seed the LLM adjustment
        alignment = self._alignment(ctx)
        diversification = self._diversification(ctx)
        fit_score = clamp(0.6 * alignment + 0.4 * diversification, 0, 100)
        evidence = {
            "objective_alignment": round(alignment, 1),
            "diversification_fit": round(diversification, 1),
            "risk_tolerance": ctx.profile.risk_tolerance,
            "time_horizon": ctx.profile.time_horizon,
            "objectives": ctx.profile.objectives,
        }
        explanation = self._reason(ctx, alignment, diversification)
        return Compute(
            round(fit_score, 2), signal_from_score(fit_score), 62.0, evidence, explanation
        )

    def _alignment(self, ctx: AgentContext) -> float:
        score = 55.0
        tol = ctx.profile.risk_tolerance
        beta = ctx.fundamentals.beta if ctx.fundamentals else None
        if ctx.instrument.type == "etf":
            score += 10 if tol == "conservative" else (-3 if tol == "aggressive" else 5)
        else:
            if beta is not None:
                if tol == "aggressive":
                    score += 10 if beta > 1.2 else 0
                elif tol == "conservative":
                    score += -10 if beta > 1.2 else 8 if beta < 0.9 else 0
        objectives = set(ctx.profile.objectives or [])
        if ctx.fundamentals:
            if "income" in objectives and (ctx.fundamentals.dividend_yield or 0) > 0.02:
                score += 5
            rev = ctx.fundamentals.revenue_growth
            if (
                "growth" in objectives
                and rev is not None
                and (rev / 100 if abs(rev) > 1.5 else rev) > 0.1
            ):
                score += 5
        return clamp(score, 0, 100)

    def _diversification(self, ctx: AgentContext) -> float:
        if not ctx.portfolio.holdings:
            return 60.0
        if ctx.instrument.type == "etf":
            return 70.0
        sector = ctx.instrument.sector or ""
        weight = ctx.portfolio.sector_exposure.get(sector, 0.0)
        if weight > 0.4:
            return 35.0
        if weight == 0.0:
            return 75.0
        return 55.0

    def _reason(self, ctx: AgentContext, alignment: float, diversification: float) -> str:
        a = "aligns with" if alignment >= 55 else "is a weaker match for"
        d = (
            "adds diversification"
            if diversification >= 60
            else (
                "adds little diversification"
                if diversification < 45
                else "is roughly neutral for diversification"
            )
        )
        return f"{a} your {ctx.profile.risk_tolerance}/{ctx.profile.time_horizon} profile and {d}."

    async def run(self, ctx: AgentContext, llm: LLMProvider) -> AgentResult:
        c = self.compute(ctx)
        fit_score = c.base_score
        explanation = c.explanation
        justification = None
        diversification = float(c.evidence["diversification_fit"])

        if ctx.use_llm:
            try:
                verdict = await llm.complete_json(
                    agent_reasoning_prompt(
                        "portfolio_fit", ctx.instrument.symbol, c.evidence, c.base_score
                    ),
                    model=ctx.agent_model,
                )
                raw = verdict.get("score")
                if isinstance(raw, (int, float)):
                    fit_score = clamp(
                        float(raw), c.base_score - self.MAX_DELTA, c.base_score + self.MAX_DELTA
                    )
                    fit_score = clamp(fit_score, 0, 100)
                reasoning = verdict.get("reasoning")
                if isinstance(reasoning, str) and reasoning.strip():
                    explanation = reasoning
                j = verdict.get("justification")
                justification = j if isinstance(j, str) else None
            except Exception as exc:  # noqa: BLE001
                logger.info("fit_llm_fallback", extra={"error": str(exc)})

        modifier = clamp((fit_score - 50) / 5, -10, 10)
        return AgentResult(
            agent=self.name,
            base_score=round(c.base_score, 2),
            score=round(fit_score, 2),
            adjustment_delta=round(fit_score - c.base_score, 2),
            confidence=c.confidence,
            signal=signal_from_score(fit_score),
            payload=c.evidence,
            explanation=explanation,
            adjustment_justification=justification,
            diversification_fit=round(diversification, 2),
            recommendation_modifier=round(modifier, 2),
        )
