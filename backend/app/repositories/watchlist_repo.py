from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.watchlist import Watchlist, WatchlistItem
from app.repositories.base import BaseRepository


class WatchlistRepository(BaseRepository):
    async def get_or_create_default(self, user_id: uuid.UUID) -> Watchlist:
        stmt = (
            select(Watchlist)
            .where(Watchlist.user_id == user_id)
            .options(selectinload(Watchlist.items).selectinload(WatchlistItem.instrument))
            .order_by(Watchlist.created_at)
        )
        watchlist = (await self.session.execute(stmt)).scalars().first()
        if watchlist is None:
            watchlist = Watchlist(user_id=user_id)
            self.session.add(watchlist)
            await self.session.flush()
            await self.session.refresh(watchlist, attribute_names=["items"])
        return watchlist

    async def get_item(
        self, watchlist_id: uuid.UUID, instrument_id: uuid.UUID
    ) -> WatchlistItem | None:
        stmt = select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.instrument_id == instrument_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def add_item(self, watchlist_id: uuid.UUID, instrument_id: uuid.UUID) -> WatchlistItem:
        item = WatchlistItem(watchlist_id=watchlist_id, instrument_id=instrument_id)
        self.session.add(item)
        await self.session.flush()
        return item

    async def remove_item(self, watchlist_id: uuid.UUID, instrument_id: uuid.UUID) -> bool:
        item = await self.get_item(watchlist_id, instrument_id)
        if item is None:
            return False
        await self.session.delete(item)
        await self.session.flush()
        return True
