from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import NotificationPriority, Recommendation, RiskLevel


class NotificationFeedItem(BaseModel):
    symbol: str | None = None
    rating: Recommendation | None = None
    category: str = "rating_change"
    sent_at: datetime
    status: str


class NotificationFeedResponse(BaseModel):
    items: list[NotificationFeedItem]


class RunResult(BaseModel):
    evaluated: int
    sent: int
    skipped_quiet_hours: bool = False


class NotificationPreferenceOut(BaseModel):
    categories: list[str] = []  # empty = all categories
    min_priority: NotificationPriority = NotificationPriority.HIGH
    max_risk: RiskLevel = RiskLevel.HIGH
    sectors: list[str] = []  # empty = all sectors
    quiet_hours_start: int | None = None
    quiet_hours_end: int | None = None


class NotificationPreferenceUpdate(BaseModel):
    categories: list[str] = Field(default_factory=list, max_length=10)
    min_priority: NotificationPriority = NotificationPriority.HIGH
    max_risk: RiskLevel = RiskLevel.HIGH
    sectors: list[str] = Field(default_factory=list, max_length=20)
    quiet_hours_start: int | None = Field(default=None, ge=0, le=23)
    quiet_hours_end: int | None = Field(default=None, ge=0, le=23)
