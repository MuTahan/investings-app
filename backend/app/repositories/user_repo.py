from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.user import User, UserRiskProfile
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.id == user_id).options(selectinload(User.risk_profile))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_active(self) -> list[User]:
        stmt = select(User).where(User.is_active.is_(True)).options(selectinload(User.risk_profile))
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_by_email(self, email: str) -> User | None:
        stmt = (
            select(User).where(User.email == email.lower()).options(selectinload(User.risk_profile))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_apple_sub(self, apple_sub: str) -> User | None:
        stmt = (
            select(User).where(User.apple_sub == apple_sub).options(selectinload(User.risk_profile))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(
        self,
        *,
        email: str | None = None,
        password_hash: str | None = None,
        apple_sub: str | None = None,
        display_name: str | None = None,
    ) -> User:
        user = User(
            email=email.lower() if email else None,
            password_hash=password_hash,
            apple_sub=apple_sub,
            display_name=display_name,
        )
        # default risk profile so personalization always has something to read
        user.risk_profile = UserRiskProfile()
        self.session.add(user)
        await self.session.flush()
        return user

    async def upsert_risk_profile(
        self,
        user: User,
        *,
        risk_tolerance: str,
        time_horizon: str,
        objectives: list[str],
        max_position_pct: float | None,
    ) -> UserRiskProfile:
        profile = user.risk_profile or UserRiskProfile(user_id=user.id)
        profile.risk_tolerance = risk_tolerance
        profile.time_horizon = time_horizon
        profile.objectives = objectives
        profile.max_position_pct = max_position_pct
        user.risk_profile = profile
        self.session.add(profile)
        await self.session.flush()
        return profile
