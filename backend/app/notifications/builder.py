"""Build a Notification payload from a recommendation result."""

from __future__ import annotations

from app.notifications.notifier import Notification
from app.schemas.recommendation import RecommendationOut

_EMOJI = {
    "STRONG_BUY": "🟢🟢",
    "BUY": "🟢",
    "HOLD": "⚪️",
    "WATCH": "🟡",
    "AVOID": "🔴",
}


def build(rec: RecommendationOut, *, app_base_url: str | None = None) -> Notification:
    rating = rec.rating.value
    title = f"{rec.symbol}: {rating.replace('_', ' ')}"
    lead = rec.reasons[0].detail if rec.reasons else (rec.suggested_action or "")
    emoji = _EMOJI.get(rating, "")
    headline = f"{emoji} {int(rec.confidence)}% confidence · {rec.time_horizon.value} term"
    body = f"{headline}\n{lead}"
    click = f"{app_base_url.rstrip('/')}/recommendations/{rec.symbol}" if app_base_url else None
    return Notification(
        title=title,
        body=body.strip(),
        priority=rec.notif_priority.value,
        tag=rec.symbol,
        click_url=click,
    )
