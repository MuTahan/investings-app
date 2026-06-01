from __future__ import annotations

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict, Forbidden, NotFound, ProviderError
from app.db.models.portfolio import Holding
from app.providers.router import MarketDataRouter
from app.repositories.instrument_repo import InstrumentRepository
from app.repositories.portfolio_repo import PortfolioRepository
from app.schemas.market import InstrumentOut
from app.schemas.portfolio import HoldingOut, PortfolioOut, PortfolioSummary


class PortfolioService:
    def __init__(self, session: AsyncSession, market: MarketDataRouter) -> None:
        self._repo = PortfolioRepository(session)
        self._instruments = InstrumentRepository(session)
        self._market = market

    async def _price(self, symbol: str, fallback: float) -> float:
        try:
            quote = await self._market.get_quote(symbol)
            return quote.price
        except ProviderError:
            return fallback  # use cost basis when live price is unavailable

    async def get(self, user_id: uuid.UUID) -> PortfolioOut:
        portfolio = await self._repo.get_or_create_default(user_id)
        holdings = portfolio.holdings

        prices = await asyncio.gather(
            *(self._price(h.instrument.symbol, float(h.avg_cost)) for h in holdings)
        )

        holding_views: list[HoldingOut] = []
        total_value = 0.0
        total_cost = 0.0
        sector_value: dict[str, float] = {}

        for holding, price in zip(holdings, prices, strict=False):
            qty = float(holding.quantity)
            avg_cost = float(holding.avg_cost)
            market_value = price * qty
            cost = avg_cost * qty
            total_value += market_value
            total_cost += cost
            sector = holding.instrument.sector or (
                "ETF" if holding.instrument.type == "etf" else "Other"
            )
            sector_value[sector] = sector_value.get(sector, 0.0) + market_value
            holding_views.append(self._holding_out(holding, price, market_value, cost))

        # second pass to set weights now that total is known
        for view in holding_views:
            view.weight = round(view.market_value / total_value, 4) if total_value else 0.0

        summary = self._summary(total_value, total_cost, sector_value, holding_views)
        return PortfolioOut(
            id=portfolio.id, name=portfolio.name, summary=summary, holdings=holding_views
        )

    @staticmethod
    def _holding_out(
        holding: Holding, price: float, market_value: float, cost: float
    ) -> HoldingOut:
        pl = market_value - cost
        return HoldingOut(
            id=holding.id,
            instrument=InstrumentOut(
                id=holding.instrument.id,
                symbol=holding.instrument.symbol,
                name=holding.instrument.name,
                type=holding.instrument.type,
                exchange=holding.instrument.exchange,
                sector=holding.instrument.sector,
                currency=holding.instrument.currency,
            ),
            quantity=float(holding.quantity),
            avg_cost=float(holding.avg_cost),
            market_value=round(market_value, 2),
            unrealized_pl=round(pl, 2),
            unrealized_pl_pct=round(pl / cost * 100, 2) if cost else 0.0,
        )

    @staticmethod
    def _summary(
        total_value: float,
        total_cost: float,
        sector_value: dict[str, float],
        holdings: list[HoldingOut],
    ) -> PortfolioSummary:
        pl = total_value - total_cost
        # Diversification = 1 - Herfindahl index of position weights, scaled 0..100.
        if total_value > 0 and holdings:
            hhi = sum((h.market_value / total_value) ** 2 for h in holdings)
            diversification = round((1 - hhi) * 100, 1)
        else:
            diversification = 0.0
        exposure = (
            {k: round(v / total_value, 4) for k, v in sector_value.items()} if total_value else {}
        )
        return PortfolioSummary(
            market_value=round(total_value, 2),
            cost_basis=round(total_cost, 2),
            unrealized_pl=round(pl, 2),
            unrealized_pl_pct=round(pl / total_cost * 100, 2) if total_cost else 0.0,
            diversification_score=diversification,
            sector_exposure=exposure,
        )

    async def add_holding(
        self, user_id: uuid.UUID, symbol: str, quantity: float, avg_cost: float
    ) -> None:
        instrument = await self._instruments.get_by_symbol(symbol)
        if instrument is None:
            raise NotFound(f"Unknown symbol '{symbol}'.")
        portfolio = await self._repo.get_or_create_default(user_id)
        if await self._repo.get_holding_by_instrument(portfolio.id, instrument.id):
            raise Conflict(f"{symbol.upper()} is already held; update it instead.")
        await self._repo.add_holding(portfolio.id, instrument.id, quantity, avg_cost)

    async def update_holding(
        self, user_id: uuid.UUID, holding_id: uuid.UUID, quantity: float, avg_cost: float
    ) -> None:
        holding = await self._owned_holding(user_id, holding_id)
        holding.quantity = quantity
        holding.avg_cost = avg_cost
        await self._repo.flush()

    async def delete_holding(self, user_id: uuid.UUID, holding_id: uuid.UUID) -> None:
        holding = await self._owned_holding(user_id, holding_id)
        await self._repo.delete_holding(holding)

    async def _owned_holding(self, user_id: uuid.UUID, holding_id: uuid.UUID) -> Holding:
        holding = await self._repo.get_holding(holding_id)
        if holding is None:
            raise NotFound("Holding not found.")
        portfolio = await self._repo.get_or_create_default(user_id)
        if holding.portfolio_id != portfolio.id:
            raise Forbidden("This holding does not belong to you.")
        return holding
