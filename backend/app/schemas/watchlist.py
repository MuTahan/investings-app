from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.market import InstrumentOut, QuoteOut


class WatchlistItemOut(BaseModel):
    instrument: InstrumentOut
    quote: QuoteOut | None = None
    added_at: datetime | None = None


class WatchlistOut(BaseModel):
    id: str
    name: str
    items: list[WatchlistItemOut]


class AddWatchlistItemRequest(BaseModel):
    symbol: str
