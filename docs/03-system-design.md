# 03 — System Design (Data Flows & Sequences)

Concrete flows for the most important operations. Diagrams are ASCII sequence
sketches; they map 1:1 to the layers in [01-architecture.md](01-architecture.md).

---

## 1. On-demand recommendation for a symbol

User opens an instrument detail screen and requests the AI recommendation.

```
iOS                Backend API        Service            Committee/Agents      Providers/Cache       DB
 │ GET /reco/AAPL ──►│                  │                    │                     │                  │
 │  (JWT)            │ authz            │                    │                     │                  │
 │                   │── get_reco ─────►│                    │                     │                  │
 │                   │                  │ check fresh reco? ─┼─────────────────────┼────────────────► │
 │                   │                  │◄── cached (<1h)? ──┼─────────────────────┼──────────────────│
 │                   │                  │  if fresh: return  │                     │                  │
 │                   │                  │  else build ctx ───┼────────────────────►│ quotes/candles/  │
 │                   │                  │                    │   AgentContext      │ fundamentals/news│
 │                   │                  │── evaluate(ctx) ──►│                     │                  │
 │                   │                  │                    │ fan-out 6 agents    │                  │
 │                   │                  │                    │  (async gather)     │  LLM (narrate)   │
 │                   │                  │                    │ weighted aggregate  │                  │
 │                   │                  │                    │ + risk gate + debate│                  │
 │                   │                  │◄── Recommendation ─│                     │                  │
 │                   │                  │── persist reco + agent_outputs ──────────┼────────────────► │
 │                   │◄── RecoResponse ─│                    │                     │                  │
 │◄── 200 JSON ──────│                  │                    │                     │                  │
```

Notes:
- **Freshness gate** avoids recomputation: if a `<1h` recommendation exists, return
  it. A `?refresh=true` query forces recompute.
- **AgentContext** is assembled once and shared by all agents (single fetch of
  quotes/candles/fundamentals/news), minimizing provider calls.
- **Agents run concurrently** via `asyncio.gather`. Total latency ≈ slowest agent
  (the LLM narration calls), not the sum.

---

## 2. Investment Committee evaluation (internal)

```
evaluate(context) ->
  # each agent: deterministic compute → base_score; Claude adjusts within ±10 (empowered mode)
  results = await gather(
     news_sentiment.run(ctx, llm),   # Claude extracts sentiment + reasons → score
     technical.run(ctx, llm),        # RSI/MACD/MA/momentum core; Claude interprets → score
     fundamental.run(ctx, llm),      # ratio core; Claude judges quality → score
     macro.run(ctx, llm),            # regime classifier core; Claude refines → score
     risk.run(ctx, llm),             # volatility/concentration core → risk_level (LLM may raise only)
     portfolio_fit.run(ctx, llm),    # fit + diversification core; Claude reasons → fit_score
  )

  composite   = weighted_sum(results, WEIGHTS)         # deterministic over final agent scores
  composite  += clamp(macro_regime_modifier(macro), -5, +5)
  composite   = apply_risk_gate(composite, risk)       # hard cap if medium/high risk
  composite   = clamp(composite + portfolio_fit.modifier, 0, 100)
  anchor      = map_to_rating(composite)               # STRONG_BUY..AVOID (deterministic)
  conflicts   = detect_conflicts(results)              # e.g. bullish TA vs bearish fundamentals

  if ctx.decision_mode == "deterministic":
     final = anchor                                    # test/fallback path
  else:
     chair = await llm_chair.decide(staff_report=results, composite, anchor,
                                    conflicts, risk_gate, user_profile)  # Claude, JSON
     final = clamp_to_band(chair.rating, anchor, max_bands=1)  # ±1 band only
     final = apply_risk_gate_rating(final, risk)        # risk gate re-applied (hard)
     # on LLM failure/invalid → final = anchor (fallback)

  confidence = confidence_from(agreement, data_quality, risk, chair_deviation)
  priority   = notification_priority(final, confidence, delta_vs_last)

  return Recommendation(final, anchor, confidence, composite, horizon, reasons, risks,
                        suggested_action, personalization, chair_rationale,
                        priority, decision_mode, breakdown)
```

The deterministic path (anchor) uses fixed thresholds and **same inputs ⇒ same anchor**
— that is what the determinism tests assert. The Chair can only move ±1 band off the
anchor and is re-gated by risk, so autonomy stays bounded and auditable. See
[06-ai-agents.md](06-ai-agents.md) §Committee.

---

## 3. Hourly scheduled refresh + notifications

```
APScheduler (hourly)
   │
   ├─ load active users + their watchlist/holding symbols  ──► DB
   │
   ├─ for each unique symbol (deduped across users):
   │     build AgentContext (shared cache) ──► Providers/Cache
   │     evaluate via Committee (per user for fit/risk personalization)
   │     persist new Recommendation + agent_outputs ──► DB
   │
   ├─ diff vs last recommendation per (user, symbol)
   │     if priority >= HIGH or rating changed up/down:
   │        build APNS payload ──► notifications/builder
   │        send via APNS ──► Apple Push
   │
   └─ record run metrics (latency, provider calls, LLM cost)
```

Cost controls:
- **Symbol dedup** across users for the data-fetch + the non-personalized agents
  (News/Technical/Fundamental/Macro run once per symbol, shared). Only Risk +
  Portfolio-Fit + the Committee Chair re-run per user.
- **Quiet hours / batching** to avoid notification spam: a user receives at most N
  high-priority pushes per run, prioritized by confidence × delta.

---

## 4. Authentication flows

### Apple Sign-In
```
iOS (ASAuthorization) ── identityToken ──► POST /auth/apple
Backend: verify token against Apple JWKS (aud, iss, exp, nonce)
         upsert user by apple_sub
         issue {access_jwt, refresh_jwt}
iOS: store tokens in Keychain (TokenStore)
```

### Email/password
```
POST /auth/register {email, password}
   → hash (Argon2), create user, issue tokens
POST /auth/login {email, password}
   → verify hash, issue tokens
POST /auth/refresh {refresh_jwt}
   → rotate, issue new access token
```

`AuthInterceptor` on iOS attaches the access JWT and transparently refreshes on 401.

---

## 5. Device registration & push

```
iOS: register for remote notifications → APNS device token
POST /notifications/devices {device_token, platform: ios}
Backend: upsert device row keyed by (user_id, device_token)
Scheduler/notification_service: look up active devices when sending.
```

Invalid/expired tokens reported by APNS are pruned from `devices`.

---

## 6. Failure & fallback behavior

| Failure                         | Behavior                                                        |
|---------------------------------|-----------------------------------------------------------------|
| Primary data vendor rate-limited| Router falls back to next vendor for that capability            |
| All vendors fail for a capability| Agent runs with `data_quality=low`, lowers its confidence; committee notes it |
| LLM provider error/timeout      | Fall back to other LLM; if both fail, return deterministic score with a templated (non-LLM) explanation |
| DB unavailable                  | API returns 503; scheduler run aborts and retries next hour     |
| APNS token invalid              | Prune device; continue                                          |

**Principle:** the deterministic core can always produce a recommendation even if all
LLMs are down — only the prose explanation degrades to a template.

---

## 7. Latency budget (target, on-demand reco)

| Stage                         | Target      |
|-------------------------------|-------------|
| Context assembly (cached data)| < 150 ms    |
| Context assembly (cold fetch) | < 1.5 s     |
| Deterministic agent compute   | < 50 ms     |
| LLM narration (parallel)      | < 2.5 s     |
| Aggregation + persist         | < 100 ms    |
| **Total (warm cache)**        | **< 3 s**   |

Freshness gate makes repeat views effectively instant (DB read).
