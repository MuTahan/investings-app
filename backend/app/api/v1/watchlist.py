from __future__ import annotations

import uuid

from fastapi import APIRouter, Response, status

from app.deps import CurrentUserDep, ProvidersDep, SessionDep
from app.schemas.common import Message
from app.schemas.watchlist import AddWatchlistItemRequest, WatchlistOut
from app.services.watchlist_service import WatchlistService

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=WatchlistOut)
async def get_watchlist(
    user: CurrentUserDep, session: SessionDep, providers: ProvidersDep
) -> WatchlistOut:
    return await WatchlistService(session, providers.market).get(user.id)


@router.post("/items", response_model=Message, status_code=status.HTTP_201_CREATED)
async def add_item(
    req: AddWatchlistItemRequest,
    user: CurrentUserDep,
    session: SessionDep,
    providers: ProvidersDep,
) -> Message:
    await WatchlistService(session, providers.market).add(user.id, req.symbol)
    return Message(message=f"{req.symbol.upper()} added to watchlist.")


@router.delete(
    "/items/{instrument_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def remove_item(
    instrument_id: uuid.UUID,
    user: CurrentUserDep,
    session: SessionDep,
    providers: ProvidersDep,
) -> Response:
    await WatchlistService(session, providers.market).remove(user.id, instrument_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
