from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import Recommendation


class NotificationFeedItem(BaseModel):
    symbol: str | None = None
    rating: Recommendation | None = None
    sent_at: datetime
    status: str


class NotificationFeedResponse(BaseModel):
    items: list[NotificationFeedItem]


class RunResult(BaseModel):
    evaluated: int
    sent: int
    skipped_quiet_hours: bool = False
