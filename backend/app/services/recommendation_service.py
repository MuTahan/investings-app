from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import (
    HoldingInfo,
    InstrumentInfo,
    PortfolioSnapshot,
    RiskProfileInfo,
)
from app.ai.committee import CommitteeResult, InvestmentCommittee
from app.ai.context import ContextBuilder, build_macro
from app.config import Settings
from app.core.exceptions import NotFound
from app.db.models.recommendation import AgentOutput
from app.db.models.recommendation import Recommendation as RecommendationModel
from app.db.models.user import User
from app.domain.enums import Recommendation as Rating
from app.domain.enums import TimeHorizon
from app.providers.container import ProviderContainer
from app.repositories.instrument_repo import InstrumentRepository
from app.repositories.portfolio_repo import PortfolioRepository
from app.repositories.recommendation_repo import RecommendationRepository
from app.repositories.watchlist_repo import WatchlistRepository
from app.schemas.recommendation import (
    AgentBreakdownOut,
    PersonalizationOut,
    RecommendationCard,
    RecommendationCenterResponse,
    RecommendationOut,
    RecommendationSummary,
    ValuationOut,
)

_committee = InvestmentCommittee()
_FRESHNESS_SECONDS = 3600
_BUY_RATINGS = {Rating.BUY, Rating.STRONG_BUY}
# Shown in the Recommendation Center when a user has no watchlist/portfolio yet, so
# the page is never empty. Kept small to bound AI calls (results are cached after the
# first compute). Add stocks to your watchlist to personalize beyond this.
_DEFAULT_UNIVERSE = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "SPY", "QQQ"]


class RecommendationService:
    def __init__(
        self, session: AsyncSession, providers: ProviderContainer, settings: Settings
    ) -> None:
        self._session = session
        self._providers = providers
        self._settings = settings
        self._instruments = InstrumentRepository(session)
        self._portfolios = PortfolioRepository(session)
        self._repo = RecommendationRepository(session)
        self._ctx_builder = ContextBuilder(providers.market)

    @property
    def _use_llm(self) -> bool:
        # Chair uses the LLM in both chair_assisted and empowered modes.
        return (
            self._settings.ai_decision_mode != "deterministic"
            and self._providers.llm.name != "stub"
        )

    @property
    def _agents_use_llm(self) -> bool:
        # Only "empowered" sends the 6 agents to the LLM (7 calls/recommendation);
        # "chair_assisted" keeps agents deterministic and uses the LLM only for the
        # Chair (1 call) — far gentler on rate-limited free tiers.
        return self._use_llm and self._settings.ai_decision_mode == "empowered"

    async def get(self, user: User, symbol: str, refresh: bool = False) -> RecommendationOut:
        instrument = await self._instruments.get_by_symbol(symbol)
        if instrument is None:
            raise NotFound(f"Unknown symbol '{symbol}'.")

        if not refresh:
            fresh = await self._repo.latest_if_fresh(user.id, instrument.id, _FRESHNESS_SECONDS)
            if fresh is not None:
                return self._orm_to_out(fresh, instrument.symbol)

        result = await self._evaluate(user, instrument)
        stored = await self._persist(user, instrument.id, result)
        return self._result_to_out(instrument.symbol, result, stored.generated_at)

    async def list_scope(self, user: User, scope: str) -> list[RecommendationSummary]:
        portfolio = await self._portfolios.get_or_create_default(user.id)
        if scope == "portfolio":
            symbols = [h.instrument.symbol for h in portfolio.holdings]
        else:
            from app.repositories.watchlist_repo import WatchlistRepository

            watchlist = await WatchlistRepository(self._session).get_or_create_default(user.id)
            symbols = [item.instrument.symbol for item in watchlist.items]

        summaries: list[RecommendationSummary] = []
        for symbol in symbols:
            out = await self.get(user, symbol, refresh=False)
            summaries.append(
                RecommendationSummary(
                    symbol=out.symbol,
                    rating=out.rating,
                    confidence=out.confidence,
                    composite_score=out.composite_score,
                    notif_priority=out.notif_priority,
                    generated_at=out.generated_at,
                )
            )
        return summaries

    async def history(
        self, user: User, symbol: str, limit: int = 20
    ) -> list[RecommendationSummary]:
        instrument = await self._instruments.get_by_symbol(symbol)
        if instrument is None:
            raise NotFound(f"Unknown symbol '{symbol}'.")
        records = await self._repo.history(user.id, instrument.id, limit)
        return [
            RecommendationSummary(
                symbol=instrument.symbol,
                rating=Rating(r.rating),
                confidence=float(r.confidence),
                composite_score=float(r.composite_score),
                notif_priority=r.notif_priority,
                generated_at=r.generated_at,
            )
            for r in records
        ]

    async def center(
        self,
        user: User,
        *,
        horizon: str | None = None,
        risk: str | None = None,
        sector: str | None = None,
        rec_type: str | None = None,
        min_confidence: float = 0.0,
    ) -> RecommendationCenterResponse:
        cards: list[RecommendationCard] = []
        symbols = await self._user_symbols(user)
        if not symbols:
            # Fresh account: show a default universe so Picks isn't empty.
            symbols = _DEFAULT_UNIVERSE
        for symbol in symbols:
            instrument = await self._instruments.get_by_symbol(symbol)
            if instrument is None:
                continue
            cards.append(self._to_card(await self.get(user, symbol), instrument))

        cards = [
            c
            for c in cards
            if (horizon is None or c.time_horizon.value == horizon)
            and (risk is None or (c.risk_level is not None and c.risk_level.value == risk))
            and (sector is None or (c.sector is not None and c.sector.lower() == sector.lower()))
            and (rec_type is None or c.rating.value == rec_type)
            and c.confidence >= min_confidence
        ]
        buys = [c for c in cards if c.rating in _BUY_RATINGS]

        def by_conf(items: list[RecommendationCard]) -> list[RecommendationCard]:
            return sorted(items, key=lambda c: c.confidence, reverse=True)[:8]

        return RecommendationCenterResponse(
            top_picks=by_conf(buys),
            short_term=by_conf(
                [c for c in buys if c.time_horizon in (TimeHorizon.SHORT, TimeHorizon.MEDIUM)]
            ),
            long_term=by_conf([c for c in buys if c.time_horizon == TimeHorizon.LONG]),
            trending=sorted(cards, key=lambda c: c.composite_score, reverse=True)[:8],
            personalized=sorted(cards, key=lambda c: c.fit_score or 0.0, reverse=True)[:8],
        )

    async def _user_symbols(self, user: User) -> list[str]:
        portfolio = await self._portfolios.get_or_create_default(user.id)
        watchlist = await WatchlistRepository(self._session).get_or_create_default(user.id)
        symbols = {item.instrument.symbol for item in watchlist.items}
        symbols.update(h.instrument.symbol for h in portfolio.holdings)
        return sorted(symbols)

    def _to_card(self, out: RecommendationOut, instrument) -> RecommendationCard:
        risk_level = next((a.risk_level for a in out.agent_breakdown if a.agent == "risk"), None)
        return RecommendationCard(
            symbol=out.symbol,
            name=instrument.name,
            sector=instrument.sector,
            rating=out.rating,
            confidence=out.confidence,
            composite_score=out.composite_score,
            time_horizon=out.time_horizon,
            risk_level=risk_level,
            valuation=out.valuation,
            reason=out.reasons[0].detail if out.reasons else None,
            fit_score=out.personalization.fit_score if out.personalization else None,
            notif_priority=out.notif_priority,
        )

    # ---------------- internals ----------------
    async def _evaluate(self, user: User, instrument) -> CommitteeResult:
        profile = self._profile(user)
        portfolio = await self._portfolio_snapshot(user)
        macro = await build_macro(self._providers.market)
        instrument_info = InstrumentInfo(
            symbol=instrument.symbol,
            name=instrument.name,
            type=instrument.type,
            sector=instrument.sector,
        )
        ctx = await self._ctx_builder.build(
            instrument=instrument_info,
            profile=profile,
            portfolio=portfolio,
            macro=macro,
            decision_mode=self._settings.ai_decision_mode,
            use_llm=self._use_llm,
            agents_use_llm=self._agents_use_llm,
            agent_model=self._settings.ai_agent_model,
        )
        previous = await self._repo.latest(user.id, instrument.id)
        prev_rating = Rating(previous.rating) if previous else None
        prev_score = float(previous.composite_score) if previous else None
        return await _committee.evaluate(
            ctx,
            self._providers.llm,
            chair_model=self._settings.ai_chair_model,
            previous_rating=prev_rating,
            previous_score=prev_score,
        )

    def _profile(self, user: User) -> RiskProfileInfo:
        rp = user.risk_profile
        if rp is None:
            return RiskProfileInfo()
        return RiskProfileInfo(
            risk_tolerance=rp.risk_tolerance,
            time_horizon=rp.time_horizon,
            objectives=rp.objectives or [],
            max_position_pct=(
                float(rp.max_position_pct) if rp.max_position_pct is not None else None
            ),
        )

    async def _portfolio_snapshot(self, user: User) -> PortfolioSnapshot:
        portfolio = await self._portfolios.get_or_create_default(user.id)
        holdings: list[HoldingInfo] = []
        total = 0.0
        raw: list[tuple[str, str | None, float]] = []
        for h in portfolio.holdings:
            value = float(h.quantity) * float(h.avg_cost)  # cost-basis proxy (no extra quote calls)
            total += value
            raw.append((h.instrument.symbol, h.instrument.sector, value))
        sector_exposure: dict[str, float] = {}
        for symbol, sector, value in raw:
            weight = value / total if total else 0.0
            holdings.append(HoldingInfo(symbol=symbol, sector=sector, value=value, weight=weight))
            key = sector or "Other"
            sector_exposure[key] = sector_exposure.get(key, 0.0) + weight
        return PortfolioSnapshot(
            holdings=holdings, sector_exposure=sector_exposure, total_value=total
        )

    async def _persist(
        self, user: User, instrument_id, result: CommitteeResult
    ) -> RecommendationModel:
        record = RecommendationModel(
            user_id=user.id,
            instrument_id=instrument_id,
            rating=result.rating.value,
            anchor_rating=result.anchor_rating.value,
            confidence=result.confidence,
            composite_score=result.composite_score,
            time_horizon=result.time_horizon.value,
            reasons=result.reasons,
            risks=result.risks,
            suggested_action=result.suggested_action,
            personalization=result.personalization,
            chair_rationale=result.chair_rationale,
            notif_priority=result.notif_priority.value,
            decision_mode=result.decision_mode,
            weights_version=result.weights_version,
            model_versions=result.model_versions,
            valuation=result.valuation,
        )
        outputs = []
        for r in result.agent_breakdown:
            payload = dict(r.payload)
            if r.risk_level is not None:
                payload["risk_level"] = r.risk_level.value
                payload["warnings"] = r.warnings
            outputs.append(
                AgentOutput(
                    agent=r.agent.value,
                    base_score=r.base_score,
                    score=r.score,
                    adjustment_delta=r.adjustment_delta,
                    confidence=r.confidence,
                    signal=r.signal.value if r.signal else None,
                    payload=payload,
                    explanation=r.explanation,
                    adjustment_justification=r.adjustment_justification,
                )
            )
        return await self._repo.add(record, outputs)

    def _result_to_out(
        self, symbol: str, result: CommitteeResult, generated_at: datetime
    ) -> RecommendationOut:
        return RecommendationOut(
            symbol=symbol,
            rating=result.rating,
            anchor_rating=result.anchor_rating,
            confidence=result.confidence,
            composite_score=result.composite_score,
            decision_mode=result.decision_mode,
            time_horizon=result.time_horizon,
            suggested_action=result.suggested_action,
            chair_rationale=result.chair_rationale,
            reasons=result.reasons,
            risks=result.risks,
            personalization=(
                PersonalizationOut(**result.personalization) if result.personalization else None
            ),
            valuation=ValuationOut(**result.valuation) if result.valuation else None,
            agent_breakdown=[
                AgentBreakdownOut(
                    agent=r.agent.value,
                    base_score=r.base_score,
                    score=r.score,
                    adjustment_delta=r.adjustment_delta,
                    confidence=r.confidence,
                    signal=r.signal,
                    explanation=r.explanation,
                    adjustment_justification=r.adjustment_justification,
                    risk_level=r.risk_level,
                    warnings=r.warnings,
                )
                for r in result.agent_breakdown
            ],
            notif_priority=result.notif_priority,
            weights_version=result.weights_version,
            model_versions=result.model_versions,
            generated_at=generated_at,
        )

    def _orm_to_out(self, rec: RecommendationModel, symbol: str) -> RecommendationOut:
        return RecommendationOut(
            symbol=symbol,
            rating=Rating(rec.rating),
            anchor_rating=Rating(rec.anchor_rating),
            confidence=float(rec.confidence),
            composite_score=float(rec.composite_score),
            decision_mode=rec.decision_mode,
            time_horizon=rec.time_horizon,
            suggested_action=rec.suggested_action,
            chair_rationale=rec.chair_rationale,
            reasons=rec.reasons or [],
            risks=rec.risks or [],
            personalization=(
                PersonalizationOut(**rec.personalization) if rec.personalization else None
            ),
            valuation=ValuationOut(**rec.valuation) if rec.valuation else None,
            agent_breakdown=[
                AgentBreakdownOut(
                    agent=ao.agent,
                    base_score=float(ao.base_score) if ao.base_score is not None else None,
                    score=float(ao.score) if ao.score is not None else None,
                    adjustment_delta=float(ao.adjustment_delta),
                    confidence=float(ao.confidence),
                    signal=ao.signal,
                    explanation=ao.explanation,
                    adjustment_justification=ao.adjustment_justification,
                    risk_level=(ao.payload or {}).get("risk_level"),
                    warnings=(ao.payload or {}).get("warnings", []),
                )
                for ao in rec.agent_outputs
            ],
            notif_priority=rec.notif_priority,
            weights_version=rec.weights_version,
            model_versions=rec.model_versions or {},
            generated_at=rec.generated_at,
        )
