"""Pure domain enums shared across layers (no I/O)."""

from __future__ import annotations

from enum import StrEnum


class InstrumentType(StrEnum):
    STOCK = "stock"
    ETF = "etf"


class Recommendation(StrEnum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    WATCH = "WATCH"
    AVOID = "AVOID"


# Ordered weakest -> strongest, used for ±1 band clamping by the Committee Chair.
RECOMMENDATION_LADDER: list[Recommendation] = [
    Recommendation.AVOID,
    Recommendation.WATCH,
    Recommendation.HOLD,
    Recommendation.BUY,
    Recommendation.STRONG_BUY,
]


class Signal(StrEnum):
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MarketRegime(StrEnum):
    RISK_ON = "risk_on"
    NEUTRAL = "neutral"
    RISK_OFF = "risk_off"
    LATE_CYCLE = "late_cycle"


class AgentName(StrEnum):
    NEWS = "news"
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    MACRO = "macro"
    RISK = "risk"
    PORTFOLIO_FIT = "portfolio_fit"


class NotificationPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class RiskTolerance(StrEnum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class TimeHorizon(StrEnum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class NewsCategory(StrEnum):
    COMPANY = "company"
    MACRO = "macro"
    ANALYST = "analyst"
