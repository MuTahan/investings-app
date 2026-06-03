"""Conversational stock-chat service backed by Grok (xAI).

Builds a grounded system prompt from live app data (quote, the app's own AI rating,
recent headlines) and forwards the conversation to the chat model.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.providers.container import ProviderContainer
from app.repositories.instrument_repo import InstrumentRepository
from app.repositories.recommendation_repo import RecommendationRepository
from app.schemas.chat import ChatMessage
from app.services.news_service import NewsService

_SYSTEM = (
    "You are the in-app assistant for Investing AI, a personal research tool for US "
    "stocks and ETFs. Be concise, factual, and conversational. Ground answers in the "
    "context provided. You are informational only: never give personalized financial "
    "advice or tell the user to buy or sell — encourage them to do their own research. "
    "Context: "
)


class ChatService:
    def __init__(
        self, session: AsyncSession, providers: ProviderContainer, settings: Settings
    ) -> None:
        self._providers = providers
        self._settings = settings
        self._market = providers.market
        self._instruments = InstrumentRepository(session)
        self._reco_repo = RecommendationRepository(session)
        self._news = NewsService(session, providers.market)

    async def reply(self, user, symbol: str | None, messages: list[ChatMessage]) -> str:
        if self._providers.chat is None:
            return (
                "The chat assistant isn't configured yet — add an xAI (Grok) API key "
                "(XAI_API_KEY) to enable it."
            )
        context = await self._context(user, symbol)
        convo = [{"role": "system", "content": _SYSTEM + context}]
        convo += [{"role": m.role, "content": m.content} for m in messages]
        return await self._providers.chat.chat(convo)

    async def _context(self, user, symbol: str | None) -> str:
        if not symbol:
            return "No specific ticker selected; answer general US stock/ETF questions."
        symbol = symbol.upper()
        instrument = await self._instruments.get_by_symbol(symbol)
        parts = [f"Discussing {symbol}" + (f" ({instrument.name})." if instrument else ".")]
        try:
            q = await self._market.get_quote(symbol)
            pct = f"{q.change_pct:+.2f}%" if q.change_pct is not None else "n/a"
            parts.append(f"Latest price ${q.price} ({pct}).")
        except Exception:  # noqa: BLE001 - context is best-effort
            pass
        if instrument is not None:
            rec = await self._reco_repo.latest(user.id, instrument.id)
            if rec is not None:
                parts.append(
                    f"This app's AI committee rates it {rec.rating} "
                    f"(confidence {float(rec.confidence):.0f}%)."
                )
        try:
            news = await self._news.list(symbol, "company", 4)
            if news:
                parts.append("Recent headlines: " + " | ".join(a.headline for a in news[:4]))
        except Exception:  # noqa: BLE001
            pass
        return " ".join(parts)
