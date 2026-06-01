from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

from app.domain.enums import RiskTolerance, TimeHorizon


class RiskProfileOut(BaseModel):
    risk_tolerance: RiskTolerance
    time_horizon: TimeHorizon
    objectives: list[str] = []
    max_position_pct: float | None = None


class RiskProfileUpdate(BaseModel):
    risk_tolerance: RiskTolerance
    time_horizon: TimeHorizon
    objectives: list[str] = Field(default_factory=list, max_length=10)
    max_position_pct: float | None = Field(default=None, ge=0, le=100)


class MeResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr | None = None
    display_name: str | None = None
    risk_profile: RiskProfileOut | None = None
