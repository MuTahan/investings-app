# 02 — Folder Structure

Production-grade, modular layouts for both stacks. These are the **target**
structures; phases fill them in incrementally (see [07-roadmap.md](07-roadmap.md)).

---

## Backend (`backend/`)

```
backend/
├── pyproject.toml                # deps, tooling (ruff, black, mypy, pytest)
├── alembic.ini
├── .env.example
├── Dockerfile
├── README.md                     # backend setup & run instructions
├── alembic/
│   ├── env.py
│   └── versions/                 # migration files
├── app/
│   ├── main.py                   # FastAPI app factory, router mounting, lifespan
│   ├── config.py                 # Pydantic Settings (env-driven)
│   ├── deps.py                   # shared FastAPI dependencies (db, auth, providers)
│   │
│   ├── api/                      # ── API LAYER ──
│   │   ├── router.py             # top-level /api/v1 aggregation
│   │   ├── errors.py             # exception handlers → HTTP responses
│   │   └── v1/
│   │       ├── auth.py           # /auth (apple, email, refresh)
│   │       ├── market.py         # /market (quotes, candles, search)
│   │       ├── watchlist.py      # /watchlist
│   │       ├── portfolio.py      # /portfolio, /holdings
│   │       ├── recommendations.py# /recommendations
│   │       ├── news.py           # /news
│   │       ├── notifications.py  # /notifications, device registration
│   │       └── user.py           # /me, risk profile
│   │
│   ├── schemas/                  # Pydantic request/response DTOs (API contracts)
│   │   ├── auth.py
│   │   ├── market.py
│   │   ├── portfolio.py
│   │   ├── recommendation.py
│   │   ├── news.py
│   │   └── common.py
│   │
│   ├── services/                 # ── SERVICE LAYER (use-cases) ──
│   │   ├── auth_service.py
│   │   ├── market_service.py
│   │   ├── portfolio_service.py
│   │   ├── recommendation_service.py
│   │   ├── news_service.py
│   │   └── notification_service.py
│   │
│   ├── ai/                       # ── AI ORCHESTRATION LAYER ──
│   │   ├── committee.py          # deterministic Investment Committee engine
│   │   ├── scoring.py            # weighted model, recommendation mapping
│   │   ├── context.py            # AgentContext assembly (data bundle per symbol)
│   │   ├── base.py               # Agent ABC, AgentResult schema
│   │   ├── agents/
│   │   │   ├── news_sentiment.py
│   │   │   ├── technical.py
│   │   │   ├── fundamental.py
│   │   │   ├── macro.py
│   │   │   ├── risk.py
│   │   │   └── portfolio_fit.py
│   │   ├── indicators/           # deterministic compute cores
│   │   │   ├── technical_math.py # RSI, MACD, MAs, momentum, breakout, volume
│   │   │   ├── fundamental_math.py
│   │   │   └── risk_math.py      # volatility, concentration, exposure
│   │   └── prompts/              # LLM prompt templates (narration only)
│   │       ├── sentiment.txt
│   │       ├── macro.txt
│   │       └── explanation.txt
│   │
│   ├── providers/                # ── PROVIDER LAYER ──
│   │   ├── base.py               # MarketDataProvider, LLMProvider Protocols
│   │   ├── router.py             # capability routing + fallback chains
│   │   ├── cache.py              # read-through cache (Redis/in-mem)
│   │   ├── rate_limit.py         # per-vendor token bucket
│   │   ├── market/
│   │   │   ├── finnhub.py
│   │   │   ├── alphavantage.py
│   │   │   ├── fmp.py
│   │   │   └── newsapi.py
│   │   └── llm/
│   │       ├── openai_provider.py
│   │       └── anthropic_provider.py
│   │
│   ├── repositories/             # ── REPOSITORY LAYER ──
│   │   ├── base.py
│   │   ├── user_repo.py
│   │   ├── watchlist_repo.py
│   │   ├── portfolio_repo.py
│   │   ├── recommendation_repo.py
│   │   ├── news_repo.py
│   │   └── device_repo.py
│   │
│   ├── db/                       # ── DATABASE LAYER ──
│   │   ├── base.py               # declarative base, naming conventions
│   │   ├── session.py            # async engine + session factory
│   │   └── models/
│   │       ├── user.py
│   │       ├── instrument.py
│   │       ├── watchlist.py
│   │       ├── portfolio.py
│   │       ├── recommendation.py
│   │       ├── agent_output.py
│   │       ├── news.py
│   │       └── device.py
│   │
│   ├── scheduler/                # ── SCHEDULER LAYER ──
│   │   ├── scheduler.py          # JobScheduler interface + APScheduler impl
│   │   └── jobs/
│   │       ├── hourly_recommendations.py
│   │       └── news_ingest.py
│   │
│   ├── notifications/
│   │   ├── apns.py               # token-based APNS HTTP/2 sender
│   │   └── builder.py            # recommendation → notification payload
│   │
│   ├── core/                     # cross-cutting
│   │   ├── security.py           # JWT, password hashing, Apple token verify
│   │   ├── logging.py            # structured logging setup
│   │   └── exceptions.py         # domain exceptions
│   │
│   └── domain/                   # pure domain types/enums (no I/O)
│       ├── enums.py              # Recommendation, RiskLevel, Signal, MarketRegime
│       └── types.py
│
└── tests/
    ├── conftest.py               # fixtures: test db, fake providers, fake LLM
    ├── unit/
    │   ├── ai/                   # indicator math, scoring, committee determinism
    │   ├── services/
    │   └── core/
    ├── integration/
    │   └── api/                  # endpoint tests against test db + fakes
    └── fixtures/                 # sample provider payloads
```

### Backend conventions
- **One aggregate per repository.** Repos return domain objects, not ORM rows where
  it matters.
- **Schemas vs models vs domain.** `schemas/` = API DTOs (Pydantic), `db/models/` =
  persistence (SQLAlchemy), `domain/` = pure enums/value types. No layer leaks.
- **Agents depend only on `AgentContext` + `LLMProvider`** — never on the DB or HTTP
  directly. This makes them trivially testable.

---

## Web (`web/`) — Responsive PWA

React + Vite + TypeScript + Tailwind, organized by **feature** over a shared core. The
clean-architecture layers map cleanly to web idioms: Presentation = components/pages,
ViewModels = hooks (TanStack Query), Services = session/push, Repository = data access,
Models = TS types, Networking = the API client. Installable as a PWA (Add to Home
Screen on iOS/Android) for an app-like experience without an app store.

```
web/
├── README.md                       # setup, run, build, deploy, test
├── index.html
├── package.json
├── vite.config.ts                  # Vite + PWA plugin
├── tsconfig.json
├── tailwind.config.js / postcss.config.js
├── .env.example                    # VITE_API_BASE_URL
├── public/
│   ├── manifest.webmanifest        # PWA manifest (name, icons, theme)
│   └── icons/                      # PWA / home-screen icons
└── src/
    ├── main.tsx                    # entry, providers (Query, Router, Auth)
    ├── App.tsx                     # shell: nav + routed outlet
    ├── router.tsx                  # routes + auth guards
    │
    ├── api/                        # ── NETWORKING LAYER ──
    │   ├── client.ts               # fetch wrapper: base URL, JWT attach, 401→refresh
    │   ├── endpoints.ts            # typed endpoint paths
    │   └── errors.ts               # API error → typed error
    │
    ├── models/                     # ── MODELS LAYER (TS types ⇄ API contracts) ──
    │   ├── auth.ts  market.ts  portfolio.ts  recommendation.ts  news.ts  user.ts
    │
    ├── repositories/               # ── REPOSITORY LAYER ──
    │   ├── authRepository.ts        marketRepository.ts
    │   ├── portfolioRepository.ts   watchlistRepository.ts
    │   ├── newsRepository.ts        recommendationRepository.ts
    │
    ├── services/                   # ── SERVICES LAYER ──
    │   ├── session.ts              # token storage + session lifecycle
    │   └── push.ts                 # web push / notification opt-in (Phase 5)
    │
    ├── store/                      # client state (Zustand): auth/session
    │   └── authStore.ts
    │
    ├── hooks/                      # ── VIEWMODELS (TanStack Query hooks) ──
    │   ├── useAuth.ts  useMarket.ts  useWatchlist.ts
    │   ├── usePortfolio.ts  useRecommendations.ts  useNews.ts
    │
    ├── components/                 # shared design system + UI primitives
    │   ├── ui/                     # Button, Card, Input, Badge, Skeleton, Toast
    │   ├── charts/                 # price/candles chart wrapper
    │   └── layout/                 # AppShell, NavBar, TabBar
    │
    ├── features/                   # ── PRESENTATION (pages per feature) ──
    │   ├── auth/                   # Login / Register / Apple
    │   ├── markets/                # list, instrument detail + chart
    │   ├── watchlist/
    │   ├── portfolio/              # holdings + summary
    │   ├── recommendations/        # rec card + full reasoning + agent breakdown
    │   └── settings/               # risk profile, notifications
    │
    └── lib/                        # formatting, helpers, constants
```

### Web conventions
- **Repositories wrap the API client; hooks (TanStack Query) are the "ViewModels."**
  Components consume hooks; hooks call repositories; repositories call `client.ts`.
  Tests mock the repository or the client.
- **Auth:** JWT access token in memory + persisted (localStorage) for reload; the
  client auto-attaches it and transparently refreshes on `401`. (localStorage is an
  acceptable XSS tradeoff for a personal tool; documented in the web README.)
- **Feature-first** under `features/`, shared infra under `components/`, `api/`,
  `services/`. Cross-feature types live in `models/`.
- **PWA:** `vite-plugin-pwa` generates the service worker + manifest so the app is
  installable and works offline-ish.
- **Responsive:** Tailwind breakpoints; bottom tab bar on mobile, side nav on desktop.
- **Testing:** Vitest + Testing Library for components/hooks with mocked repositories.

> **Backend unchanged.** The web app consumes the exact same FastAPI `/api/v1`
> contracts the iOS plan targeted — the *backend-only call path* decision is what makes
> this client swap nearly free.
