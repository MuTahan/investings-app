"""Import all models so Base.metadata is fully populated (Alembic + create_all)."""

from __future__ import annotations

from app.db.models.device import Device, NotificationLog, NotificationPreference
from app.db.models.instrument import Instrument
from app.db.models.news import NewsItem
from app.db.models.portfolio import Holding, Portfolio
from app.db.models.recommendation import AgentOutput, Recommendation
from app.db.models.user import User, UserRiskProfile
from app.db.models.watchlist import Watchlist, WatchlistItem

__all__ = [
    "Device",
    "NotificationLog",
    "NotificationPreference",
    "Instrument",
    "NewsItem",
    "Holding",
    "Portfolio",
    "AgentOutput",
    "Recommendation",
    "User",
    "UserRiskProfile",
    "Watchlist",
    "WatchlistItem",
]
