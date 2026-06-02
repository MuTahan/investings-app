from __future__ import annotations

from datetime import UTC, datetime

import httpx

from app.core.exceptions import ProviderError
from app.providers.base import (
    BaseMarketProvider,
    Candle,
    CandleSeries,
    Fundamentals,
    NewsArticle,
    QuoteData,
    SymbolHit,
)

_BASE = "https://finnhub.io/api/v1"
_RES_MAP = {"1": "1", "5": "5", "15": "15", "60": "60", "D": "D", "W": "W"}


class FinnhubProvider(BaseMarketProvider):
    name = "finnhub"

    def __init__(self, client: httpx.AsyncClient, api_key: str) -> None:
        self._client = client
        self._key = api_key

    async def _get(self, path: str, params: dict) -> dict | list:
        params = {**params, "token": self._key}
        try:
            resp = await self._client.get(f"{_BASE}{path}", params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"finnhub {path} failed: {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"finnhub {path} error: {exc}") from exc

    async def search_symbols(self, query: str, limit: int) -> list[SymbolHit]:
        data = await self._get("/search", {"q": query})
        results = data.get("result", []) if isinstance(data, dict) else []
        hits: list[SymbolHit] = []
        for r in results:
            symbol = (r.get("symbol") or "").upper()
            raw_type = (r.get("type") or "").lower()
            # US listings only: skip dotted foreign tickers (e.g. "AAPL.MX").
            if not symbol or "." in symbol:
                continue
            if raw_type and raw_type not in ("common stock", "etp", "etf", "adr", ""):
                continue
            hits.append(
                SymbolHit(
                    symbol=symbol,
                    name=r.get("description") or symbol,
                    type="etf" if raw_type in ("etp", "etf") else "stock",
                )
            )
            if len(hits) >= limit:
                break
        return hits

    async def get_quote(self, symbol: str) -> QuoteData:
        data = await self._get("/quote", {"symbol": symbol.upper()})
        if not isinstance(data, dict) or data.get("c") in (None, 0):
            raise ProviderError(f"finnhub: no quote for {symbol}")
        ts = data.get("t")
        return QuoteData(
            symbol=symbol.upper(),
            price=float(data["c"]),
            change=_f(data.get("d")),
            change_pct=_f(data.get("dp")),
            open=_f(data.get("o")),
            high=_f(data.get("h")),
            low=_f(data.get("l")),
            prev_close=_f(data.get("pc")),
            as_of=datetime.fromtimestamp(ts, tz=UTC) if ts else None,
        )

    async def get_candles(
        self, symbol: str, resolution: str, frm: datetime, to: datetime
    ) -> CandleSeries:
        res = _RES_MAP.get(resolution, "D")
        data = await self._get(
            "/stock/candle",
            {
                "symbol": symbol.upper(),
                "resolution": res,
                "from": int(frm.timestamp()),
                "to": int(to.timestamp()),
            },
        )
        if not isinstance(data, dict) or data.get("s") != "ok":
            raise ProviderError(f"finnhub: no candles for {symbol}")
        candles = [
            Candle(
                t=datetime.fromtimestamp(t, tz=UTC),
                o=o,
                h=h,
                l=low,
                c=c,
                v=v,
            )
            for t, o, h, low, c, v in zip(
                data["t"], data["o"], data["h"], data["l"], data["c"], data["v"], strict=False
            )
        ]
        return CandleSeries(symbol=symbol.upper(), resolution=resolution, candles=candles)

    async def get_fundamentals(self, symbol: str) -> Fundamentals:
        data = await self._get("/stock/metric", {"symbol": symbol.upper(), "metric": "all"})
        metric = data.get("metric", {}) if isinstance(data, dict) else {}
        return Fundamentals(
            symbol=symbol.upper(),
            pe=_f(metric.get("peTTM")),
            eps_growth=_f(metric.get("epsGrowthTTMYoy")),
            revenue_growth=_f(metric.get("revenueGrowthTTMYoy")),
            gross_margin=_f(metric.get("grossMarginTTM")),
            op_margin=_f(metric.get("operatingMarginTTM")),
            market_cap=_f(metric.get("marketCapitalization")),
            dividend_yield=_f(metric.get("dividendYieldIndicatedAnnual")),
            beta=_f(metric.get("beta")),
            raw=metric,
        )

    async def get_news(self, symbol: str | None, category: str, limit: int) -> list[NewsArticle]:
        if symbol is None:
            data = await self._get("/news", {"category": "general"})
        else:
            today = datetime.now(UTC).date()
            frm = today.replace(day=1)
            data = await self._get(
                "/company-news",
                {"symbol": symbol.upper(), "from": frm.isoformat(), "to": today.isoformat()},
            )
        if not isinstance(data, list):
            return []
        articles: list[NewsArticle] = []
        for item in data[:limit]:
            dt = item.get("datetime")
            articles.append(
                NewsArticle(
                    headline=item.get("headline", ""),
                    summary=item.get("summary"),
                    url=item.get("url", ""),
                    source=item.get("source"),
                    published_at=datetime.fromtimestamp(dt, tz=UTC) if dt else None,
                    category="macro" if symbol is None else category,
                )
            )
        return [a for a in articles if a.headline and a.url]


def _f(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
