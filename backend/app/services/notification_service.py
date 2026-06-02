from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.news_impact import score_headline
from app.config import Settings
from app.core.logging import get_logger
from app.db.models.device import NotificationPreference
from app.db.models.user import User
from app.domain.enums import NotificationPriority, Recommendation, RiskLevel
from app.notifications.builder import build as build_notification
from app.notifications.notifier import Notification
from app.providers.container import ProviderContainer
from app.repositories.instrument_repo import InstrumentRepository
from app.repositories.notification_repo import (
    NotificationPreferenceRepository,
    NotificationRepository,
)
from app.repositories.portfolio_repo import PortfolioRepository
from app.repositories.recommendation_repo import RecommendationRepository
from app.repositories.user_repo import UserRepository
from app.repositories.watchlist_repo import WatchlistRepository
from app.schemas.notification import NotificationFeedItem, RunResult
from app.services.news_service import NewsService
from app.services.recommendation_service import RecommendationService

logger = get_logger("notifications.service")

_PRIORITY_ORDER = [
    NotificationPriority.LOW,
    NotificationPriority.NORMAL,
    NotificationPriority.HIGH,
    NotificationPriority.CRITICAL,
]
_RISK_ORDER = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]
_NEWS_IMPACT_THRESHOLD = 60  # |impact| of the strongest recent headline to trigger a news alert


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
        self._prefs_repo = NotificationPreferenceRepository(session)
        self._reco_service = RecommendationService(session, providers, settings)
        self._news = NewsService(session, providers.market)

    # ---------- public ----------
    async def run_hourly(self) -> RunResult:
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
        prefs = await self._prefs_repo.get_or_create(user.id)
        if self._in_quiet_hours(prefs):
            return RunResult(evaluated=0, sent=0, skipped_quiet_hours=True)

        cap = self._settings.notify_max_per_run
        news_on = not prefs.categories or "news" in prefs.categories
        evaluated = 0
        sent = 0
        for symbol in await self._symbols_for(user):
            instrument = await self._instruments.get_by_symbol(symbol)
            if instrument is None:
                continue
            out = await self._reco_service.get(user, symbol, refresh=True)
            evaluated += 1
            risk_level = next(
                (a.risk_level for a in out.agent_breakdown if a.agent == "risk"), None
            )
            rec = await self._reco_repo.latest(user.id, instrument.id)
            rec_id = rec.id if rec else None

            # 1) rating-change alert
            if sent < cap and self._eligible(
                prefs, out.notif_priority, "rating_change", instrument.sector, risk_level
            ):
                notification = build_notification(out, app_base_url=self._settings.app_base_url)
                ok = await self._providers.notifier.send(notification)
                await self._notif_repo.add(
                    user.id, rec_id, "sent" if ok else "failed", category="rating_change"
                )
                sent += 1

            # 2) news-impact alert
            if (
                news_on
                and sent < cap
                and self._eligible(
                    prefs, NotificationPriority.HIGH, "news", instrument.sector, risk_level
                )
            ):
                top = await self._top_news(symbol)
                if top is not None:
                    ok = await self._providers.notifier.send(top)
                    await self._notif_repo.add(
                        user.id, rec_id, "sent" if ok else "failed", category="news"
                    )
                    sent += 1
        return RunResult(evaluated=evaluated, sent=sent)

    async def send_test(self, user: User) -> RunResult:
        """Fire a fixed test alert through every configured channel + the in-app feed,
        so the user can confirm notifications work without waiting for the hourly job."""
        url = (
            f"{self._settings.app_base_url.rstrip('/')}/notifications"
            if self._settings.app_base_url
            else None
        )
        notification = Notification(
            title="Investing AI: test alert",
            body="✅ Notifications are working. Rating changes & news will arrive here.",
            priority="high",
            tag="TEST",
            click_url=url,
        )
        ok = await self._providers.notifier.send(notification)
        await self._notif_repo.add(user.id, None, "sent" if ok else "failed", category="test")
        return RunResult(evaluated=1, sent=1 if ok else 0)

    async def list_feed(self, user: User, limit: int = 50) -> list[NotificationFeedItem]:
        rows = await self._notif_repo.list_for_user(user.id, limit)
        return [
            NotificationFeedItem(
                symbol=symbol,
                rating=Recommendation(rec.rating) if rec else None,
                category=log.category,
                sent_at=log.sent_at,
                status=log.status,
            )
            for log, rec, symbol in rows
        ]

    # ---------- internals ----------
    async def _top_news(self, symbol: str) -> Notification | None:
        articles = await self._news.list(symbol, "company", 8)
        best = None
        best_abs = 0
        for a in articles:
            mag = abs(score_headline(a.headline))
            if mag > best_abs:
                best_abs, best = mag, a
        if best is None or best_abs < _NEWS_IMPACT_THRESHOLD:
            return None
        url = (
            f"{self._settings.app_base_url.rstrip('/')}/markets/{symbol.upper()}"
            if self._settings.app_base_url
            else None
        )
        return Notification(
            title=f"{symbol.upper()}: significant news",
            body=best.headline,
            priority="high",
            tag=symbol.upper(),
            click_url=url,
        )

    async def _symbols_for(self, user: User) -> list[str]:
        watchlist = await WatchlistRepository(self._session).get_or_create_default(user.id)
        portfolio = await PortfolioRepository(self._session).get_or_create_default(user.id)
        symbols = {item.instrument.symbol for item in watchlist.items}
        symbols.update(h.instrument.symbol for h in portfolio.holdings)
        return sorted(symbols)

    def _eligible(
        self,
        prefs: NotificationPreference,
        priority: NotificationPriority,
        category: str,
        sector: str | None,
        risk_level: RiskLevel | None,
    ) -> bool:
        if _PRIORITY_ORDER.index(priority) < _PRIORITY_ORDER.index(
            NotificationPriority(prefs.min_priority)
        ):
            return False
        if prefs.categories and category not in prefs.categories:
            return False
        if prefs.sectors and (sector or "") not in prefs.sectors:
            return False
        rl = risk_level or RiskLevel.LOW
        if _RISK_ORDER.index(rl) > _RISK_ORDER.index(RiskLevel(prefs.max_risk)):
            return False
        return True

    def _in_quiet_hours(self, prefs: NotificationPreference) -> bool:
        start = prefs.quiet_hours_start
        end = prefs.quiet_hours_end
        if start is None or end is None:
            return False
        hour = datetime.now(UTC).hour
        if start == end:
            return False
        if start < end:
            return start <= hour < end
        return hour >= start or hour < end  # overnight window
