from __future__ import annotations

from datetime import UTC, datetime

import httpx

from app.core.exceptions import ProviderError
from app.providers.base import (
    BaseMarketProvider,
    Candle,
    CandleSeries,
    Fundamentals,
    QuoteData,
)

_BASE = "https://financialmodelingprep.com/api/v3"


class FMPProvider(BaseMarketProvider):
    name = "fmp"

    def __init__(self, client: httpx.AsyncClient, api_key: str) -> None:
        self._client = client
        self._key = api_key

    async def _get(self, path: str, params: dict | None = None) -> list | dict:
        params = {**(params or {}), "apikey": self._key}
        try:
            resp = await self._client.get(f"{_BASE}{path}", params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"fmp {path} error: {exc}") from exc

    async def get_quote(self, symbol: str) -> QuoteData:
        data = await self._get(f"/quote/{symbol.upper()}")
        if not isinstance(data, list) or not data:
            raise ProviderError(f"fmp: no quote for {symbol}")
        q = data[0]
        return QuoteData(
            symbol=symbol.upper(),
            price=float(q["price"]),
            change=_f(q.get("change")),
            change_pct=_f(q.get("changesPercentage")),
            open=_f(q.get("open")),
            high=_f(q.get("dayHigh")),
            low=_f(q.get("dayLow")),
            prev_close=_f(q.get("previousClose")),
            volume=_f(q.get("volume")),
            as_of=datetime.now(UTC),
        )

    async def get_candles(
        self, symbol: str, resolution: str, frm: datetime, to: datetime
    ) -> CandleSeries:
        data = await self._get(
            f"/historical-price-full/{symbol.upper()}",
            {"from": frm.date().isoformat(), "to": to.date().isoformat()},
        )
        rows = data.get("historical", []) if isinstance(data, dict) else []
        if not rows:
            raise ProviderError(f"fmp: no candles for {symbol}")
        candles = [
            Candle(
                t=datetime.fromisoformat(r["date"]).replace(tzinfo=UTC),
                o=float(r["open"]),
                h=float(r["high"]),
                l=float(r["low"]),
                c=float(r["close"]),
                v=_f(r.get("volume")),
            )
            for r in rows
        ]
        candles.sort(key=lambda c: c.t)
        return CandleSeries(symbol=symbol.upper(), resolution="D", candles=candles)

    async def get_fundamentals(self, symbol: str) -> Fundamentals:
        ratios = await self._get(f"/ratios-ttm/{symbol.upper()}")
        profile = await self._get(f"/profile/{symbol.upper()}")
        r = ratios[0] if isinstance(ratios, list) and ratios else {}
        p = profile[0] if isinstance(profile, list) and profile else {}
        return Fundamentals(
            symbol=symbol.upper(),
            pe=_f(r.get("peRatioTTM")),
            eps_growth=None,
            revenue_growth=None,
            gross_margin=_f(r.get("grossProfitMarginTTM")),
            op_margin=_f(r.get("operatingProfitMarginTTM")),
            market_cap=_f(p.get("mktCap")),
            dividend_yield=_f(r.get("dividendYielTTM") or r.get("dividendYieldTTM")),
            beta=_f(p.get("beta")),
            raw={"ratios": r, "profile": {k: p.get(k) for k in ("sector", "industry", "isEtf")}},
        )


def _f(value: object) -> float | None:
    try:
        return float(value) if value not in (None, "") else None  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
