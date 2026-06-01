from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.portfolio import Holding, Portfolio
from app.repositories.base import BaseRepository


class PortfolioRepository(BaseRepository):
    async def get_or_create_default(self, user_id: uuid.UUID) -> Portfolio:
        stmt = (
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .options(selectinload(Portfolio.holdings).selectinload(Holding.instrument))
            .order_by(Portfolio.created_at)
        )
        portfolio = (await self.session.execute(stmt)).scalars().first()
        if portfolio is None:
            portfolio = Portfolio(user_id=user_id)
            self.session.add(portfolio)
            await self.session.flush()
            await self.session.refresh(portfolio, attribute_names=["holdings"])
        return portfolio

    async def get_holding(self, holding_id: uuid.UUID) -> Holding | None:
        stmt = (
            select(Holding)
            .where(Holding.id == holding_id)
            .options(selectinload(Holding.instrument))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_holding_by_instrument(
        self, portfolio_id: uuid.UUID, instrument_id: uuid.UUID
    ) -> Holding | None:
        stmt = select(Holding).where(
            Holding.portfolio_id == portfolio_id,
            Holding.instrument_id == instrument_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def add_holding(
        self,
        portfolio_id: uuid.UUID,
        instrument_id: uuid.UUID,
        quantity: float,
        avg_cost: float,
    ) -> Holding:
        holding = Holding(
            portfolio_id=portfolio_id,
            instrument_id=instrument_id,
            quantity=quantity,
            avg_cost=avg_cost,
        )
        self.session.add(holding)
        await self.session.flush()
        return holding

    async def delete_holding(self, holding: Holding) -> None:
        await self.session.delete(holding)
        await self.session.flush()
