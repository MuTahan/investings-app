from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.device import NotificationLog
from app.db.models.instrument import Instrument
from app.db.models.recommendation import Recommendation
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    async def add(
        self, user_id: uuid.UUID, recommendation_id: uuid.UUID, status: str
    ) -> NotificationLog:
        log = NotificationLog(user_id=user_id, recommendation_id=recommendation_id, status=status)
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
