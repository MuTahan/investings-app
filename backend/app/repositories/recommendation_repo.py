from __future__ import annotations

import uuid
from datetime import UTC, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.base import utcnow
from app.db.models.recommendation import AgentOutput, Recommendation
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository):
    async def latest(self, user_id: uuid.UUID, instrument_id: uuid.UUID) -> Recommendation | None:
        stmt = (
            select(Recommendation)
            .where(
                Recommendation.user_id == user_id,
                Recommendation.instrument_id == instrument_id,
            )
            .options(selectinload(Recommendation.agent_outputs))
            .order_by(Recommendation.generated_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def latest_if_fresh(
        self, user_id: uuid.UUID, instrument_id: uuid.UUID, max_age_seconds: int
    ) -> Recommendation | None:
        reco = await self.latest(user_id, instrument_id)
        if reco is None:
            return None
        generated = reco.generated_at
        if generated.tzinfo is None:
            generated = generated.replace(tzinfo=UTC)
        if utcnow() - generated <= timedelta(seconds=max_age_seconds):
            return reco
        return None

    async def history(
        self, user_id: uuid.UUID, instrument_id: uuid.UUID, limit: int = 20
    ) -> list[Recommendation]:
        stmt = (
            select(Recommendation)
            .where(
                Recommendation.user_id == user_id,
                Recommendation.instrument_id == instrument_id,
            )
            .order_by(Recommendation.generated_at.desc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def add(
        self, recommendation: Recommendation, agent_outputs: list[AgentOutput]
    ) -> Recommendation:
        recommendation.agent_outputs = agent_outputs
        self.session.add(recommendation)
        await self.session.flush()
        return recommendation
