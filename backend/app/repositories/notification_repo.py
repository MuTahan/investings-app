from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.device import NotificationLog, NotificationPreference
from app.db.models.instrument import Instrument
from app.db.models.recommendation import Recommendation
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    async def add(
        self,
        user_id: uuid.UUID,
        recommendation_id: uuid.UUID | None,
        status: str,
        category: str = "rating_change",
    ) -> NotificationLog:
        log = NotificationLog(
            user_id=user_id,
            recommendation_id=recommendation_id,
            status=status,
            category=category,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_for_user(
        self, user_id: uuid.UUID, limit: int = 50
    ) -> list[tuple[NotificationLog, Recommendation | None, str | None]]:
        stmt = (
            select(NotificationLog, Recommendation)
            .outerjoin(Recommendation, NotificationLog.recommendation_id == Recommendation.id)
            .options(selectinload(Recommendation.agent_outputs))
            .where(NotificationLog.user_id == user_id)
            .order_by(NotificationLog.sent_at.desc())
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).all()
        result: list[tuple[NotificationLog, Recommendation | None, str | None]] = []
        for log, rec in rows:
            symbol = None
            if rec is not None:
                instrument = await self.session.get(Instrument, rec.instrument_id)
                symbol = instrument.symbol if instrument else None
            result.append((log, rec, symbol))
        return result


class NotificationPreferenceRepository(BaseRepository):
    async def get_or_create(self, user_id: uuid.UUID) -> NotificationPreference:
        pref = await self.session.get(NotificationPreference, user_id)
        if pref is None:
            pref = NotificationPreference(user_id=user_id)
            self.session.add(pref)
            await self.session.flush()
        return pref

    async def upsert(
        self,
        user_id: uuid.UUID,
        *,
        categories: list[str],
        min_priority: str,
        max_risk: str,
        sectors: list[str],
        quiet_hours_start: int | None,
        quiet_hours_end: int | None,
    ) -> NotificationPreference:
        pref = await self.get_or_create(user_id)
        pref.categories = categories
        pref.min_priority = min_priority
        pref.max_risk = max_risk
        pref.sectors = sectors
        pref.quiet_hours_start = quiet_hours_start
        pref.quiet_hours_end = quiet_hours_end
        await self.session.flush()
        return pref
