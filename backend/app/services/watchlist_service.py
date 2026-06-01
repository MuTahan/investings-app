from __future__ import annotations

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict, NotFound, ProviderError
from app.providers.router import MarketDataRouter
from app.repositories.instrument_repo import InstrumentRepository
from app.repositories.watchlist_repo import WatchlistRepository
from app.schemas.market import InstrumentOut, QuoteOut
from app.schemas.watchlist import WatchlistItemOut, WatchlistOut


class WatchlistService:
    def __init__(self, session: AsyncSession, market: MarketDataRouter) -> None:
        self._repo = WatchlistRepository(session)
        self._instruments = InstrumentRepository(session)
        self._market = market

    async def _quote_or_none(self, symbol: str) -> QuoteOut | None:
        try:
            quote = await self._market.get_quote(symbol)
            return QuoteOut(**quote.model_dump())
        except ProviderError:
            return None

    async def get(self, user_id: uuid.UUID) -> WatchlistOut:
        watchlist = await self._repo.get_or_create_default(user_id)
        instruments = [item.instrument for item in watchlist.items]
        quotes = await asyncio.gather(*(self._quote_or_none(i.symbol) for i in instruments))
        items = [
            WatchlistItemOut(
                instrument=InstrumentOut(
                    id=item.instrument.id,
                    symbol=item.instrument.symbol,
                    name=item.instrument.name,
                    type=item.instrument.type,
                    exchange=item.instrument.exchange,
                    sector=item.instrument.sector,
                    currency=item.instrument.currency,
                ),
                quote=quote,
                added_at=item.added_at,
            )
            for item, quote in zip(watchlist.items, quotes, strict=False)
        ]
        return WatchlistOut(id=str(watchlist.id), name=watchlist.name, items=items)

    async def add(self, user_id: uuid.UUID, symbol: str) -> None:
        instrument = await self._instruments.get_by_symbol(symbol)
        if instrument is None:
            raise NotFound(f"Unknown symbol '{symbol}'. Add it to the catalog first.")
        watchlist = await self._repo.get_or_create_default(user_id)
        if await self._repo.get_item(watchlist.id, instrument.id):
            raise Conflict(f"{symbol.upper()} is already in your watchlist.")
        await self._repo.add_item(watchlist.id, instrument.id)

    async def remove(self, user_id: uuid.UUID, instrument_id: uuid.UUID) -> None:
        watchlist = await self._repo.get_or_create_default(user_id)
        removed = await self._repo.remove_item(watchlist.id, instrument_id)
        if not removed:
            raise NotFound("Item not in watchlist.")
