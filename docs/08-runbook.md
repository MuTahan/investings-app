# 08 — Runbook & Operations

Practical guide to running, configuring, operating, and understanding the limits of
the Investing AI MVP.

---

## 1. Run the whole stack (one command)

```bash
docker compose up --build
```

Brings up Postgres + Redis + the FastAPI backend (migrations + instrument seed run
automatically) + the React PWA behind nginx.

- **Web app:** http://localhost:8080  (nginx proxies `/api` → backend, so no CORS)
- **API + Swagger:** http://localhost:8000/docs
- **Health:** http://localhost:8000/api/v1/health

Runs out-of-the-box with **no API keys**: AI runs in `deterministic` mode and live
quotes are unavailable (auth, watchlist, portfolio, and deterministic recommendations
all work). Add keys to the `api` service `environment` in `docker-compose.yml` to go
live (see §3).

### Demo data (optional)
Populate a demo user with a watchlist + portfolio so screens aren't empty:

```bash
docker compose exec api python -m app.db.seed_demo
# then log in at http://localhost:8080 with:
#   email: demo@example.com   password: demodemo123
```

### Run stacks separately (development)
- Backend only: `cd backend && docker compose up` (see `backend/README.md`).
- Web dev server: `cd web && npm install && npm run dev` (see `web/README.md`).

---

## 2. Architecture at a glance

```
Browser/PWA ──HTTPS──> nginx (web) ──/api proxy──> FastAPI (api) ──> Postgres
                                                        │  ├─> Redis (cache, optional)
                                                        │  ├─> Market vendors (Finnhub/FMP/AV/NewsAPI)
                                                        │  ├─> LLM (Anthropic/OpenAI) — agents + Chair
                                                        │  └─> Notifier (ntfy / Telegram)
                                                        └─ APScheduler (hourly refresh + notify)
```

Full design: [01-architecture.md](01-architecture.md), [06-ai-agents.md](06-ai-agents.md).

---

## 3. Configuration (key env vars)

Set on the `api` service (compose) or `backend/.env`. Full list:
`backend/.env.example`.

| Area | Vars | Effect |
|------|------|--------|
| Database | `DATABASE_URL` | Postgres (prod) / SQLite (tests) |
| Cache | `REDIS_URL` | blank → in-memory cache |
| Auth | `JWT_SECRET` (set in prod!), `APPLE_CLIENT_ID` | sessions, Apple Sign-In |
| Market data | `FINNHUB_API_KEY`, `FMP_API_KEY`, `ALPHAVANTAGE_API_KEY`, `NEWSAPI_API_KEY` | live quotes/candles/fundamentals/news |
| AI | `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`, `AI_DECISION_MODE`, `AI_AGENT_MODEL`, `AI_CHAIR_MODEL` | empowered agents + Chair vs deterministic |
| Notifications | `NTFY_TOPIC`, `TELEGRAM_BOT_TOKEN`+`TELEGRAM_CHAT_ID`, `APP_BASE_URL` | push channels + deep links |
| Scheduler | `SCHEDULER_ENABLED`, `SCHEDULER_INTERVAL_MINUTES`, `NOTIFY_MIN_PRIORITY`, `NOTIFY_MAX_PER_RUN`, `QUIET_HOURS_START/END` | hourly job + delivery tuning |

**Decision modes:** `deterministic` (reproducible, no LLM — the default with no key),
`chair_assisted`, `empowered` (agents ±10 + Chair ±1 band). Set `ANTHROPIC_API_KEY`
+ `AI_DECISION_MODE=empowered` to activate Claude.

---

## 4. Common operations

```bash
# DB migrations
docker compose exec api alembic upgrade head
docker compose exec api alembic revision --autogenerate -m "msg"

# Reseed instruments / demo
docker compose exec api python -m app.db.seed
docker compose exec api python -m app.db.seed_demo

# Trigger a notification run immediately (per the calling user)
curl -X POST localhost:8000/api/v1/notifications/run -H "Authorization: Bearer <jwt>"

# Verify every configured provider works against its LIVE API (reads root .env)
cd backend && docker run --rm --env-file ../.env -e PYTHONPATH=/code \
  -v "$PWD":/code -w /code investing-backend:test python scripts/check_providers.py

# Tests
cd backend && docker run --rm -v "$PWD":/code -w /code <img> pytest -q
cd web && npm test
```

Logs are structured JSON (one object per line) including request id, method, path,
status, and `duration_ms`. Per-agent + provider fallbacks are logged by the AI layer.

---

## 5. Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `502 provider_error` on quotes | No market-data key set, or free-tier rate limit. Add a key; router falls back across vendors. |
| Recommendation `decision_mode: deterministic` despite a key | `AI_DECISION_MODE` not `empowered`, or the LLM provider errored (check logs; it falls back to the anchor). |
| No push notifications | `NTFY_TOPIC` / Telegram vars unset, priority below `NOTIFY_MIN_PRIORITY`, or quiet hours. Use `POST /notifications/run` + lower threshold to test. |
| Two scheduler runs in dev | `uvicorn --reload` spawns two processes. Use the root compose (no reload) or `SCHEDULER_ENABLED=false`. |
| 401 loops in the web app | Backend `JWT_SECRET` changed → old tokens invalid. Sign out / clear site data. |
| `/api` 404 from the web container | nginx proxy or `VITE_API_BASE_URL` misconfigured; the web image expects `/api/v1`. |

---

## 6. Known limitations (MVP)

- **Informational only** — no brokerage, no trade execution, no real-money actions. By design.
- **Free-tier data** — quotas constrain refresh frequency; cached aggressively. Index/macro
  (VIX/SPY) data is best-effort and degrades to a neutral regime.
- **Apple Sign-In** is backend-ready; the web UI ships email/password.
- **Auth tokens** are stored in `localStorage` (acceptable XSS tradeoff for personal use).
- **Single-node scheduler** (APScheduler in-process); not HA. Don't run multiple API
  replicas with the scheduler enabled (duplicate jobs).
- **No metrics/tracing stack** — structured logs only.

## 7. Cost notes (when AI is enabled)

- Per recommendation: ~6 agent calls (Haiku-tier) + 1 Chair call (Sonnet/Opus-tier).
- Controls already in place: model tiering, 1-hour freshness gate (repeat views = DB read,
  no LLM), per-symbol single data fetch shared across agents, deterministic fallback.
- To cut cost: raise the freshness window, set some/all agents to `deterministic`, lower
  `SCHEDULER_INTERVAL` frequency, or reduce watchlist/holdings size.

## 8. Scale-later path (interfaces already in place)

- **Redis** for cache (set `REDIS_URL`) — same interface as in-memory.
- **Celery + Redis** for the scheduler — swap behind the `JobScheduler` interface.
- **New data/LLM vendors** — add an adapter behind `MarketDataProvider` / `LLMProvider`.
- **Metrics/tracing** — logging hooks are in place to add Prometheus/OTel without churn.
