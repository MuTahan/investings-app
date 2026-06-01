# 01 — System Architecture

This document describes the overall architecture, the major components, and the
reasoning behind each significant decision.

---

## 1. High-level topology

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       Web App (React + Vite PWA)                           │
│   Presentation → Hooks(VM) → Services → Repository → API client → Models    │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │  HTTPS (JSON, JWT bearer)
                                    │  web push / notification opt-in
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          FastAPI Backend (Python)                          │
│                                                                            │
│  ┌────────────┐   ┌──────────────┐   ┌──────────────────────────────────┐ │
│  │  API Layer │ → │ Service Layer│ → │     AI Orchestration Layer       │ │
│  │ (routers)  │   │ (use-cases)  │   │  6 Agents + Committee Engine     │ │
│  └────────────┘   └──────┬───────┘   └───────────────┬──────────────────┘ │
│                          │                           │                    │
│                   ┌──────▼───────┐          ┌────────▼─────────┐          │
│                   │  Repository  │          │ Provider Clients │          │
│                   │   Layer      │          │ MarketData / LLM │          │
│                   └──────┬───────┘          └────────┬─────────┘          │
│                          │                           │                    │
│   ┌──────────────┐  ┌────▼─────┐   ┌─────────┐  ┌────▼──────────────────┐ │
│   │  Scheduler   │  │ Postgres │   │  Redis  │  │ Finnhub / AlphaVantage│ │
│   │ (APScheduler)│  │   (DB)   │   │ (cache) │  │ FMP / NewsAPI / OpenAI│ │
│   └──────────────┘  └──────────┘   └─────────┘  │ / Anthropic           │ │
│                                                 └───────────────────────┘ │
│   ┌──────────────┐                                                        │
│   │ APNS Sender  │ ──────────────────────────────► Apple Push Service     │
│   └──────────────┘                                                        │
└──────────────────────────────────────────────────────────────────────────┘
```

**Decision: backend-only call path.** The web app (and any future client) talks only
to our backend. No third-party API keys ever ship to the browser. This centralizes
caching, rate-limiting, cost control, and failover, and means we can change data
vendors without touching the client. This client-agnostic design is exactly what let
us swap the planned iOS app for a responsive web PWA with zero backend changes.

---

## 2. Backend layered architecture

We use a clean, dependency-inwards layering. Each layer only knows about the layer
directly beneath it; dependencies point toward the domain, never outward toward I/O.

| Layer                  | Responsibility                                                                 | Knows about            |
|------------------------|---------------------------------------------------------------------------------|------------------------|
| **API Layer**          | HTTP routing, request/response (Pydantic), auth guards, validation, error mapping | Service layer          |
| **Service Layer**      | Use-cases / business workflows (e.g. "generate recommendations for user")        | Repos, Orchestration, Providers |
| **AI Orchestration**   | The 6 agents + the deterministic Committee engine                                | Providers, domain models |
| **Scheduler Layer**    | Cron-like jobs (hourly recommendation refresh, news ingest)                       | Service layer          |
| **Repository Layer**   | Persistence abstraction over the DB; one repo per aggregate                       | Database (SQLAlchemy)  |
| **Database Layer**     | SQLAlchemy models, sessions, Alembic migrations                                  | Postgres               |
| **Provider Layer**     | External API clients (market data + LLM) behind unified interfaces               | HTTP, vendor SDKs      |

**Why this split:** the AI Orchestration layer is the product's differentiator and
the most likely to change. Isolating it behind the Service layer means the API and
persistence can stay stable while agents evolve. The Provider layer isolates vendor
churn (rate limits, schema changes, swaps) to one place.

### Dependency injection
FastAPI's dependency system wires concrete implementations (DB session, provider
clients, repos) into services. Interfaces are Python `Protocol`/ABC types so unit
tests inject fakes. No global singletons for I/O.

---

## 3. AI Orchestration: the core idea

The orchestration layer is split deliberately to control **cost, latency, and
determinism**:

```
                         ┌─────────────────────────────┐
   Symbol + User ──────► │   Investment Committee       │
   context               │   (deterministic engine)     │
                         └──────────────┬──────────────┘
                                        │ fans out (async)
        ┌──────────────┬───────────────┼───────────────┬──────────────┐
        ▼              ▼               ▼               ▼              ▼
  ┌───────────┐  ┌───────────┐  ┌────────────┐  ┌──────────┐  ┌──────────────┐
  │   News &  │  │ Technical │  │Fundamental │  │  Macro   │  │ Risk +       │
  │ Sentiment │  │ Analysis  │  │ Analysis   │  │          │  │ Portfolio-Fit│
  └─────┬─────┘  └─────┬─────┘  └─────┬──────┘  └────┬─────┘  └──────┬───────┘
        │ score+expl   │ score+expl   │ score+expl   │ score+expl    │ score+expl
        └──────────────┴───────┬──────┴──────────────┴───────────────┘
                               ▼
                    ┌────────────────────────┐
                    │  Weighted aggregation  │  (fixed weights, deterministic)
                    │  + conflict "debate"   │
                    │  + risk gating         │
                    └───────────┬────────────┘
                                ▼
              Recommendation + confidence + reasons + risks +
              suggested action + personalization + notif priority
```

**Decision: anchored autonomy (deterministic core + bounded Claude reasoning).**
Every LLM decision is bounded by a deterministic anchor, giving Claude genuine
reasoning power while preserving reproducibility, safety, and auditability:
- **Compute core (deterministic):** indicators (RSI, MACD, MAs, momentum, volume),
  fundamental ratios (P/E, EPS/revenue growth, margins), volatility, concentration,
  diversification — computed in Python from provider data. These produce the
  normalized `0–100` **anchor** scores.
- **Empowered agents (Claude):** each agent's LLM reasons over the computed evidence
  and may **adjust its score within ±10 points**, with a written justification.
- **Committee Chair (Claude):** receives the full staff report and issues the final
  rating, but may move only **±1 rating band** from the deterministic anchor rating.
- **Hard rails stay deterministic:** the risk gate caps any rating (high risk can't be
  STRONG_BUY) and is re-applied after the Chair; the ±bounds mean no hallucination can
  flip AVOID→STRONG_BUY. Both anchor and adjusted values are persisted for audit.

A `decision_mode` flag (`deterministic | chair_assisted | empowered`) selects how much
autonomy is active; **`deterministic` is always available and is the test oracle**, so
the reproducible core remains a verifiable safety net. **Model tiering** keeps cost in
check: Haiku-tier for agents, Sonnet/Opus-tier for the Chair.

**Why:** the deterministic anchor keeps the system reproducible, unit-testable, and
debuggable; the bounded LLM layers add real synthesis of conflicting signals without
letting the model run unchecked. See [06-ai-agents.md](06-ai-agents.md) for full specs.

**Decision: deterministic anchor, Claude Chair decides within bounds.** The
deterministic weighted model produces an **anchor rating**; the Chair issues the final
rating within ±1 band of it. Weight model:

| Component               | Weight |
|-------------------------|--------|
| News sentiment          | 20%    |
| Technical momentum      | 20%    |
| Fundamentals            | 20%    |
| Macro trend             | 15%    |
| Portfolio fit           | 15%    |
| Diversification fit     | 10%    |

Risk acts as a **gate/modifier** (can cap or downgrade a recommendation), not a
weight. This matches the spec and keeps scoring auditable.

```
                 ┌─────────────────────────────────────────────┐
  agent scores ─►│ deterministic weighted model → anchor rating│
                 └───────────────────┬─────────────────────────┘
                                     │ staff report (+ conflicts, risk gate)
                                     ▼
                       ┌──────────────────────────┐
                       │  Committee Chair (Claude) │  final rating within ±1 band
                       │  bounded synthesis        │  → risk gate re-applied (hard)
                       └──────────────────────────┘
```

---

## 4. Provider abstraction & resilience

```
        Service / Agents
              │
              ▼
    ┌───────────────────┐         ┌────────────────────────┐
    │ MarketDataProvider│◄────────│  Caching + RateLimiter  │
    │   (interface)     │         │  (Redis or in-memory)   │
    └─────────┬─────────┘         └────────────────────────┘
              │  routing + fallback chain
   ┌──────────┼───────────┬──────────────┐
   ▼          ▼           ▼              ▼
 Finnhub  AlphaVantage   FMP          NewsAPI
```

- **Unified interfaces:** `MarketDataProvider` (quotes, candles, fundamentals,
  news) and `LLMProvider` (chat/JSON completion). Each vendor is an adapter.
- **Routing + fallback:** each capability has a preferred vendor and an ordered
  fallback list (e.g. quotes: Finnhub → FMP → AlphaVantage). On rate-limit/error,
  route to the next.
- **Caching:** read-through cache keyed by `(capability, symbol, params)` with
  per-capability TTLs (quotes seconds, fundamentals hours, news minutes). Backed by
  Redis when configured, in-memory `cachetools` otherwise — same interface.
- **Rate limiting:** token-bucket per vendor to stay under free-tier quotas.

**Why:** free-tier APIs are the MVP's hard constraint. This layer is what keeps the
product alive under quotas and lets us swap vendors without touching agents.

---

## 5. Scheduler

**Decision: APScheduler (in-process AsyncIO) for the MVP.**
- Hourly job: refresh recommendations for active users' watchlists/holdings and
  enqueue notifications for high-priority changes.
- Periodic job: news ingestion + sentiment cache warming.

Wrapped behind a `JobScheduler` interface. The migration path to **Celery + Redis**
(for horizontal scale and durable queues) is a configuration swap, not a rewrite.
See [03-system-design.md](03-system-design.md) for the hourly job sequence.

---

## 6. Authentication & security

- **Methods:** Apple Sign-In (verify identity token against Apple's JWKS) and
  email/password (Argon2/bcrypt hashing). Both issue our own **JWT access +
  refresh tokens**.
- **Transport:** HTTPS only; JWT bearer on every authenticated request.
- **Secrets:** all vendor keys live in backend env/secret store only.
- **APNS:** token-based auth (p8 key); device tokens stored per user/device.
- **PII:** minimal — email, hashed password, Apple subject id, risk profile,
  holdings. No brokerage linkage in the MVP (no real-money actions).

> The app provides **informational recommendations only** — it never executes trades
> or moves money. This is a deliberate scope and safety boundary.

---

## 7. Caching strategy summary

| Data                | TTL          | Store           |
|---------------------|--------------|-----------------|
| Real-time quote     | 10–30s       | Redis/in-mem    |
| Intraday candles    | 1–5 min      | Redis/in-mem    |
| Fundamentals        | 6–24h        | Redis + DB      |
| Company/macro news  | 5–15 min     | Redis + DB      |
| Agent sub-scores    | 1h (per run) | DB (audit)      |
| Final recommendation| 1h           | DB (history)    |

Recommendations and agent outputs are **persisted** (not just cached) so the app can
show history and we can audit/debug the committee's reasoning over time.

---

## 8. Observability (MVP-appropriate)

- Structured JSON logging (request id, user id, symbol, agent timings).
- Per-agent latency + LLM token/cost counters.
- Provider call success/failure + fallback counters.
- Health endpoint (`/health`) checking DB and provider reachability.

Full metrics/tracing stack (Prometheus/OTel) is deferred — interfaces are logging
so it can be added without code churn.

---

## 9. Decisions log (summary)

| # | Decision | Rationale | Alternative rejected |
|---|----------|-----------|----------------------|
| 1 | Backend-only API path | Secret safety, cost/rate control, vendor agility | Client-direct calls (leaks keys) |
| 2 | Anchored autonomy: deterministic anchor + Claude Chair decides within ±1 band | Real synthesis of conflicts, yet bounded, auditable, safe | Pure-deterministic (no synthesis) / unbounded LLM (unsafe) |
| 3 | Empowered agents: bounded ±10 LLM adjustment over deterministic core | Richer per-agent reasoning, still anchored & testable | Narration-only agents / fully-LLM agents |
| 3b | Model tiering (Haiku agents, Sonnet/Opus Chair) + `deterministic` test mode | Cost control + reproducible test oracle | Single model everywhere |
| 4 | Provider abstraction + fallback + cache | Survive free-tier limits, swap vendors easily | Hardcoded single vendor |
| 5 | APScheduler now, Celery later | Zero extra infra for MVP, clean upgrade path | Celery upfront (overkill) |
| 6 | Redis optional behind cache interface | Run MVP with zero Redis, scale when needed | Mandatory Redis |
| 7 | Monorepo | Atomic cross-stack changes, one source of truth | Split repos |
| 8 | No trade execution | Safety & scope; informational product | Brokerage integration |
