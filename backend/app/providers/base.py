"""Provider-layer DTOs and interfaces.

Market-data and LLM vendors implement these so the rest of the app never depends on a
specific vendor. DTOs are Pydantic models for easy validation + serialization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from app.core.exceptions import ProviderError


class ProviderNotSupported(ProviderError):
    """Raised when a vendor adapter does not implement a capability."""

    code = "provider_unsupported"


# ---------------- market-data DTOs ----------------
class QuoteData(BaseModel):
    symbol: str
    price: float
    change: float | None = None
    change_pct: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    prev_close: float | None = None
    volume: float | None = None
    as_of: datetime | None = None


class Candle(BaseModel):
    t: datetime
    o: float
    h: float
    l: float  # noqa: E741 - OHLC convention
    c: float
    v: float | None = None


class CandleSeries(BaseModel):
    symbol: str
    resolution: str
    candles: list[Candle]


class Fundamentals(BaseModel):
    symbol: str
    pe: float | None = None
    forward_pe: float | None = None
    eps_growth: float | None = None
    revenue_growth: float | None = None
    gross_margin: float | None = None
    op_margin: float | None = None
    market_cap: float | None = None
    dividend_yield: float | None = None
    beta: float | None = None
    expense_ratio: float | None = None  # ETFs
    raw: dict[str, Any] = {}


class NewsArticle(BaseModel):
    headline: str
    url: str
    summary: str | None = None
    source: str | None = None
    published_at: datetime | None = None
    category: str = "company"


class SymbolHit(BaseModel):
    symbol: str
    name: str
    type: str = "stock"  # "stock" | "etf"
    exchange: str | None = None


class MacroSnapshot(BaseModel):
    vix: float | None = None
    rate_trend: str | None = None
    inflation_trend: str | None = None
    sector_rotation: dict[str, float] = {}
    raw: dict[str, Any] = {}


# ---------------- interfaces ----------------
@runtime_checkable
class MarketDataProvider(Protocol):
    """A market-data vendor. Adapters raise ProviderNotSupported for capabilities
    they don't implement; the router handles fallback."""

    name: str

    async def get_quote(self, symbol: str) -> QuoteData: ...
    async def get_candles(
        self, symbol: str, resolution: str, frm: datetime, to: datetime
    ) -> CandleSeries: ...
    async def get_fundamentals(self, symbol: str) -> Fundamentals: ...
    async def get_news(
        self, symbol: str | None, category: str, limit: int
    ) -> list[NewsArticle]: ...
    async def search_symbols(self, query: str, limit: int) -> list[SymbolHit]: ...


class BaseMarketProvider:
    """Default impl raising ProviderNotSupported so adapters override only what they support."""

    name: str = "base"

    async def get_quote(self, symbol: str) -> QuoteData:
        raise ProviderNotSupported(f"{self.name} does not support quotes")

    async def get_candles(
        self, symbol: str, resolution: str, frm: datetime, to: datetime
    ) -> CandleSeries:
        raise ProviderNotSupported(f"{self.name} does not support candles")

    async def get_fundamentals(self, symbol: str) -> Fundamentals:
        raise ProviderNotSupported(f"{self.name} does not support fundamentals")

    async def get_news(self, symbol: str | None, category: str, limit: int) -> list[NewsArticle]:
        raise ProviderNotSupported(f"{self.name} does not support news")

    async def search_symbols(self, query: str, limit: int) -> list[SymbolHit]:
        raise ProviderNotSupported(f"{self.name} does not support symbol search")


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    async def complete_text(self, prompt: str, *, model: str, max_tokens: int = 600) -> str: ...
    async def complete_json(
        self, prompt: str, *, model: str, max_tokens: int = 800
    ) -> dict[str, Any]: ...
