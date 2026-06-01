from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.logging import get_logger
from app.db.models.user import User
from app.domain.enums import NotificationPriority, Recommendation
from app.notifications.builder import build as build_notification
from app.providers.container import ProviderContainer
from app.repositories.instrument_repo import InstrumentRepository
from app.repositories.notification_repo import NotificationRepository
from app.repositories.portfolio_repo import PortfolioRepository
from app.repositories.recommendation_repo import RecommendationRepository
from app.repositories.user_repo import UserRepository
from app.repositories.watchlist_repo import WatchlistRepository
from app.schemas.notification import NotificationFeedItem, RunResult
from app.services.recommendation_service import RecommendationService

logger = get_logger("notifications.service")

_PRIORITY_ORDER = [
    NotificationPriority.LOW,
    NotificationPriority.NORMAL,
    NotificationPriority.HIGH,
    NotificationPriority.CRITICAL,
]


class NotificationService:
    def __init__(
        self, session: AsyncSession, providers: ProviderContainer, settings: Settings
    ) -> None:
        self._session = session
        self._providers = providers
        self._settings = settings
        self._instruments = InstrumentRepository(session)
        self._reco_repo = RecommendationRepository(session)
        self._notif_repo = NotificationRepository(session)
        self._reco_service = RecommendationService(session, providers, settings)

    # ---------- public ----------
    async def run_hourly(self) -> RunResult:
        if self._in_quiet_hours():
            logger.info("scheduler_quiet_hours_skip")
            return RunResult(evaluated=0, sent=0, skipped_quiet_hours=True)
        users = await UserRepository(self._session).list_active()
        evaluated = 0
        sent = 0
        for user in users:
            result = await self.run_for_user(user)
            evaluated += result.evaluated
            sent += result.sent
        logger.info("scheduler_run_complete", extra={"users": len(users), "sent": sent})
        return RunResult(evaluated=evaluated, sent=sent)

    async def run_for_user(self, user: User) -> RunResult:
        if self._in_quiet_hours():
            return RunResult(evaluated=0, sent=0, skipped_quiet_hours=True)
        symbols = await self._symbols_for(user)
        evaluated = 0
        sent = 0
        for symbol in symbols:
            instrument = await self._instruments.get_by_symbol(symbol)
            if instrument is None:
                continue
            out = await self._reco_service.get(user, symbol, refresh=True)
            evaluated += 1
            if sent < self._settings.notify_max_per_run and self._eligible(out.notif_priority):
                rec = await self._reco_repo.latest(user.id, instrument.id)
                notification = build_notification(out, app_base_url=self._settings.app_base_url)
                ok = await self._providers.notifier.send(notification)
                await self._notif_repo.add(
                    user.id, rec.id if rec else None, "sent" if ok else "failed"
                )
                sent += 1
        return RunResult(evaluated=evaluated, sent=sent)

    async def list_feed(self, user: User, limit: int = 50) -> list[NotificationFeedItem]:
        rows = await self._notif_repo.list_for_user(user.id, limit)
        items: list[NotificationFeedItem] = []
        for log, rec, symbol in rows:
            items.append(
                NotificationFeedItem(
                    symbol=symbol,
                    rating=Recommendation(rec.rating) if rec else None,
                    sent_at=log.sent_at,
                    status=log.status,
                )
            )
        return items

    # ---------- internals ----------
    async def _symbols_for(self, user: User) -> list[str]:
        watchlist = await WatchlistRepository(self._session).get_or_create_default(user.id)
        portfolio = await PortfolioRepository(self._session).get_or_create_default(user.id)
        symbols = {item.instrument.symbol for item in watchlist.items}
        symbols.update(h.instrument.symbol for h in portfolio.holdings)
        return sorted(symbols)

    def _eligible(self, priority: NotificationPriority) -> bool:
        threshold = NotificationPriority(self._settings.notify_min_priority)
        return _PRIORITY_ORDER.index(priority) >= _PRIORITY_ORDER.index(threshold)

    def _in_quiet_hours(self) -> bool:
        start = self._settings.quiet_hours_start
        end = self._settings.quiet_hours_end
        if start is None or end is None:
            return False
        hour = datetime.now(UTC).hour
        if start == end:
            return False
        if start < end:
            return start <= hour < end
        return hour >= start or hour < end  # overnight window
