from __future__ import annotations

from fastapi import APIRouter

from app.deps import CurrentUserDep, SessionDep
from app.schemas.user import MeResponse, RiskProfileOut, RiskProfileUpdate
from app.services.user_service import UserService

router = APIRouter(tags=["user"])


@router.get("/me", response_model=MeResponse)
async def get_me(user: CurrentUserDep, session: SessionDep) -> MeResponse:
    return UserService(session).to_me(user)


@router.put("/me/risk-profile", response_model=RiskProfileOut)
async def update_risk_profile(
    req: RiskProfileUpdate, user: CurrentUserDep, session: SessionDep
) -> RiskProfileOut:
    return await UserService(session).update_risk_profile(user, req)
