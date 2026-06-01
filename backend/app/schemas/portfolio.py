from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.schemas.market import InstrumentOut


class HoldingOut(BaseModel):
    id: uuid.UUID
    instrument: InstrumentOut
    quantity: float
    avg_cost: float
    market_value: float | None = None
    unrealized_pl: float | None = None
    unrealized_pl_pct: float | None = None
    weight: float | None = None


class PortfolioSummary(BaseModel):
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_pl_pct: float
    diversification_score: float
    sector_exposure: dict[str, float] = {}


class PortfolioOut(BaseModel):
    id: uuid.UUID
    name: str
    summary: PortfolioSummary
    holdings: list[HoldingOut]


class AddHoldingRequest(BaseModel):
    symbol: str
    quantity: float = Field(gt=0)
    avg_cost: float = Field(ge=0)


class UpdateHoldingRequest(BaseModel):
    quantity: float = Field(gt=0)
    avg_cost: float = Field(ge=0)
