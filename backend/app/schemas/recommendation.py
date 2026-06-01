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
