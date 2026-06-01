from __future__ import annotations

from datetime import UTC, datetime

from app.domain.enums import NotificationPriority, Recommendation, TimeHorizon
from app.notifications.builder import build
from app.schemas.recommendation import ReasonOut, RecommendationOut


def _rec() -> RecommendationOut:
    return RecommendationOut(
        symbol="AAPL",
        rating=Recommendation.BUY,
        anchor_rating=Recommendation.BUY,
        confidence=72.0,
        composite_score=68.0,
        decision_mode="deterministic",
        time_horizon=TimeHorizon.LONG,
        reasons=[ReasonOut(label="Momentum", detail="Strong technical momentum")],
        notif_priority=NotificationPriority.HIGH,
        generated_at=datetime.now(UTC),
    )


def test_build_notification_title_and_body():
    n = build(_rec(), app_base_url="https://app.example")
    assert n.title == "AAPL: BUY"
    assert "Strong technical momentum" in n.body
    assert n.priority == "high"
    assert n.tag == "AAPL"
    assert n.click_url == "https://app.example/recommendations/AAPL"
