"""The Investment Committee: deterministic pipeline + a Claude Chair on top."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from app.ai import scoring
from app.ai.agents.fundamental import FundamentalAgent
from app.ai.agents.macro import MacroAgent
from app.ai.agents.news_sentiment import NewsSentimentAgent
from app.ai.agents.portfolio_fit import PortfolioFitAgent
from app.ai.agents.risk import RiskAgent
from app.ai.agents.technical import TechnicalAgent
from app.ai.base import AgentContext, AgentResult, clamp
from app.ai.prompts import chair_prompt
from app.core.logging import get_logger
from app.domain.enums import (
    RECOMMENDATION_LADDER,
    AgentName,
    NotificationPriority,
    Recommendation,
    RiskLevel,
    TimeHorizon,
)
from app.providers.base import LLMProvider

logger = get_logger("ai.committee")

_AGENT_LABELS = {
    AgentName.NEWS: "News & sentiment",
    AgentName.TECHNICAL: "Technical momentum",
    AgentName.FUNDAMENTAL: "Fundamentals",
    AgentName.MACRO: "Macro backdrop",
    AgentName.PORTFOLIO_FIT: "Portfolio fit",
}

_ACTIONS = {
    Recommendation.STRONG_BUY: "Strong setup — consider initiating or adding a position.",
    Recommendation.BUY: "Consider initiating or adding a moderate position on pullbacks.",
    Recommendation.HOLD: "Hold; no compelling action right now.",
    Recommendation.WATCH: "Keep on watch; wait for a better setup.",
    Recommendation.AVOID: "Avoid for now; risks outweigh the opportunity.",
}


@dataclass
class CommitteeResult:
    rating: Recommendation
    anchor_rating: Recommendation
    confidence: float
    composite_score: float
    decision_mode: str
    time_horizon: TimeHorizon
    suggested_action: str
    chair_rationale: str | None
    reasons: list[dict]
    risks: list[dict]
    personalization: dict
    agent_breakdown: list[AgentResult]
    notif_priority: NotificationPriority
    weights_version: str = scoring.WEIGHTS_VERSION
    model_versions: dict = field(default_factory=dict)


class InvestmentCommittee:
    def __init__(self) -> None:
        self._agents = [
            NewsSentimentAgent(),
            TechnicalAgent(),
            FundamentalAgent(),
            MacroAgent(),
            RiskAgent(),
            PortfolioFitAgent(),
        ]

    async def evaluate(
        self,
        ctx: AgentContext,
        llm: LLMProvider,
        *,
        chair_model: str,
        previous_rating: Recommendation | None = None,
        previous_score: float | None = None,
    ) -> CommitteeResult:
        results = list(await asyncio.gather(*(agent.run(ctx, llm) for agent in self._agents)))
        by = {r.agent: r for r in results}
        risk = by.get(AgentName.RISK)
        fit = by.get(AgentName.PORTFOLIO_FIT)
        risk_level = risk.risk_level if risk else None

        # --- deterministic composite ---
        composite = scoring.composite_score(results)
        composite += clamp(ctx.macro.regime_modifier, -5, 5)
        composite = scoring.apply_risk_gate_score(composite, risk_level)
        if fit:
            composite += clamp(fit.recommendation_modifier, -10, 10)
        composite = clamp(composite, 0, 100)

        anchor = scoring.map_score_to_rating(composite)
        anchor = scoring.cap_rating_for_risk(anchor, risk_level)
        conflicts = scoring.detect_conflicts(results, composite)

        # --- chair (bounded) ---
        final = anchor
        chair_rationale: str | None = None
        chair_confidence: float | None = None
        if ctx.use_llm:
            final, chair_rationale, chair_confidence = await self._chair(
                ctx, llm, chair_model, results, anchor, composite, conflicts
            )

        bands_moved = RECOMMENDATION_LADDER.index(final) - RECOMMENDATION_LADDER.index(anchor)
        conf = scoring.confidence(results, risk_level, bands_moved)
        if chair_confidence is not None:
            conf = round((conf + clamp(chair_confidence, 5, 99)) / 2, 1)

        horizon = scoring.time_horizon(results, ctx.profile.time_horizon)
        delta = composite - previous_score if previous_score is not None else 0.0
        priority = scoring.notification_priority(final, previous_rating, delta, conf, risk_level)

        return CommitteeResult(
            rating=final,
            anchor_rating=anchor,
            confidence=conf,
            composite_score=round(composite, 2),
            decision_mode=ctx.decision_mode if ctx.use_llm else "deterministic",
            time_horizon=horizon,
            suggested_action=_ACTIONS[final],
            chair_rationale=chair_rationale,
            reasons=self._reasons(results, final),
            risks=self._risks(risk, conflicts, risk_level),
            personalization=self._personalization(fit),
            agent_breakdown=results,
            notif_priority=priority,
            model_versions=(
                {"agents": ctx.agent_model, "chair": chair_model} if ctx.use_llm else {}
            ),
        )

    async def _chair(
        self,
        ctx: AgentContext,
        llm: LLMProvider,
        chair_model: str,
        results: list[AgentResult],
        anchor: Recommendation,
        composite: float,
        conflicts: list[str],
    ) -> tuple[Recommendation, str | None, float | None]:
        staff = [
            {
                "agent": r.agent.value,
                "score": r.score,
                "signal": r.signal.value if r.signal else None,
                "risk_level": r.risk_level.value if r.risk_level else None,
                "explanation": r.explanation,
            }
            for r in results
        ]
        risk = next((r for r in results if r.agent == AgentName.RISK), None)
        risk_level = risk.risk_level if risk else None
        allowed = scoring.allowed_ratings(anchor, max_bands=1)
        profile = {
            "risk_tolerance": ctx.profile.risk_tolerance,
            "time_horizon": ctx.profile.time_horizon,
            "objectives": ctx.profile.objectives,
        }
        try:
            verdict = await llm.complete_json(
                chair_prompt(
                    ctx.instrument.symbol,
                    staff,
                    anchor.value,
                    round(composite, 1),
                    conflicts,
                    profile,
                    allowed,
                ),
                model=chair_model,
            )
        except Exception as exc:  # noqa: BLE001 - degrade to anchor
            logger.info("chair_llm_fallback", extra={"error": str(exc)})
            return anchor, None, None

        raw_rating = verdict.get("final_rating")
        try:
            chair_rating = Recommendation(raw_rating)
        except (ValueError, TypeError):
            chair_rating = anchor
        final = scoring.clamp_to_band(chair_rating, anchor, max_bands=1)
        final = scoring.cap_rating_for_risk(final, risk_level)
        rationale = verdict.get("rationale")
        conf = verdict.get("confidence")
        return (
            final,
            rationale if isinstance(rationale, str) else None,
            float(conf) if isinstance(conf, (int, float)) else None,
        )

    def _reasons(self, results: list[AgentResult], rating: Recommendation) -> list[dict]:
        by = {r.agent: r for r in results}
        bullish = rating in (Recommendation.STRONG_BUY, Recommendation.BUY)
        bearish = rating in (Recommendation.WATCH, Recommendation.AVOID)
        candidates: list[tuple[float, str, str]] = []
        for agent, label in _AGENT_LABELS.items():
            r = by.get(agent)
            if r is None or r.score is None:
                continue
            dev = r.score - 50
            if (bullish and dev > 3) or (bearish and dev < -3) or (not bullish and not bearish):
                candidates.append((abs(dev), label, r.explanation or ""))
        candidates.sort(key=lambda x: x[0], reverse=True)
        reasons = [
            {"label": label, "detail": detail} for _, label, detail in candidates[:3] if detail
        ]
        if not reasons:
            reasons = [{"label": "Balanced signals", "detail": "No single factor dominates."}]
        return reasons

    def _risks(
        self, risk: AgentResult | None, conflicts: list[str], risk_level: RiskLevel | None
    ) -> list[dict]:
        severity = (risk_level or RiskLevel.LOW).value
        notes: list[dict] = []
        if risk and risk.warnings:
            for w in risk.warnings:
                notes.append({"label": "Risk", "detail": w, "severity": severity})
        for c in conflicts:
            notes.append({"label": "Signal conflict", "detail": c, "severity": "medium"})
        if not notes:
            notes.append(
                {"label": "Market risk", "detail": "All investments carry risk.", "severity": "low"}
            )
        return notes

    def _personalization(self, fit: AgentResult | None) -> dict:
        if fit is None:
            return {}
        return {"fit_score": fit.score, "fit_reason": fit.explanation}
