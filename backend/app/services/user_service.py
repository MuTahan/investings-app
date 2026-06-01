from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import MeResponse, RiskProfileOut, RiskProfileUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._users = UserRepository(session)

    def to_me(self, user: User) -> MeResponse:
        profile = None
        if user.risk_profile is not None:
            rp = user.risk_profile
            profile = RiskProfileOut(
                risk_tolerance=rp.risk_tolerance,
                time_horizon=rp.time_horizon,
                objectives=rp.objectives or [],
                max_position_pct=(
                    float(rp.max_position_pct) if rp.max_position_pct is not None else None
                ),
            )
        return MeResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            risk_profile=profile,
        )

    async def update_risk_profile(self, user: User, req: RiskProfileUpdate) -> RiskProfileOut:
        await self._users.upsert_risk_profile(
            user,
            risk_tolerance=req.risk_tolerance.value,
            time_horizon=req.time_horizon.value,
            objectives=req.objectives,
            max_position_pct=req.max_position_pct,
        )
        return RiskProfileOut(
            risk_tolerance=req.risk_tolerance,
            time_horizon=req.time_horizon,
            objectives=req.objectives,
            max_position_pct=req.max_position_pct,
        )
