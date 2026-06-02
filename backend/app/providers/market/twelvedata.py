"""Twelve Data provider — the only one of our free tiers that serves intraday bars.

Used primarily for intraday candles (1min..1h) so the stock chart can show 1D/3D/1W
ranges; also works as a quote/daily-candle/symbol-search fallback. Free tier is
800 requests/day, so it sits *after* FMP for daily candles to conserve quota.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from app.core.exceptions import ProviderError
from app.providers.base import (
    BaseMarketProvider,
    Candle,
    CandleSeries,
    QuoteData,
    SymbolHit,
)

_BASE = "https://api.twelvedata.com"

# Our internal resolution codes -> Twelve Data interval strings.
_INTERVAL = {
    "1": "1min",
    "5": "5min",
    "15": "15min",
    "30": "30min",
    "60": "1h",
    "D": "1day",
    "W": "1week",
    "M": "1month",
}
_US_EXCHANGES = {"NASDAQ", "NYSE", "AMEX", "NYSE AMERICAN", "BATS", "OTC"}


class TwelveDataProvider(BaseMarketProvider):
    name = "twelvedata"

    def __init__(self, client: httpx.AsyncClient, api_key: str) -> None:
        self._client = client
        self._key = api_key

    async def _get(self, path: str, params: dict) -> dict | list:
        params = {**params, "apikey": self._key}
        try:
            resp = await self._client.get(f"{_BASE}{path}", params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"twelvedata {path} error: {exc}") from exc
        # Twelve Data signals errors in-body with status=error (HTTP is still 200).
        if isinstance(data, dict) and data.get("status") == "error":
            raise ProviderError(f"twelvedata {path}: {data.get('message')}")
        return data

    async def get_quote(self, symbol: str) -> QuoteData:
        data = await self._get("/quote", {"symbol": symbol.upper()})
        if not isinstance(data, dict) or "close" not in data:
            raise ProviderError(f"twelvedata: no quote for {symbol}")
        return QuoteData(
            symbol=symbol.upper(),
            price=float(data["close"]),
            change=_f(data.get("change")),
            change_pct=_f(data.get("percent_change")),
            open=_f(data.get("open")),
            high=_f(data.get("high")),
            low=_f(data.get("low")),
            prev_close=_f(data.get("previous_close")),
            volume=_f(data.get("volume")),
            as_of=datetime.now(UTC),
        )

    async def get_candles(
        self, symbol: str, resolution: str, frm: datetime, to: datetime
    ) -> CandleSeries:
        interval = _INTERVAL.get(resolution, "1day")
        data = await self._get(
            "/time_series",
            {
                "symbol": symbol.upper(),
                "interval": interval,
                "start_date": frm.strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": to.strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": "UTC",
                "outputsize": 5000,
                "order": "ASC",
            },
        )
        values = data.get("values", []) if isinstance(data, dict) else []
        if not values:
            raise ProviderError(f"twelvedata: no candles for {symbol}")
        candles = [
            Candle(
                t=_parse_dt(v["datetime"]),
                o=float(v["open"]),
                h=float(v["high"]),
                l=float(v["low"]),
                c=float(v["close"]),
                v=_f(v.get("volume")),
            )
            for v in values
            if v.get("open") is not None
        ]
        candles.sort(key=lambda c: c.t)
        return CandleSeries(symbol=symbol.upper(), resolution=resolution, candles=candles)

    async def search_symbols(self, query: str, limit: int) -> list[SymbolHit]:
        data = await self._get("/symbol_search", {"symbol": query, "outputsize": limit * 2})
        results = data.get("data", []) if isinstance(data, dict) else []
        hits: list[SymbolHit] = []
        for r in results:
            symbol = (r.get("symbol") or "").upper()
            exchange = (r.get("exchange") or "").upper()
            if not symbol or "." in symbol or (exchange and exchange not in _US_EXCHANGES):
                continue
            hits.append(
                SymbolHit(
                    symbol=symbol,
                    name=r.get("instrument_name") or symbol,
                    type="etf" if (r.get("instrument_type") or "").lower() == "etf" else "stock",
                    exchange=exchange or None,
                )
            )
            if len(hits) >= limit:
                break
        return hits


def _parse_dt(value: str) -> datetime:
    # Daily -> "2024-06-03"; intraday -> "2024-06-03 15:55:00" (UTC via timezone param).
    dt = datetime.fromisoformat(value)
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def _f(value: object) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None
