from __future__ import annotations

import httpx
import pytest

from app.core.exceptions import ProviderError
from app.providers.market.twelvedata import TwelveDataProvider


class FakeClient:
    def __init__(self, payload) -> None:
        self.payload = payload
        self.calls: list[dict] = []

    async def get(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return httpx.Response(200, json=self.payload, request=httpx.Request("GET", url))


def _bar(dt: str, close: str) -> dict:
    return {"datetime": dt, "open": "1", "high": "2", "low": "0.5", "close": close, "volume": "10"}


async def test_intraday_candles_parsed_and_sorted():
    payload = {
        "status": "ok",
        "values": [
            _bar("2024-06-03 15:55:00", "1.5"),
            _bar("2024-06-03 15:50:00", "1.4"),
        ],
    }
    client = FakeClient(payload)
    provider = TwelveDataProvider(client, "KEY")  # type: ignore[arg-type]

    series = await provider.get_candles("AAPL", "5", _dt(), _dt())

    assert series.resolution == "5"
    assert [c.c for c in series.candles] == [1.4, 1.5]  # sorted ascending by time
    assert client.calls[0]["params"]["interval"] == "5min"


async def test_status_error_raises():
    client = FakeClient({"status": "error", "message": "bad symbol", "code": 400})
    provider = TwelveDataProvider(client, "KEY")  # type: ignore[arg-type]

    with pytest.raises(ProviderError):
        await provider.get_quote("NOPE")


def _dt():
    from datetime import UTC, datetime

    return datetime(2024, 6, 3, tzinfo=UTC)
