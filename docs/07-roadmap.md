# 07 — Implementation Roadmap

Incremental, approval-gated delivery. Each phase is self-contained, ends with a
stop for review, and ships code + README + setup + tests (no shortcuts).

Legend: ✅ done · ▶ current · ⏸ awaiting approval · ☐ planned

---

## Phase 1 — Architecture & Design  ✅ COMPLETE
**Goal:** complete, production-grade blueprint. No app code.

Deliverables:
- ✅ System architecture & decisions — [01-architecture.md](01-architecture.md)
- ✅ Backend + iOS folder structures — [02-folder-structure.md](02-folder-structure.md)
- ✅ System design / data flows — [03-system-design.md](03-system-design.md)
- ✅ PostgreSQL schema — [04-database-schema.md](04-database-schema.md)
- ✅ REST API contracts — [05-api-contracts.md](05-api-contracts.md)
- ✅ AI agents + committee spec — [06-ai-agents.md](06-ai-agents.md)
- ✅ This roadmap

**Locked decisions (from kickoff):** backend-only call path · depth-first on the AI
committee · live free-tier data APIs with caching.

➡ Approved.

---

## Phase 2 — Backend Foundation  ✅ COMPLETE
**Goal:** a running FastAPI service with auth, DB, providers, and the API skeleton —
everything the AI layer will plug into.

Scope:
- Project scaffold: `pyproject.toml`, ruff/black/mypy, `Dockerfile`, `docker-compose`
  (api + postgres + optional redis), `.env.example`.
- Config (`app/config.py`), structured logging, app factory + lifespan.
- DB layer: SQLAlchemy models for all tables in [04](04-database-schema.md), async
  session, Alembic initial migration + instrument seed.
- Repositories for each aggregate.
- Auth: email/password (Argon2) + Apple Sign-In verify, JWT access/refresh, guards.
- Provider layer: `MarketDataProvider`/`LLMProvider` interfaces, the four market
  adapters + two LLM adapters, routing + fallback + cache + rate-limit (LLM/agents
  stubbed minimally — full logic in Phase 4).
- API endpoints: auth, user/risk-profile, market (search/quote/candles), watchlist,
  portfolio, news. (`/recommendations` returns a stub until Phase 4.)
- Tests: unit (security, repos, providers with fakes) + integration (API against
  test DB), `conftest` fixtures.
- `backend/README.md` with full setup/run/test instructions.

**Exit criteria:** `docker-compose up` serves a healthy API; auth + market +
portfolio endpoints work against live free-tier data; tests green.

**Delivered:** FastAPI app factory + layered architecture; 13-table Postgres schema +
Alembic migration + instrument seed; Argon2/JWT auth + Apple Sign-In verify; provider
router (Finnhub/FMP/AlphaVantage/NewsAPI) with fallback, cache, rate-limit; Anthropic/
OpenAI LLM adapters + stub; full auth/market/watchlist/portfolio/news endpoints;
`/recommendations` stubbed (501) for Phase 4; **32 tests passing + ruff clean, verified
in Docker**; `backend/README.md`.

➡ Approved.

---

## Phase 3 — Web Foundation (Responsive PWA)  ✅ COMPLETE
**Goal:** a responsive React PWA that authenticates and renders
markets/watchlist/portfolio against the Phase 2 backend. (Replaces the original iOS
plan — chosen for personal use: deploy once, run on desktop + phone, no app store.)

Scope:
- Vite + React + TS + Tailwind scaffold; `vite-plugin-pwa` (installable, offline-ish).
- `api/client.ts` (fetch wrapper, JWT attach, `401`→refresh); session store (Zustand).
- Models (TS types) matching the API contracts; repositories + hooks (TanStack Query).
- Features: Auth (email + Apple), Markets (list + detail + price chart), Watchlist,
  Portfolio (holdings + summary), Settings (risk profile). Recommendations page shows a
  placeholder until Phase 4.
- Design system basics (Tailwind theme, shared UI components); responsive nav
  (bottom tabs on mobile, side nav on desktop).
- Tests: Vitest + Testing Library (components/hooks with mocked repositories);
  build verified (`vite build`), dev server smoke-checked.
- `web/README.md` setup/run/build/deploy instructions.

**Exit criteria:** sign in, browse markets, manage watchlist/portfolio, edit risk
profile — all live against the backend, responsive on mobile + desktop, installable as
a PWA. Build + tests green (verifiable in this environment).

**Delivered:** Vite/React/TS/Tailwind PWA; `api/client.ts` with JWT attach +
401→refresh→retry + forced-logout; models/repositories/hooks per resource; Zustand auth
store; responsive AppShell (side nav desktop / bottom tabs mobile); features — Auth
(email), Markets (search + detail + lightweight-charts candlesticks), Watchlist,
Portfolio (summary + holdings CRUD), Settings (risk profile), Recommendations
("Phase 4" placeholder, full render ready); **15 Vitest tests + typecheck + production
build all green in Docker**; `web/README.md`. (Apple Sign-In: backend-ready, web UI ships
email/password.)

➡ Approved.

---

## Phase 4 — AI Orchestration  ⏸ AWAITING APPROVAL
**Goal:** the differentiator — six agents + deterministic committee, wired end to end.
**Status: ✅ COMPLETE.**

Scope:
- `indicators/` deterministic math (technical, fundamental, risk) with fixture tests.
- Six **empowered agents** ([06](06-ai-agents.md)): deterministic compute core +
  bounded ±10 Claude adjustment with justification; per-agent fallback to anchor.
- `context.py` assembly (shared single fetch), `LLMProvider` with **model tiering**
  (Haiku agents / Sonnet-Opus Chair), JSON sentiment extraction, templated fallbacks.
- `committee.py` + `scoring.py`: weighted anchor model, regime modifier, risk gating,
  anchor-rating mapping, **Committee Chair** (Claude, ±1 band, re-gated by risk,
  fallback to anchor), `decision_mode`, confidence, notif priority, `weights_version`.
- Persist `recommendations` + `agent_outputs`; freshness gate.
- Real `/recommendations/{symbol}`, `/recommendations?scope=`, history endpoints.
- Web Recommendations feature: rec card + full reasoning + agent breakdown UI.
- Tests: committee determinism (golden cases), indicator math, agents with fake LLM,
  end-to-end recommendation integration test.

**Exit criteria:** request a personalized, explained recommendation for a symbol;
`deterministic` mode yields identical anchor ratings for identical inputs; the Chair's
final stays within ±1 band and is re-gated by risk; agent base-vs-adjusted breakdown
and `chair_rationale` visible in the app.

**Delivered:** indicator math (RSI/MACD/SMA/momentum/breakout/volatility), fundamental
& risk scoring; six agents (deterministic compute + bounded ±10 Claude adjustment,
fallback to anchor); resilient `context.py` + macro snapshot (VIX/SPY); `scoring.py`
(weights v1, regime modifier, risk gating, anchor thresholds, ±1 ladder clamp,
confidence, notif priority); `committee.py` Chair (±1 band, risk re-gate, fallback);
persistence of `recommendations` + `agent_outputs` with audit fields; freshness gate;
real `/recommendations/{symbol}` + `?scope=` + `/history`. **+21 tests (53 total) +
ruff clean, verified in Docker.** Web Recommendations page renders it live (no FE change).

➡ Approved.

---

## Phase 5 — Notifications & Hourly Scheduler  ⏸ AWAITING APPROVAL
**Goal:** proactive intelligence.

Scope:
- `JobScheduler` interface + APScheduler impl; hourly recommendation refresh job
  (symbol dedup, per-user personalization) + news ingest job.
- **Notification channel (to pick at Phase 5):** Web Push (PWA) and/or a simple
  personal channel like a Telegram bot / [ntfy.sh](https://ntfy.sh) / email digest —
  far simpler than APNS for a single user. `notifications/` builder + sender behind an
  interface so the channel is swappable.
- Subscription/registration endpoints; notification log; per-run caps / quiet hours.
- Web: notification opt-in (`services/push.ts`), deep-link into a recommendation.
- Tests: scheduler job logic (fake clock + fakes), notification priority/build.

**Exit criteria:** an hourly run recomputes recommendations and delivers high-priority
changes to the chosen channel; following the notification opens the recommendation.

**Delivered:** `Notifier` abstraction fanning out to **ntfy + Telegram** (each active
only when configured) + notification builder; `JobScheduler` (APScheduler) hourly job
wired into app lifespan (symbol dedup per user, quiet hours, per-run cap); freshness-gated
recompute; `notification_log` + in-app feed; endpoints `GET /notifications` and
`POST /notifications/run` (manual trigger); **web Alerts page + nav** ("Run now" + feed).
**Tests: backend 61 (notifier payloads, composite fan-out, builder, run/feed e2e) + web 16
(Alerts page) — all green in Docker; ruff + typecheck + build clean.**

➡ Approved.

---

## Phase 6 — MVP Finalization  ✅ COMPLETE
**Goal:** harden, document, demo.

Scope:
- End-to-end smoke pass; fix gaps; tighten error states & empty states in the app.
- Caching/rate-limit tuning against real free-tier quotas; cost report for LLM usage.
- Observability pass (timings, provider/LLM counters, `/health` completeness).
- Final docs: top-level README quickstart, architecture diagram refresh, runbook,
  known limitations & "scale later" notes (Celery/Redis, metrics stack).
- Demo script + seed data for a compelling first-run experience.

**Delivered:** one-command full stack ([docker-compose.yml](../docker-compose.yml):
db+redis+api+web) with a web `Dockerfile` (nginx, `/api` proxy → no CORS); request-id +
`duration_ms` logging middleware; enriched `/health` (db, llm, vendors, channels,
scheduler); web `ErrorBoundary`; `seed_demo` (demo user + watchlist + portfolio);
[08-runbook.md](08-runbook.md) (run/operate/troubleshoot/limits/cost/scale) + refreshed
root README. **Full-stack smoke verified in Docker on real Postgres**: migration + seed,
`/health` via nginx + api, register → AAPL recommendation (6 agents) → portfolio summary.

**Exit criteria:** a runnable, documented, tested MVP demonstrating the full loop:
auth → markets → portfolio → AI committee recommendation with explanations →
hourly refresh → push notification. ✅

---

## 🎉 MVP COMPLETE — all six phases delivered.
Backend 61 tests + web 16 tests green in Docker; ruff/typecheck/builds clean; full-stack
smoke passed on real Postgres. Run it: `docker compose up --build` → http://localhost:8080.

---

## Cross-cutting standards (every phase)
- Explain architectural decisions in the phase write-up.
- Show the folder structure touched.
- Production-grade, modular code — no placeholders, no dead scaffolding.
- README + setup instructions kept current.
- Tests for new logic (determinism for AI, contract tests for API, mocks for the web).
- No secrets in code; `.env.example` documents every required key.

## Out of scope for the MVP (deliberately)
- Real-money / brokerage execution (informational product only).
- Native iOS/Android apps (responsive PWA covers mobile).
- Options, crypto, non-US equities.
- Backtesting engine, social features, real-time websocket streaming.
- Full metrics/tracing stack and Celery/Redis scale-out (interfaces are ready).
