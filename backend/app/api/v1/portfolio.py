from __future__ import annotations

import uuid

from fastapi import APIRouter, Response, status

from app.deps import CurrentUserDep, ProvidersDep, SessionDep
from app.schemas.common import Message
from app.schemas.portfolio import (
    AddHoldingRequest,
    PortfolioOut,
    UpdateHoldingRequest,
)
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioOut)
async def get_portfolio(
    user: CurrentUserDep, session: SessionDep, providers: ProvidersDep
) -> PortfolioOut:
    return await PortfolioService(session, providers.market).get(user.id)


@router.post("/holdings", response_model=Message, status_code=status.HTTP_201_CREATED)
async def add_holding(
    req: AddHoldingRequest,
    user: CurrentUserDep,
    session: SessionDep,
    providers: ProvidersDep,
) -> Message:
    await PortfolioService(session, providers.market).add_holding(
        user.id, req.symbol, req.quantity, req.avg_cost
    )
    return Message(message=f"{req.symbol.upper()} added to portfolio.")


@router.put("/holdings/{holding_id}", response_model=Message)
async def update_holding(
    holding_id: uuid.UUID,
    req: UpdateHoldingRequest,
    user: CurrentUserDep,
    session: SessionDep,
    providers: ProvidersDep,
) -> Message:
    await PortfolioService(session, providers.market).update_holding(
        user.id, holding_id, req.quantity, req.avg_cost
    )
    return Message(message="Holding updated.")


@router.delete(
    "/holdings/{holding_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_holding(
    holding_id: uuid.UUID,
    user: CurrentUserDep,
    session: SessionDep,
    providers: ProvidersDep,
) -> Response:
    await PortfolioService(session, providers.market).delete_holding(user.id, holding_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
