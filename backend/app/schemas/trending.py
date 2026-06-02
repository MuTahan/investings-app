from __future__ import annotations

from pydantic import BaseModel

from app.domain.enums import InstrumentType, Signal


class TrendingItem(BaseModel):
    id: str
    symbol: str
    name: str
    type: InstrumentType
    price: float | None = None
    change_pct: float | None = None
    sentiment: Signal = Signal.NEUTRAL
    trend_score: float = 50.0
    summary: str = ""


class TrendingResponse(BaseModel):
    category: str
    items: list[TrendingItem]
