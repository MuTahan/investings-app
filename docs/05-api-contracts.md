# 05 — API Contracts

REST API exposed by the FastAPI backend. All routes are under `/api/v1`. JSON only.
Authenticated routes require `Authorization: Bearer <access_jwt>`.

Conventions:
- Timestamps are ISO-8601 UTC.
- Money/scores are JSON numbers; scores are `0..100` unless noted.
- Errors use a uniform envelope (see §Errors).
- Pagination: `?limit=` (default 20, max 100) + `?cursor=` where listed.

---

## Auth

### `POST /auth/register`
Request:
```json
{ "email": "a@b.com", "password": "string(min 8)", "display_name": "Ada" }
```
Response `201`:
```json
{ "access_token": "jwt", "refresh_token": "jwt", "token_type": "bearer",
  "expires_in": 3600, "user": { "id": "uuid", "email": "a@b.com", "display_name": "Ada" } }
```

### `POST /auth/login`
Request: `{ "email": "a@b.com", "password": "string" }` → same shape as register.

### `POST /auth/apple`
Request:
```json
{ "identity_token": "apple_jwt", "nonce": "string", "full_name": "Ada Lovelace" }
```
Response `200`: same auth payload (user upserted by `apple_sub`).

### `POST /auth/refresh`
Request: `{ "refresh_token": "jwt" }` → `{ "access_token": "...", "expires_in": 3600 }`.

---

## User

### `GET /me`
Response `200`:
```json
{ "id": "uuid", "email": "a@b.com", "display_name": "Ada",
  "risk_profile": { "risk_tolerance": "moderate", "time_horizon": "long",
                    "objectives": ["growth"], "max_position_pct": 20.0 } }
```

### `PUT /me/risk-profile`
Request:
```json
{ "risk_tolerance": "aggressive", "time_horizon": "medium",
  "objectives": ["growth","income"], "max_position_pct": 15.0 }
```
Response `200`: updated risk profile.

---

## Market

### `GET /market/search?q=appl`
Response `200`:
```json
{ "results": [ { "id":"uuid","symbol":"AAPL","name":"Apple Inc.","type":"stock","exchange":"NASDAQ" } ] }
```

### `GET /market/instruments/{symbol}`
Response `200`:
```json
{ "id":"uuid","symbol":"AAPL","name":"Apple Inc.","type":"stock",
  "exchange":"NASDAQ","sector":"Technology","currency":"USD" }
```

### `GET /market/quote/{symbol}`
Response `200` (live, cached):
```json
{ "symbol":"AAPL","price":201.34,"change":1.22,"change_pct":0.61,
  "open":200.10,"high":202.40,"low":199.80,"prev_close":200.12,
  "volume":54213000,"as_of":"2026-06-01T15:30:00Z" }
```

### `GET /market/candles/{symbol}?resolution=D&days=180`
`resolution` ∈ `1|5|15|60|D|W` (free tier serves daily). `days` 1–4000. Response `200`:
```json
{ "symbol":"AAPL","resolution":"D",
  "candles":[ { "t":"2026-05-30T00:00:00Z","o":199,"h":203,"l":198,"c":201,"v":51000000 } ] }
```

### `GET /market/trending?category=trending&limit=12`  ⭐ (Phase 8)
`category` ∈ `trending | most_bought | most_sold | high_momentum | high_opportunity`.
Computed from quote momentum over a curated universe, cached ~5 min. Response `200`:
```json
{ "category":"most_bought",
  "items":[ { "id":"uuid","symbol":"NVDA","name":"NVIDIA Corporation","type":"stock",
              "price":131.2,"change_pct":3.4,"sentiment":"bullish",
              "trend_score":67.0,"summary":"Up sharply 3.4% today" } ] }
```

---

## Watchlist

### `GET /watchlist`
```json
{ "id":"uuid","name":"My Watchlist",
  "items":[ { "instrument": { "symbol":"AAPL","name":"Apple Inc.","type":"stock" },
              "quote": { "price":201.34,"change_pct":0.61 }, "added_at":"..." } ] }
```

### `POST /watchlist/items`  → `{ "symbol":"AAPL" }` → `201` item.
### `DELETE /watchlist/items/{instrument_id}` → `204`.

---

## Portfolio

### `GET /portfolio`
```json
{ "id":"uuid","name":"My Portfolio",
  "summary": { "market_value": 25310.50, "cost_basis": 22000.00,
               "unrealized_pl": 3310.50, "unrealized_pl_pct": 15.05,
               "diversification_score": 68.0,
               "sector_exposure": { "Technology": 0.52, "Healthcare": 0.18 } },
  "holdings": [ { "instrument": { "symbol":"AAPL","type":"stock" },
                  "quantity": 50, "avg_cost": 180.0,
                  "market_value": 10067.0, "unrealized_pl_pct": 11.8,
                  "weight": 0.40 } ] }
```

### `POST /portfolio/holdings`
`{ "symbol":"AAPL", "quantity": 50, "avg_cost": 180.0 }` → `201` holding.

### `PUT /portfolio/holdings/{id}` → update quantity/avg_cost → `200`.
### `DELETE /portfolio/holdings/{id}` → `204`.

---

## Recommendations  ⭐ (core product)

### `GET /recommendations/{symbol}?refresh=false`
Returns the latest committee recommendation for the authenticated user (personalized).
If none `<1h` old exists, computes one (unless served from freshness gate).

Response `200`:
```json
{
  "symbol": "AAPL",
  "rating": "BUY",
  "anchor_rating": "BUY",
  "confidence": 72.5,
  "composite_score": 68.4,
  "decision_mode": "empowered",
  "time_horizon": "long",
  "suggested_action": "Consider initiating or adding a moderate position on pullbacks.",
  "chair_rationale": "Agreed with the anchor BUY; strong technical + fundamental alignment outweighs a neutral macro and a mild concentration concern.",
  "reasons": [
    { "label": "Strong technical momentum", "detail": "RSI 58, price above 50/200-day MAs, MACD positive crossover." },
    { "label": "Healthy fundamentals", "detail": "Revenue +8% YoY, operating margin 30%, reasonable forward P/E." }
  ],
  "risks": [
    { "label": "Concentration", "detail": "Would push Technology exposure above 55%.", "severity": "medium" },
    { "label": "Valuation", "detail": "Trading above 5-year average P/E.", "severity": "low" }
  ],
  "personalization": {
    "fit_score": 64.0,
    "fit_reason": "Aligns with your aggressive, long-horizon growth objective, but adds to an already tech-heavy book."
  },
  "agent_breakdown": [
    { "agent": "news",         "base_score": 68.0, "score": 70.0, "adjustment_delta": 2.0,
      "confidence": 65.0, "signal": "bullish",
      "explanation": "Net-positive coverage; recent analyst upgrade.",
      "adjustment_justification": "Upgrade is recent and from a top-tier analyst; nudged up." },
    { "agent": "technical",    "base_score": 74.0, "score": 76.0, "adjustment_delta": 2.0,
      "confidence": 80.0, "signal": "bullish",
      "explanation": "Uptrend intact, momentum positive.", "adjustment_justification": "MACD crossover confirms trend." },
    { "agent": "fundamental",  "base_score": 73.0, "score": 71.0, "adjustment_delta": -2.0,
      "confidence": 75.0, "signal": "bullish",
      "explanation": "Quality balance sheet, steady growth.", "adjustment_justification": "Valuation premium trims the score slightly." },
    { "agent": "macro",        "base_score": 55.0, "score": 55.0, "adjustment_delta": 0.0,
      "confidence": 60.0, "signal": "neutral",
      "explanation": "Rate environment mixed; risk-on regime.", "adjustment_justification": null },
    { "agent": "risk",         "base_score": null, "score": null, "adjustment_delta": 0.0,
      "confidence": 70.0, "signal": "neutral",
      "explanation": "Moderate volatility; earnings in 3 weeks.",
      "risk_level": "medium", "warnings": ["Earnings event risk"], "adjustment_justification": null },
    { "agent": "portfolio_fit","base_score": 64.0, "score": 64.0, "adjustment_delta": 0.0,
      "confidence": 68.0, "signal": "neutral",
      "explanation": "Good objective fit, weak diversification benefit.", "adjustment_justification": null }
  ],
  "decision_mode": "empowered",
  "weights_version": "v1",
  "model_versions": { "agents": "claude-haiku-4-5", "chair": "claude-sonnet-4-6" },
  "generated_at": "2026-06-01T15:32:00Z"
}
```

### `GET /recommendations?scope=watchlist|portfolio`
Batch latest recommendations across the user's watchlist or holdings.
```json
{ "items": [ { "symbol":"AAPL","rating":"BUY","confidence":72.5,"composite_score":68.4,
               "notif_priority":"normal","generated_at":"..." } ] }
```

### `GET /recommendations/{symbol}/history?limit=20`
Time series of past recommendations for trend display.

### `GET /recommendations/center`  ⭐ (Phase 8)
Bucketed recommendation cards across the user's watchlist + holdings. Optional filters:
`horizon` (short|medium|long), `risk` (low|medium|high), `sector`, `type` (a rating),
`min_confidence` (0–100). Each card carries the `valuation` block. Response `200`:
```json
{ "top_picks": [ { "symbol":"AAPL","name":"Apple Inc.","sector":"Technology",
                   "rating":"BUY","confidence":72.5,"composite_score":68.4,
                   "time_horizon":"long","risk_level":"medium","reason":"Strong momentum",
                   "fit_score":64.0,"notif_priority":"normal",
                   "valuation": { "fair_value":224.4,"target_price":236.9,"stop_loss":214.2 } } ],
  "short_term": [], "long_term": [], "trending": [], "personalized": [] }
```

---

## News

### `GET /news?symbol=AAPL&category=company&limit=20`
```json
{ "items": [ { "headline":"...","summary":"...","url":"https://...","source":"Reuters",
               "published_at":"...","sentiment": 42.0, "category":"company" } ] }
```
Omit `symbol` for macro/market news.

---

## Notifications / Devices

### `POST /notifications/devices`
`{ "device_token":"apns_token", "platform":"ios" }` → `201`.

### `DELETE /notifications/devices/{device_token}` → `204`.

### `GET /notifications` (history)
```json
{ "items": [ { "symbol":"AAPL","rating":"BUY","sent_at":"...","status":"sent" } ] }
```

---

## System

### `GET /health`
```json
{ "status":"ok", "db":"ok", "providers": { "finnhub":"ok","openai":"ok" } }
```

---

## Errors

Uniform envelope, correct HTTP status:
```json
{ "error": { "code": "validation_error", "message": "Human readable",
             "details": { "field": "password", "reason": "too short" } } }
```

| HTTP | code                | When                                  |
|------|---------------------|---------------------------------------|
| 400  | `validation_error`  | bad input                             |
| 401  | `unauthorized`      | missing/expired token                 |
| 403  | `forbidden`         | not allowed                           |
| 404  | `not_found`         | unknown resource/symbol               |
| 409  | `conflict`          | duplicate (e.g. watchlist item)       |
| 429  | `rate_limited`      | client throttled                      |
| 502  | `provider_error`    | upstream data/LLM failure (post-fallback) |
| 503  | `unavailable`       | DB/dependency down                    |

---

## Versioning & contract stability
- Path-versioned (`/api/v1`). Breaking changes → `/api/v2`.
- Response models are Pydantic schemas in `app/schemas/`; these ARE the contract and
  are covered by integration tests so the iOS `Models/` stay in sync.
