# Investing AI — AI-Powered Investing for US Stocks & ETFs

An Investing.com-like iOS experience for **US Stocks & ETFs**, powered by a **deterministic multi-agent Investment Committee** that produces explainable, personalized recommendations, portfolio analysis, and market intelligence — delivered with push notifications.

> **Status:** Phase 1 — Architecture & Design (this document set). No application code yet.
> Implementation proceeds in approved phases (see [docs/07-roadmap.md](docs/07-roadmap.md)).

---

## What this is

- **Web app (React + Vite PWA)** — responsive, installable on desktop + phone; markets, watchlists, portfolio, AI recommendations with full reasoning.
- **Python backend (FastAPI)** — auth, data aggregation, the AI orchestration layer, scheduler, and APNS notifications.
- **Multi-agent AI** — six Claude-empowered specialist agents (News/Sentiment, Technical, Fundamental, Macro, Risk, Portfolio-Fit), each anchored to deterministic market math, feeding a **Committee Chair (Claude)** that issues one of `STRONG_BUY | BUY | HOLD | WATCH | AVOID` within bounded, auditable limits.

## Core design principles

1. **Backend-only secrets.** The iOS app never holds market-data or AI API keys. It only talks to our FastAPI backend.
2. **Anchored autonomy.** A deterministic weighted model produces an **anchor** rating that is fully reproducible and unit-testable. Claude then reasons on top within hard bounds: each agent may adjust its score ±10, and a **Committee Chair** (Claude) issues the final rating within ±1 band of the anchor. The risk gate is deterministic and re-applied last, so no LLM can flip AVOID→STRONG_BUY. Both anchor and adjusted values are logged for audit.
3. **Provider abstraction + fallback.** All four market-data vendors and both LLM vendors sit behind unified interfaces with caching and failover, so free-tier rate limits don't break the product.
4. **Simple now, scales later.** In-process async scheduler (APScheduler) and Redis-optional caching for the MVP, behind interfaces that allow a Celery/Redis swap with no business-logic changes.
5. **Modular clean architecture** on both stacks.

## Repository layout

```
investing-app/
├── README.md                  # this file
├── docs/                      # Phase 1 design (source of truth)
│   ├── 01-architecture.md     # system architecture & decisions
│   ├── 02-folder-structure.md # backend + iOS folder structures
│   ├── 03-system-design.md    # data flows, sequence diagrams
│   ├── 04-database-schema.md  # PostgreSQL schema & migrations
│   ├── 05-api-contracts.md    # REST API contracts
│   ├── 06-ai-agents.md        # agent + committee specifications
│   ├── 07-roadmap.md          # phased implementation plan
│   ├── 08-runbook.md          # run, operate, troubleshoot, limits
│   ├── 09-deploy-vps.md       # deploy to a VPS (HTTPS via Caddy)
│   └── 10-deploy-oracle.md    # deploy free on Oracle Always Free
├── backend/                   # FastAPI service (API, AI committee, scheduler)
├── web/                       # React + Vite PWA (nginx in prod)
├── docker-compose.yml         # local full stack: db + redis + api + web
└── docker-compose.prod.yml    # production stack + Caddy (auto HTTPS)
```

## Tech stack

| Layer            | Choice                                            |
|------------------|---------------------------------------------------|
| Web              | React, Vite, TypeScript, Tailwind, PWA, TanStack Query |
| Backend          | Python 3.11+, FastAPI, Pydantic v2                 |
| ORM / migrations | SQLAlchemy 2.0 (async) + Alembic                  |
| Database         | PostgreSQL 15+                                     |
| Cache            | Redis (optional in MVP, interface-ready)          |
| Scheduler        | APScheduler (MVP) → Celery/Redis (scale)          |
| Notifications    | ntfy + Telegram (fan-out, swappable)              |
| Auth             | Apple Sign-In (backend) + email/password, JWT     |
| Market data      | Finnhub, AlphaVantage, Financial Modeling Prep, NewsAPI |
| AI providers     | OpenAI, Anthropic (behind one `LLMProvider`)      |
| Infra            | Docker, docker-compose                            |

## Getting started

Run the entire stack with one command:

```bash
docker compose up --build
```

Then open **http://localhost:8080** (web) — register an account and explore. The API
+ Swagger docs are at **http://localhost:8000/docs**.

Works with **no API keys** (AI in `deterministic` mode, no live quotes). To go live —
market data, Claude-powered committee, and push notifications — add keys to the `api`
service in [docker-compose.yml](docker-compose.yml). Optional demo data:

```bash
docker compose exec api python -m app.db.seed_demo   # demo@example.com / demodemo123
```

Full operations guide: **[docs/08-runbook.md](docs/08-runbook.md)**. Per-stack details:
[backend/README.md](backend/README.md), [web/README.md](web/README.md).

## Status

MVP complete — all six phases delivered. The full loop runs end to end: auth → markets
→ portfolio → AI committee recommendation (explained + personalized) → hourly refresh →
push notification. Verified in Docker (backend 61 tests, web 16 tests, both builds green).

## Reading order

New to the project? Read the docs in numeric order. The most important documents are
[01-architecture.md](docs/01-architecture.md) and [06-ai-agents.md](docs/06-ai-agents.md).
