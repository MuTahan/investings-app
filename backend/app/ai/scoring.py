"""Deterministic scoring model: weights, gating, mapping, confidence, priority.

This module is the reproducible core. Given fixed agent scores it always yields the
same composite, anchor rating, and notification priority — which is what the
determinism tests assert.
"""

from __future__ import annotations

import statistics

from app.ai.base import AgentResult, clamp
from app.domain.enums import (
    RECOMMENDATION_LADDER,
    AgentName,
    NotificationPriority,
    Recommendation,
    RiskLevel,
    TimeHorizon,
)

WEIGHTS_VERSION = "v1"
WEIGHTS = {
    "news": 0.20,
    "technical": 0.20,
    "fundamental": 0.20,
    "macro": 0.15,
    "portfolio_fit": 0.15,
    "diversification_fit": 0.10,
}

CAP_MEDIUM_RISK = 80.0
CAP_HIGH_RISK = 55.0


def _by_agent(results: list[AgentResult]) -> dict[AgentName, AgentResult]:
    return {r.agent: r for r in results}


def _score(result: AgentResult | None) -> float:
    if result is None or result.score is None:
        return 50.0
    return result.score


def composite_score(results: list[AgentResult]) -> float:
    by = _by_agent(results)
    fit = by.get(AgentName.PORTFOLIO_FIT)
    diversification = (
        fit.diversification_fit if fit and fit.diversification_fit is not None else 50.0
    )
    total = (
        _score(by.get(AgentName.NEWS)) * WEIGHTS["news"]
        + _score(by.get(AgentName.TECHNICAL)) * WEIGHTS["technical"]
        + _score(by.get(AgentName.FUNDAMENTAL)) * WEIGHTS["fundamental"]
        + _score(by.get(AgentName.MACRO)) * WEIGHTS["macro"]
        + _score(fit) * WEIGHTS["portfolio_fit"]
        + diversification * WEIGHTS["diversification_fit"]
    )
    return total


def apply_risk_gate_score(score: float, risk_level: RiskLevel | None) -> float:
    if risk_level == RiskLevel.HIGH:
        return min(score, CAP_HIGH_RISK)
    if risk_level == RiskLevel.MEDIUM:
        return min(score, CAP_MEDIUM_RISK)
    return score


def map_score_to_rating(score: float) -> Recommendation:
    if score >= 80:
        return Recommendation.STRONG_BUY
    if score >= 65:
        return Recommendation.BUY
    if score >= 45:
        return Recommendation.HOLD
    if score >= 30:
        return Recommendation.WATCH
    return Recommendation.AVOID


def cap_rating_for_risk(rating: Recommendation, risk_level: RiskLevel | None) -> Recommendation:
    idx = RECOMMENDATION_LADDER.index(rating)
    if risk_level == RiskLevel.HIGH:
        cap = RECOMMENDATION_LADDER.index(Recommendation.HOLD)
        return RECOMMENDATION_LADDER[min(idx, cap)]
    if risk_level == RiskLevel.MEDIUM:
        cap = RECOMMENDATION_LADDER.index(Recommendation.BUY)
        return RECOMMENDATION_LADDER[min(idx, cap)]
    return rating


def clamp_to_band(
    rating: Recommendation, anchor: Recommendation, max_bands: int = 1
) -> Recommendation:
    anchor_idx = RECOMMENDATION_LADDER.index(anchor)
    idx = RECOMMENDATION_LADDER.index(rating)
    low = max(0, anchor_idx - max_bands)
    high = min(len(RECOMMENDATION_LADDER) - 1, anchor_idx + max_bands)
    return RECOMMENDATION_LADDER[clamp_int(idx, low, high)]


def allowed_ratings(anchor: Recommendation, max_bands: int = 1) -> list[str]:
    anchor_idx = RECOMMENDATION_LADDER.index(anchor)
    low = max(0, anchor_idx - max_bands)
    high = min(len(RECOMMENDATION_LADDER) - 1, anchor_idx + max_bands)
    return [r.value for r in RECOMMENDATION_LADDER[low : high + 1]]


def clamp_int(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def detect_conflicts(results: list[AgentResult], composite: float) -> list[str]:
    by = _by_agent(results)
    conflicts: list[str] = []
    tech = _score(by.get(AgentName.TECHNICAL))
    fund = _score(by.get(AgentName.FUNDAMENTAL))
    news = _score(by.get(AgentName.NEWS))
    risk = by.get(AgentName.RISK)

    if tech >= 60 and fund <= 40:
        conflicts.append("Momentum bullish vs weak fundamentals")
    if fund >= 60 and tech <= 40:
        conflicts.append("Strong fundamentals vs weak price action")
    if news <= 40 and tech >= 60:
        conflicts.append("Negative news vs bullish technicals")
    if composite >= 65 and risk and risk.risk_level == RiskLevel.HIGH:
        conflicts.append("Attractive score gated by elevated risk")
    return conflicts


def confidence(
    results: list[AgentResult],
    risk_level: RiskLevel | None,
    bands_moved: int,
) -> float:
    by = _by_agent(results)
    scores = [
        _score(by.get(a))
        for a in (
            AgentName.NEWS,
            AgentName.TECHNICAL,
            AgentName.FUNDAMENTAL,
            AgentName.MACRO,
            AgentName.PORTFOLIO_FIT,
        )
    ]
    confidences = [r.confidence for r in results if r.confidence is not None]
    mean_conf = statistics.fmean(confidences) if confidences else 50.0
    spread = statistics.pstdev(scores) if len(scores) > 1 else 0.0
    agreement = 100 - clamp(spread, 0, 40)
    risk_penalty = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 5, RiskLevel.HIGH: 12}.get(risk_level, 0)
    deviation_penalty = 5 * abs(bands_moved)
    return round(
        clamp(0.5 * mean_conf + 0.5 * agreement - risk_penalty - deviation_penalty, 5, 99), 1
    )


def time_horizon(results: list[AgentResult], profile_horizon: str) -> TimeHorizon:
    by = _by_agent(results)
    tech_dev = abs(_score(by.get(AgentName.TECHNICAL)) - 50)
    fund_dev = abs(_score(by.get(AgentName.FUNDAMENTAL)) - 50)
    macro_dev = abs(_score(by.get(AgentName.MACRO)) - 50)
    short_signal = tech_dev
    long_signal = fund_dev + macro_dev
    if short_signal < 5 and long_signal < 5:
        return _to_horizon(profile_horizon)
    if short_signal > long_signal:
        return TimeHorizon.SHORT if profile_horizon == "short" else TimeHorizon.MEDIUM
    return TimeHorizon.LONG


def _to_horizon(value: str) -> TimeHorizon:
    try:
        return TimeHorizon(value)
    except ValueError:
        return TimeHorizon.LONG


def notification_priority(
    final_rating: Recommendation,
    previous_rating: Recommendation | None,
    delta_score: float,
    confidence_value: float,
    risk_level: RiskLevel | None,
) -> NotificationPriority:
    if previous_rating is not None:
        bands = abs(
            RECOMMENDATION_LADDER.index(final_rating) - RECOMMENDATION_LADDER.index(previous_rating)
        )
        if bands >= 2:
            return NotificationPriority.CRITICAL
        if bands == 1:
            return NotificationPriority.HIGH
        if abs(delta_score) >= 10:
            return NotificationPriority.NORMAL
        return NotificationPriority.LOW
    # first recommendation for this symbol
    if final_rating in (Recommendation.STRONG_BUY, Recommendation.AVOID) and confidence_value >= 70:
        return NotificationPriority.HIGH
    return NotificationPriority.NORMAL
