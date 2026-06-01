from __future__ import annotations

import uuid

from sqlalchemy import select

from app.db.models.news import NewsItem
from app.repositories.base import BaseRepository


class NewsRepository(BaseRepository):
    async def list_for_instrument(
        self, instrument_id: uuid.UUID | None, category: str | None, limit: int = 20
    ) -> list[NewsItem]:
        stmt = select(NewsItem)
        if instrument_id is not None:
            stmt = stmt.where(NewsItem.instrument_id == instrument_id)
        else:
            stmt = stmt.where(NewsItem.instrument_id.is_(None))
        if category is not None:
            stmt = stmt.where(NewsItem.category == category)
        stmt = stmt.order_by(NewsItem.published_at.desc().nullslast()).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_by_url(self, url: str) -> NewsItem | None:
        stmt = select(NewsItem).where(NewsItem.url == url)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def upsert(self, item: NewsItem) -> NewsItem:
        """Insert if the URL is new; ignore duplicates (URL is unique)."""
        existing = await self.get_by_url(item.url)
        if existing is not None:
            return existing
        self.session.add(item)
        await self.session.flush()
        return item
