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
        # 1) Local seeded/known instruments first (fast, always available).
        instruments = await self._instruments.search(query, limit)
        seen = {i.symbol.upper() for i in instruments}

        # 2) Top up from the live provider symbol search so the whole US market is
        #    reachable — not just the seeded universe. New hits are persisted so the
        #    detail/quote/AI pages work when the user opens them.
        if len(instruments) < limit and len(query.strip()) >= 1:
            try:
                hits = await self._market.search_symbols(query, limit)
            except Exception:  # noqa: BLE001 - search is best-effort; never break the page
                hits = []
            for hit in hits:
                if hit.symbol.upper() in seen:
                    continue
                instrument = await self._instruments.get_or_create(
                    symbol=hit.symbol, name=hit.name, type_=hit.type, exchange=hit.exchange
                )
                instruments.append(instrument)
                seen.add(hit.symbol.upper())
                if len(instruments) >= limit:
                    break

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
