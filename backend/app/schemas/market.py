from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import InstrumentType


class InstrumentOut(BaseModel):
    id: uuid.UUID
    symbol: str
    name: str
    type: InstrumentType
    exchange: str | None = None
    sector: str | None = None
    currency: str = "USD"


class SearchResponse(BaseModel):
    results: list[InstrumentOut]


class QuoteOut(BaseModel):
    symbol: str
    price: float
    change: float | None = None
    change_pct: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    prev_close: float | None = None
    volume: float | None = None
    as_of: datetime | None = None


class CandleOut(BaseModel):
    t: datetime
    o: float
    h: float
    l: float  # noqa: E741
    c: float
    v: float | None = None


class CandleSeriesOut(BaseModel):
    symbol: str
    resolution: str
    candles: list[CandleOut]
