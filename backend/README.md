# Investing AI — Backend (FastAPI)

Phase 2 foundation: auth, market data, watchlist, portfolio, news, and the provider /
DB / scheduler scaffolding the AI committee (Phase 4) plugs into.

- **Stack:** Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), Alembic,
  PostgreSQL, Redis (optional), Docker.
- **Auth:** email/password (Argon2) + Apple Sign-In, JWT access/refresh.
- **Market data:** Finnhub, Financial Modeling Prep, AlphaVantage, NewsAPI behind a
  unified router with fallback + caching + rate limiting.
- **AI:** Anthropic / OpenAI behind one `LLMProvider` (used in Phase 4; a deterministic
  stub runs when no key is set).

> The `/recommendations` endpoints return `501 not_implemented` until Phase 4 — the
> committee engine is built then. Everything else is live.

---

## Quick start (Docker Compose — recommended)

```bash
cd backend
cp .env.example .env          # fill in API keys (optional for first boot)
docker compose up --build
```

This starts **Postgres + Redis + the API**, runs migrations, seeds instruments, and
serves with autoreload at:

- API base: `http://localhost:8000/api/v1`
- Swagger docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`

The API works with **no API keys** (auth, watchlist, portfolio, search all function);
live quotes/candles/news require at least one market-data key in `.env`.

## Run locally without Docker

Requires Python 3.11+ and a reachable PostgreSQL (or point `DATABASE_URL` at SQLite).

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
export DATABASE_URL="postgresql+asyncpg://investing:investing@localhost:5432/investing"
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

## Configuration

All config is environment-driven (`app/config.py`). See `.env.example` for the full
list. Key variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | async SQLAlchemy URL (postgres in prod, sqlite for tests) |
| `REDIS_URL` | optional; blank → in-memory cache |
| `JWT_SECRET` | sign JWTs (`openssl rand -hex 32` in prod) |
| `APPLE_CLIENT_ID` | bundle/service id used as the Apple token audience |
| `FINNHUB_API_KEY` / `FMP_API_KEY` / `ALPHAVANTAGE_API_KEY` / `NEWSAPI_API_KEY` | market data (free tiers) |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | AI providers (Phase 4) |
| `AI_DECISION_MODE` | `deterministic` \| `chair_assisted` \| `empowered` |

## Tests

Tests run on an isolated SQLite DB with fake providers — **no network, no Postgres
needed**.

```bash
# locally
pytest -q

# in Docker (matches CI)
docker build -t investing-backend:test .
docker run --rm investing-backend:test pytest -q
```

Lint / format / type-check:

```bash
ruff check app tests
black app tests
mypy app
```

## Database & migrations

```bash
alembic upgrade head                      # apply migrations
alembic revision --autogenerate -m "..."  # create a new migration
python -m app.db.seed                      # idempotent instrument seed (S&P sample + ETFs)
```

Models use cross-DB-portable types (`Uuid`, `JSON`, `Numeric`, timezone-aware
`DateTime`) so the same schema runs on Postgres and SQLite.

## Project layout

```
app/
├── main.py            # app factory + lifespan (builds the provider container)
├── config.py          # env-driven settings
├── deps.py            # FastAPI dependencies (db, settings, providers, current user)
├── api/               # routers (api/v1/*) + error envelope
├── schemas/           # Pydantic request/response DTOs (the API contract)
├── services/          # use-cases (auth, market, portfolio, watchlist, news, user)
├── ai/                # agents + committee (Phase 4)
├── providers/         # market + LLM adapters, router (fallback/cache/rate-limit)
├── repositories/      # persistence per aggregate
├── db/                # SQLAlchemy models, session, seed
├── scheduler/         # hourly jobs (Phase 5)
├── notifications/     # APNS (Phase 5)
├── core/              # security (JWT/Argon2/Apple), logging, exceptions
└── domain/            # enums + pure types
alembic/               # migrations
tests/                 # unit + integration (SQLite + fakes)
```

## Notifications & scheduler (Phase 5)

An in-process **APScheduler** job recomputes recommendations for each active user's
watchlist + holdings every `SCHEDULER_INTERVAL_MINUTES` (default 60) and pushes
**high-priority rating changes** to every configured channel. Channels fan out:

- **ntfy** — set `NTFY_TOPIC` (any hard-to-guess string), subscribe to it in the
  [ntfy](https://ntfy.sh) app/browser. No account/token.
- **Telegram** — set `TELEGRAM_BOT_TOKEN` (via @BotFather) + `TELEGRAM_CHAT_ID`.

Every send is also recorded to the in-app feed (`GET /notifications`). Trigger a run
immediately with `POST /notifications/run` (handy for testing without waiting an hour).
`NOTIFY_MIN_PRIORITY`, `NOTIFY_MAX_PER_RUN`, and `QUIET_HOURS_*` tune delivery. The
scheduler is behind a `JobScheduler` interface for a future Celery/Redis swap.

> With `uvicorn --reload` (dev), two processes may each start a scheduler. Set
> `SCHEDULER_ENABLED=false` if you only want the API, or run without `--reload`.

## API surface

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST | `/auth/register` `/auth/login` `/auth/apple` `/auth/refresh` | – | JWT issue/refresh |
| GET/PUT | `/me`, `/me/risk-profile` | ✅ | profile + risk profile |
| GET | `/market/search` `/market/instruments/{symbol}` `/market/quote/{symbol}` `/market/candles/{symbol}` | ✅ | live data via router |
| GET/POST/DELETE | `/watchlist`, `/watchlist/items` | ✅ | watchlist + quotes |
| GET/POST/PUT/DELETE | `/portfolio`, `/portfolio/holdings` | ✅ | holdings + computed summary |
| GET | `/news` | ✅ | company/macro news |
| GET | `/recommendations/{symbol}` (+`?refresh`), `?scope=`, `/{symbol}/history` | ✅ | AI committee (Phase 4) |
| GET/POST | `/notifications`, `/notifications/run` | ✅ | in-app feed + manual run (Phase 5) |
| POST/DELETE | `/notifications/devices` | ✅ | device registration (legacy/optional) |
| GET | `/health`, `/api/v1/health` | – | liveness + DB/LLM status |

Full request/response contracts: [`../docs/05-api-contracts.md`](../docs/05-api-contracts.md).

## Design references

- Architecture & decisions: [`../docs/01-architecture.md`](../docs/01-architecture.md)
- AI agents & committee: [`../docs/06-ai-agents.md`](../docs/06-ai-agents.md)
- Roadmap: [`../docs/07-roadmap.md`](../docs/07-roadmap.md)
