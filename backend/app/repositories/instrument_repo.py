from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, or_, select

from app.db.models.instrument import Instrument
from app.repositories.base import BaseRepository


class InstrumentRepository(BaseRepository):
    async def get_by_id(self, instrument_id: uuid.UUID) -> Instrument | None:
        return await self.session.get(Instrument, instrument_id)

    async def get_by_symbol(self, symbol: str) -> Instrument | None:
        stmt = select(Instrument).where(Instrument.symbol == symbol.upper())
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_by_ids(self, ids: Sequence[uuid.UUID]) -> list[Instrument]:
        if not ids:
            return []
        stmt = select(Instrument).where(Instrument.id.in_(ids))
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_active(self, limit: int = 60) -> list[Instrument]:
        stmt = (
            select(Instrument)
            .where(Instrument.is_active.is_(True))
            .order_by(Instrument.symbol)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def search(self, query: str, limit: int = 20) -> list[Instrument]:
        like = f"%{query.upper()}%"
        stmt = (
            select(Instrument)
            .where(
                Instrument.is_active.is_(True),
                or_(
                    func.upper(Instrument.symbol).like(like),
                    func.upper(Instrument.name).like(like),
                ),
            )
            .order_by(Instrument.symbol)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_or_create(
        self,
        *,
        symbol: str,
        name: str | None = None,
        type_: str = "stock",
        exchange: str | None = None,
        sector: str | None = None,
    ) -> Instrument:
        existing = await self.get_by_symbol(symbol)
        if existing:
            return existing
        instrument = Instrument(
            symbol=symbol.upper(),
            name=name or symbol.upper(),
            type=type_,
            exchange=exchange,
            sector=sector,
            currency="USD",
            is_active=True,
        )
        self.session.add(instrument)
        await self.session.flush()
        return instrument
