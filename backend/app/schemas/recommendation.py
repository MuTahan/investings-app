from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import (
    NotificationPriority,
    Recommendation,
    RiskLevel,
    Signal,
    TimeHorizon,
)


class ReasonOut(BaseModel):
    label: str
    detail: str


class RiskOut(BaseModel):
    label: str
    detail: str
    severity: str = "low"


class PersonalizationOut(BaseModel):
    fit_score: float | None = None
    fit_reason: str | None = None


class AgentBreakdownOut(BaseModel):
    agent: str
    base_score: float | None = None
    score: float | None = None
    adjustment_delta: float = 0.0
    confidence: float
    signal: Signal | None = None
    explanation: str | None = None
    adjustment_justification: str | None = None
    risk_level: RiskLevel | None = None
    warnings: list[str] = []


class ValuationOut(BaseModel):
    fair_value: float | None = None
    valuation_gap_pct: float | None = None  # +ve = undervalued (upside to fair value)
    margin_of_safety_pct: float | None = None
    entry_low: float | None = None
    entry_high: float | None = None
    target_price: float | None = None
    stop_loss: float | None = None
    holding_period: str | None = None


class RecommendationOut(BaseModel):
    symbol: str
    rating: Recommendation
    anchor_rating: Recommendation
    confidence: float
    composite_score: float
    decision_mode: str
    time_horizon: TimeHorizon
    suggested_action: str | None = None
    chair_rationale: str | None = None
    reasons: list[ReasonOut] = []
    risks: list[RiskOut] = []
    personalization: PersonalizationOut | None = None
    valuation: ValuationOut | None = None
    agent_breakdown: list[AgentBreakdownOut] = []
    notif_priority: NotificationPriority = NotificationPriority.NORMAL
    weights_version: str = "v1"
    model_versions: dict[str, str] = {}
    generated_at: datetime


class RecommendationSummary(BaseModel):
    symbol: str
    rating: Recommendation
    confidence: float
    composite_score: float
    notif_priority: NotificationPriority
    generated_at: datetime


class RecommendationListResponse(BaseModel):
    items: list[RecommendationSummary]


class RecommendationCard(BaseModel):
    symbol: str
    name: str
    sector: str | None = None
    rating: Recommendation
    confidence: float
    composite_score: float
    time_horizon: TimeHorizon
    risk_level: RiskLevel | None = None
    valuation: ValuationOut | None = None
    reason: str | None = None
    fit_score: float | None = None
    notif_priority: NotificationPriority


class RecommendationCenterResponse(BaseModel):
    top_picks: list[RecommendationCard] = []
    short_term: list[RecommendationCard] = []
    long_term: list[RecommendationCard] = []
    trending: list[RecommendationCard] = []
    personalized: list[RecommendationCard] = []
