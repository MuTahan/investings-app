"""Test fixtures: isolated SQLite DB per test, fake providers, authed client.

Tests never touch the network: a FakeProviderContainer supplies canned market data,
a stub LLM, and a fake Apple verifier.
"""

from __future__ import annotations

import os
import tempfile
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.providers.base import (
    Candle,
    CandleSeries,
    Fundamentals,
    NewsArticle,
    QuoteData,
)


# ---------------- fakes ----------------
class FakeMarketRouter:
    """Deterministic market data for tests (no network)."""

    async def get_quote(self, symbol: str) -> QuoteData:
        return QuoteData(
            symbol=symbol.upper(),
            price=100.0,
            change=1.5,
            change_pct=1.5,
            open=99.0,
            high=101.0,
            low=98.5,
            prev_close=98.5,
            volume=1_000_000,
            as_of=datetime.now(UTC),
        )

    async def get_candles(self, symbol, resolution, frm, to) -> CandleSeries:
        candles = [
            Candle(t=datetime(2026, 5, d, tzinfo=UTC), o=99, h=101, l=98, c=100, v=1000)
            for d in range(1, 6)
        ]
        return CandleSeries(symbol=symbol.upper(), resolution=resolution, candles=candles)

    async def get_fundamentals(self, symbol: str) -> Fundamentals:
        return Fundamentals(symbol=symbol.upper(), pe=20.0, op_margin=0.25)

    async def get_news(self, symbol, category="company", limit=20) -> list[NewsArticle]:
        return [
            NewsArticle(
                headline=f"{symbol or 'Market'} update",
                url=f"https://news.example/{symbol or 'macro'}/1",
                source="Test Wire",
                published_at=datetime.now(UTC),
                category="macro" if symbol is None else category,
            )
        ]


class FakeAppleVerifier:
    async def verify(self, identity_token: str, nonce: str | None = None) -> dict:
        return {"sub": "apple-sub-123", "email": "apple.user@example.com"}


class FakeLLM:
    name = "stub"

    async def complete_text(self, prompt, *, model, max_tokens=600) -> str:
        return "test explanation"

    async def complete_json(self, prompt, *, model, max_tokens=800) -> dict:
        return {}


class FakeNotifier:
    name = "composite"

    def __init__(self) -> None:
        self.sent: list = []

    @property
    def channels(self) -> list[str]:
        return ["fake"]

    async def send(self, notification) -> bool:
        self.sent.append(notification)
        return True


class FakeProviderContainer:
    def __init__(self) -> None:
        from app.providers.cache import InMemoryCache

        self.market = FakeMarketRouter()
        self.market_vendors = ["fake"]
        self.llm = FakeLLM()
        self.apple_verifier = FakeAppleVerifier()
        self.notifier = FakeNotifier()
        self.cache = InMemoryCache()

    async def aclose(self) -> None:
        return None


# ---------------- db + app fixtures ----------------
@pytest.fixture(autouse=True)
async def _setup_db():
    from app.config import get_settings
    from app.db.base import Base
    from app.db.seed import seed
    from app.db.session import get_engine, reset_engine_state

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{path}"
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["APPLE_CLIENT_ID"] = "com.test.app"
    os.environ["ENVIRONMENT"] = "test"
    get_settings.cache_clear()
    reset_engine_state()

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed()

    yield

    await engine.dispose()
    reset_engine_state()
    get_settings.cache_clear()
    os.unlink(path)


@pytest.fixture
async def client():
    from app.config import get_settings
    from app.main import create_app

    app = create_app(get_settings())
    app.state.providers = FakeProviderContainer()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "password123", "display_name": "Tester"},
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
