from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound
from app.db.models.instrument import Instrument
from app.providers.router import MarketDataRouter
from app.repositories.instrument_repo import InstrumentRepository
from app.schemas.market import (
    CandleOut,
    CandleSeriesOut,
    InstrumentOut,
    QuoteOut,
)


class MarketService:
    def __init__(self, session: AsyncSession, market: MarketDataRouter) -> None:
        self._instruments = InstrumentRepository(session)
        self._market = market

    @staticmethod
    def _to_instrument_out(instrument: Instrument) -> InstrumentOut:
        return InstrumentOut(
            id=instrument.id,
            symbol=instrument.symbol,
            name=instrument.name,
            type=instrument.type,
            exchange=instrument.exchange,
            sector=instrument.sector,
            currency=instrument.currency,
        )

    async def search(self, query: str, limit: int = 20) -> list[InstrumentOut]:
        instruments = await self._instruments.search(query, limit)
        return [self._to_instrument_out(i) for i in instruments]

    async def get_instrument(self, symbol: str) -> InstrumentOut:
        instrument = await self._instruments.get_by_symbol(symbol)
        if instrument is None:
            raise NotFound(f"Unknown symbol '{symbol}'.")
        return self._to_instrument_out(instrument)

    async def get_quote(self, symbol: str) -> QuoteOut:
        quote = await self._market.get_quote(symbol)
        return QuoteOut(**quote.model_dump())

    async def get_candles(
        self, symbol: str, resolution: str, frm: datetime, to: datetime
    ) -> CandleSeriesOut:
        series = await self._market.get_candles(symbol, resolution, frm, to)
        return CandleSeriesOut(
            symbol=series.symbol,
            resolution=series.resolution,
            candles=[CandleOut(**c.model_dump()) for c in series.candles],
        )
