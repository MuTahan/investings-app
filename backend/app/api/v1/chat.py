from __future__ import annotations

from fastapi import APIRouter

from app.deps import CurrentUserDep, ProvidersDep, SessionDep, SettingsDep
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    user: CurrentUserDep,
    session: SessionDep,
    providers: ProvidersDep,
    settings: SettingsDep,
) -> ChatResponse:
    reply = await ChatService(session, providers, settings).reply(user, req.symbol, req.messages)
    return ChatResponse(reply=reply)
