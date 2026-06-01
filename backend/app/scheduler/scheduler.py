"""JobScheduler interface + APScheduler implementation.

Behind an interface so the MVP's in-process AsyncIO scheduler can be swapped for
Celery/Redis later without touching job logic.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.logging import get_logger

logger = get_logger("scheduler")


class JobScheduler(Protocol):
    def add_interval_job(
        self, func: Callable[[], Awaitable[None]], minutes: int, job_id: str
    ) -> None: ...
    def start(self) -> None: ...
    def shutdown(self) -> None: ...


class APSchedulerJobScheduler:
    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler(timezone="UTC")

    def add_interval_job(
        self, func: Callable[[], Awaitable[None]], minutes: int, job_id: str
    ) -> None:
        self._scheduler.add_job(
            func,
            "interval",
            minutes=minutes,
            id=job_id,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    def start(self) -> None:
        self._scheduler.start()
        logger.info("scheduler_started")

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")
