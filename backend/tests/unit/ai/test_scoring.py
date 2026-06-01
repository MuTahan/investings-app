from __future__ import annotations

from app.ai import scoring
from app.ai.base import AgentResult
from app.domain.enums import AgentName, NotificationPriority, Recommendation, RiskLevel, Signal


def _result(agent: AgentName, score: float | None, conf: float = 70.0, **kw) -> AgentResult:
    return AgentResult(agent=agent, score=score, base_score=score, confidence=conf, **kw)


def test_rating_thresholds():
    assert scoring.map_score_to_rating(85) == Recommendation.STRONG_BUY
    assert scoring.map_score_to_rating(70) == Recommendation.BUY
    assert scoring.map_score_to_rating(50) == Recommendation.HOLD
    assert scoring.map_score_to_rating(35) == Recommendation.WATCH
    assert scoring.map_score_to_rating(10) == Recommendation.AVOID


def test_clamp_to_band_limits_chair():
    # anchor BUY -> chair cannot jump to AVOID; clamps to HOLD (one band down)
    assert scoring.clamp_to_band(Recommendation.AVOID, Recommendation.BUY) == Recommendation.HOLD
    # chair STRONG_BUY from BUY anchor is within +1 band -> allowed
    assert (
        scoring.clamp_to_band(Recommendation.STRONG_BUY, Recommendation.BUY)
        == Recommendation.STRONG_BUY
    )


def test_risk_gate_caps_rating():
    assert (
        scoring.cap_rating_for_risk(Recommendation.STRONG_BUY, RiskLevel.HIGH)
        == Recommendation.HOLD
    )
    assert (
        scoring.cap_rating_for_risk(Recommendation.STRONG_BUY, RiskLevel.MEDIUM)
        == Recommendation.BUY
    )
    assert (
        scoring.cap_rating_for_risk(Recommendation.STRONG_BUY, RiskLevel.LOW)
        == Recommendation.STRONG_BUY
    )


def test_risk_gate_caps_score():
    assert scoring.apply_risk_gate_score(90, RiskLevel.HIGH) == scoring.CAP_HIGH_RISK
    assert scoring.apply_risk_gate_score(90, RiskLevel.MEDIUM) == scoring.CAP_MEDIUM_RISK
    assert scoring.apply_risk_gate_score(70, RiskLevel.LOW) == 70


def test_composite_score_weighting():
    fit = _result(AgentName.PORTFOLIO_FIT, 60, diversification_fit=70)
    results = [
        _result(AgentName.NEWS, 60),
        _result(AgentName.TECHNICAL, 80),
        _result(AgentName.FUNDAMENTAL, 70),
        _result(AgentName.MACRO, 50),
        fit,
        AgentResult(agent=AgentName.RISK, score=None, confidence=70, risk_level=RiskLevel.LOW),
    ]
    # 60*.2 + 80*.2 + 70*.2 + 50*.15 + 60*.15 + 70*.10 = 12+16+14+7.5+9+7 = 65.5
    assert scoring.composite_score(results) == 65.5


def test_notification_priority_transitions():
    assert (
        scoring.notification_priority(
            Recommendation.STRONG_BUY, Recommendation.HOLD, 20, 80, RiskLevel.LOW
        )
        == NotificationPriority.CRITICAL
    )
    assert (
        scoring.notification_priority(Recommendation.BUY, Recommendation.HOLD, 5, 80, RiskLevel.LOW)
        == NotificationPriority.HIGH
    )
    assert (
        scoring.notification_priority(
            Recommendation.HOLD, Recommendation.HOLD, 1, 80, RiskLevel.LOW
        )
        == NotificationPriority.LOW
    )
    assert (
        scoring.notification_priority(Recommendation.STRONG_BUY, None, 0, 80, RiskLevel.LOW)
        == NotificationPriority.HIGH
    )


def test_detect_conflicts():
    results = [
        _result(AgentName.TECHNICAL, 70, signal=Signal.BULLISH),
        _result(AgentName.FUNDAMENTAL, 35, signal=Signal.BEARISH),
        _result(AgentName.NEWS, 50),
    ]
    conflicts = scoring.detect_conflicts(results, composite=55)
    assert any("Momentum" in c for c in conflicts)
