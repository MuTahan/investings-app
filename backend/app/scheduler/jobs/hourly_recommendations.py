"""Hourly job: recompute recommendations and notify on high-priority changes."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.core.logging import get_logger
from app.providers.container import ProviderContainer
from app.services.notification_service import NotificationService

logger = get_logger("scheduler.job")


async def run_job(
    sessionmaker: async_sessionmaker[AsyncSession],
    providers: ProviderContainer,
    settings: Settings,
) -> None:
    async with sessionmaker() as session:
        try:
            service = NotificationService(session, providers, settings)
            result = await service.run_hourly()
            await session.commit()
            logger.info(
                "hourly_job_done",
                extra={"evaluated": result.evaluated, "sent": result.sent},
            )
        except Exception:
            await session.rollback()
            logger.exception("hourly_job_failed")
