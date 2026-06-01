# 06 — AI Agents & Investment Committee

The heart of the product. Six specialist agents feed a **Committee Chair** that makes
the final call — all anchored to a deterministic core for safety, auditability, and
testability.

## Core principle: anchored autonomy

Every LLM decision in the system is **bounded by a deterministic anchor**. This gives
Claude genuine reasoning power without sacrificing reproducibility or safety:

- **Agents** compute a deterministic `base_score` from market math, then Claude
  reasons over that evidence and may **adjust the score within ±10 points**, with a
  written justification. (*Empowered-agents mode.*)
- **The Committee Chair** (Claude) receives the full "staff report", weighs the
  conflicting signals, and issues the final rating — but may only move **±1 rating
  band** from the deterministic anchor rating. (*Chair-assisted mode.*)
- **Hard safety rails stay deterministic**: the risk gate can cap any rating (a
  high-risk symbol can never be STRONG_BUY), and the ±band limits mean no
  hallucination can flip AVOID→STRONG_BUY.
- **Everything is logged**: we persist both the deterministic anchor and the
  LLM-adjusted value at every level, so any deviation is auditable and we can monitor
  drift between the math and the model.
- **Graceful fallback**: any LLM timeout / malformed output falls back to the
  deterministic value. The system always produces a recommendation, even with all
  LLMs down (explanations degrade to templates).

### `decision_mode` (config flag)
| Mode | Agents | Chair | Use |
|------|--------|-------|-----|
| `deterministic` | base_score only (no LLM) | threshold map only | **tests / golden cases / fallback** — fully reproducible |
| `chair_assisted` | base_score only | Claude, ±1 band | lighter production |
| `empowered` ✅ | Claude, ±10 pts | Claude, ±1 band | **our production mode** |

The `deterministic` mode is always available and is what the regression/determinism
tests run against — so the deterministic core stays a verifiable safety net no matter
how much autonomy production uses.

### Model tiering (cost lever)
Roles map to different Claude models via the `LLMProvider` abstraction:
- **Agents** → fast/cheap model (e.g. Claude Haiku) for bounded reasoning + narration.
- **Chair** → stronger model (e.g. Claude Sonnet/Opus) for the high-stakes synthesis.

This is the main cost control given the empowered path adds calls (see §Cost).

---

## Shared types

### `AgentContext`
Assembled once per evaluation and passed to every agent (single data fetch).
```python
class AgentContext:
    instrument: Instrument              # symbol, type, sector
    quote: Quote                        # latest price/volume
    candles: list[Candle]               # OHLCV history (for indicators)
    fundamentals: Fundamentals          # PE, EPS, revenue, margins, etc.
    news: list[NewsItem]                # company + analyst items
    macro: MacroSnapshot                # inflation, rates, VIX, sector rotation
    user_profile: RiskProfile           # tolerance, horizon, objectives
    portfolio: PortfolioSnapshot        # holdings, weights, sector exposure
    data_quality: DataQuality           # per-source freshness/completeness flags
    decision_mode: DecisionMode         # deterministic | chair_assisted | empowered
```

### `AgentResult`
Uniform output every agent returns — note the **anchor + adjustment** pair.
```python
class AgentResult:
    agent: AgentName                    # enum
    base_score: float | None            # 0..100 deterministic anchor (None for risk)
    score: float | None                 # 0..100 final (= base_score in deterministic mode,
                                        #   else base_score + bounded LLM delta, clamped ±10)
    adjustment_delta: float             # score - base_score (audit; 0 in deterministic mode)
    confidence: float                   # 0..100
    signal: Signal                      # bullish | neutral | bearish
    payload: dict                       # agent-specific structured detail (the "evidence")
    reasoning: str                      # LLM analysis (or template in deterministic mode)
    adjustment_justification: str | None# why the LLM moved off the anchor (if it did)
    # risk agent additionally:
    risk_level: RiskLevel | None        # low | medium | high
    warnings: list[str]                 # risk only
```

### Agent base — the empowerment pattern
```python
class Agent(ABC):
    name: AgentName
    MAX_DELTA = 10.0                     # bounded LLM authority

    async def run(self, ctx, llm) -> AgentResult:
        evidence, base_score, signal = self.compute(ctx)      # deterministic core
        if ctx.decision_mode == "deterministic":
            return self._anchor_result(base_score, signal, evidence, template=True)
        # empowered: Claude reasons over the evidence and may adjust within ±MAX_DELTA
        verdict = await llm.analyze(self.prompt(ctx, evidence, base_score))  # JSON
        score = clamp(verdict.score, base_score - self.MAX_DELTA,
                                     base_score + self.MAX_DELTA)
        return AgentResult(score=score, base_score=base_score,
                           adjustment_delta=score - base_score,
                           reasoning=verdict.reasoning,
                           adjustment_justification=verdict.justification, ...)

    @abstractmethod
    def compute(self, ctx) -> tuple[dict, float, Signal]: ...   # deterministic
    @abstractmethod
    def prompt(self, ctx, evidence, base_score) -> Prompt: ...
```
`compute()` is pure and unit-tested. The LLM gets the *computed evidence* (not raw
data) and a structured schema to fill, so its output is validated and bounded. On
parse failure/timeout → return the anchor result (fallback).

`confidence` is auto-lowered when `data_quality` for the agent's inputs is poor.

---

## The six agents

For each: the deterministic compute core produces the anchor; Claude (Haiku-tier)
reasons over the evidence and adjusts within ±10.

### 1. News & Sentiment Agent (`news`)
**Purpose:** analyze news + market sentiment.
- **Inputs:** company news, macro news, analyst upgrades/downgrades, prior sentiment.
- **Compute core:** recency-weighted aggregation of per-headline sentiment → anchor `0..100`.
- **LLM role:** this is the most LLM-native agent — Claude both *extracts* structured
  sentiment + bull/bear signals from `ctx.news` text **and** reasons to the adjusted score.
- **Outputs:** `sentiment_score`, `bullish_signals[]`, `bearish_signals[]`, confidence, reasoning.
- **Cost control:** cap headlines (top ~8 by recency); cache sentiment per news URL.
- `payload`: `{ sentiment_score, bullish_signals, bearish_signals, n_articles }`.

### 2. Technical Analysis Agent (`technical`)
**Purpose:** momentum & trend opportunities.
- **Inputs:** RSI, MACD, MAs (50/200), momentum, breakout, volume — from `ctx.candles`.
- **Compute core:** `indicators/technical_math.py` → indicators → rules → anchor score + signal.
- **LLM role:** Claude interprets the indicator constellation (e.g. weighs a positive
  MACD crossover against overbought RSI) and adjusts within ±10 with justification.
- **Outputs:** `technical_score`, `signal`, confidence, reasoning.
- `payload`: `{ rsi, macd, macd_signal, sma50, sma200, momentum, breakout, volume_ratio }`.

### 3. Fundamental Analysis Agent (`fundamental`)
**Purpose:** long-term investment quality.
- **Inputs:** P/E, EPS growth, revenue growth, margins, valuation vs history/sector.
- **Compute core:** `fundamental_math.py` → ratios/growth → anchor score + quality assessment.
  (Type-aware: ETFs use expense ratio, breadth, tracking instead of single-company ratios.)
- **LLM role:** Claude judges quality nuance (e.g. margin trend vs valuation premium) and adjusts ±10.
- **Outputs:** `fundamental_score`, `quality_assessment`, confidence, reasoning.
- `payload`: `{ pe, forward_pe, eps_growth, revenue_growth, gross_margin, op_margin, valuation_vs_avg }`.

### 4. Macro Agent (`macro`)
**Purpose:** market context / regime.
- **Inputs:** inflation, rates, sector rotation, VIX, macro sentiment (`ctx.macro`).
- **Compute core:** deterministic regime classifier → anchor `macro_score` + `market_regime`.
- **LLM role:** Claude refines how supportive the regime is for *this* instrument's sector and adjusts ±10.
- **Outputs:** `macro_score`, `market_regime ∈ {risk_on, neutral, risk_off, late_cycle}`, reasoning.
  Also emits a small **regime modifier** the Chair sees.
- `payload`: `{ regime, vix, rate_trend, inflation_trend, sector_rotation }`.

### 5. Risk Agent (`risk`) — the gatekeeper
**Purpose:** prevent bad recommendations.
- **Inputs:** volatility, concentration, earnings risk, overvaluation, portfolio exposure.
- **Compute core:** `risk_math.py` → `risk_level ∈ {low, medium, high}` + `warnings[]`.
- **LLM role:** Claude articulates and prioritizes warnings; it can **raise** the
  assessed risk level but **never lower it below the deterministic floor** (safety:
  the gate only tightens, never loosens, under LLM influence).
- **Special role:** acts as a **hard gate** (caps max rating); carries no weight in the score.
- `payload`: `{ volatility, concentration_pct, sector_exposure_pct, earnings_in_days, overvalued }`.

### 6. Portfolio-Fit Agent (`portfolio_fit`)
**Purpose:** personalization.
- **Inputs:** user risk profile, holdings, diversification, sector exposure.
- **Compute core:** deterministic `fit_score` + `diversification_fit` + sector-delta.
- **LLM role:** Claude reasons about objective alignment & diversification benefit, adjusts ±10,
  and writes the personal `fit_reason`.
- **Outputs:** `fit_score`, `fit_reason`, `recommendation_modifier` (-10..+10), confidence.
- Feeds **two** committee components: `portfolio_fit` (15%) and `diversification_fit` (10%).
- `payload`: `{ fit_score, diversification_fit, sector_exposure_delta, objective_alignment }`.

---

## Investment Committee Engine

`ai/committee.py` — deterministic pipeline with a Claude Chair on top.

### Step 1 — fan-out
Run all six agents concurrently over the shared `AgentContext` (`asyncio.gather`).
In `empowered` mode each agent makes one bounded LLM call; total latency ≈ slowest agent.

### Step 2 — weighted base score (over agent *final* scores)
```
WEIGHTS = {
  "news":               0.20,   # News sentiment
  "technical":          0.20,   # Technical momentum
  "fundamental":        0.20,   # Fundamentals
  "macro":              0.15,   # Macro trend
  "portfolio_fit":      0.15,   # Portfolio fit
  "diversification_fit":0.10,   # Diversification fit
}  # sums to 1.00
composite_score = Σ (agent_score_i * weight_i)        # 0..100
```
`portfolio_fit` + `diversification_fit` both come from the Portfolio-Fit agent. Risk
is excluded from weighting (it gates). In `deterministic` mode this uses each agent's
`base_score`, making the whole pipeline reproducible.

### Step 3 — macro regime modifier
`composite_score += clamp(macro_regime_modifier, -5, +5)`.

### Step 4 — risk gating (deterministic, hard)
```
if risk_level == "high":   composite_score = min(composite_score, CAP_HIGH)  # e.g. 55
if risk_level == "medium": composite_score = min(composite_score, CAP_MED)   # e.g. 80
# hard vetoes (e.g. extreme overvaluation) can force max rating = WATCH
```

### Step 5 — personalization modifier
`composite_score = clamp(composite_score + clamp(portfolio_fit.recommendation_modifier, -10, +10), 0, 100)`

### Step 6 — anchor rating (fixed thresholds)
| composite_score | anchor_rating |
|-----------------|---------------|
| ≥ 80 | STRONG_BUY |
| 65–79 | BUY |
| 45–64 | HOLD |
| 30–44 | WATCH |
| < 30 | AVOID |

This `anchor_rating` is the deterministic recommendation. In `deterministic` mode it
**is** the final rating (Steps 7–8 skipped).

### Step 7 — Committee Chair (Claude, chair-assisted)
The Chair receives the **staff report**: every `AgentResult` (incl. base vs adjusted
scores + per-agent reasoning), detected conflicts, `composite_score`, `anchor_rating`,
the risk gate result, and the user's profile. It returns structured JSON:
```
{ final_rating, confidence, time_horizon,
  reasons[], risks[], suggested_action, personalization,
  chair_rationale }            # justification, required if it deviates from anchor
```
**Bounded authority:**
- `final_rating` may differ from `anchor_rating` by **at most ±1 band**
  (e.g. anchor BUY → Chair may pick STRONG_BUY, BUY, or HOLD; never WATCH/AVOID).
- The **risk gate is re-applied after** the Chair: a `high`-risk symbol is capped
  regardless of the Chair's choice.
- Output is schema-validated; on failure/timeout → `final_rating = anchor_rating`
  with a templated rationale (fallback).
- The Chair **synthesizes the debate**: it must explicitly address material conflicts
  (e.g. bullish technicals vs bearish fundamentals) in `reasons`/`risks` rather than
  papering over them.

### Step 8 — confidence, horizon, priority
- **Confidence:** `f(agent_agreement, mean_agent_confidence, data_quality, risk_penalty,
  chair_deviation_penalty)` — large Chair deviations from the anchor reduce confidence.
- **Time horizon:** technical-led → short/medium; fundamental/macro-led → long; tempered by user profile.
- **Notification priority:** `g(rating_change_vs_last, |Δscore|, confidence, risk_level)`
  → `low | normal | high | critical`.

### Output (matches API `GET /recommendations/{symbol}`)
```
Recommendation:
  rating (= final_rating), anchor_rating, confidence, composite_score, time_horizon,
  reasons[], risks[], suggested_action, personalization, chair_rationale,
  notif_priority, decision_mode, weights_version, model_versions, agent_breakdown[]
```
`agent_breakdown[]` exposes each agent's `base_score`, adjusted `score`,
`adjustment_justification`, signal, confidence, and reasoning — full explainability.

---

## Determinism & testing
- **Deterministic mode is the test oracle.** All committee/scoring/indicator logic is
  unit-tested in `deterministic` mode (no LLM): fixed `AgentContext` → identical
  `composite_score`, `anchor_rating`, `notif_priority`. This stays true regardless of
  production autonomy.
- **Indicator tests:** `technical_math` / `fundamental_math` / `risk_math` vs known fixtures.
- **Empowered-path tests:** agents + Chair tested with a **fake `LLMProvider`**
  returning canned JSON, asserting (a) bounds are enforced (±10 / ±1 band), (b) risk
  gate overrides the Chair, (c) malformed output falls back to the anchor.
- **Golden cases:** full fixtures (bullish, bearish, high-risk, poor-fit) lock anchor
  ratings; empowered runs assert final stays within the allowed band.

## Cost & latency (empowered mode)
Per evaluation ≈ **6 agent calls + 1 Chair call**. Controls:
- **Model tiering:** Haiku-tier for agents, Sonnet/Opus-tier for the Chair (biggest lever).
- **Symbol dedup in the hourly job:** the 4 non-personalized agents
  (news/technical/fundamental/macro) run **once per symbol** and are shared across all
  users holding it; only Risk + Portfolio-Fit + Chair run per (user, symbol).
- **Caching:** agent outputs cached 1h; news sentiment cached per URL.
- **Freshness gate:** repeat views read from DB, zero LLM calls.
- **Fallback:** all-LLM-down still yields a recommendation (deterministic core + templates).
- **Tunable:** if cost runs high, drop selected agents to `deterministic` per-config
  without code changes (the mode is per-agent capable).

## Weight & model configuration
Weights live in `ai/scoring.py` as a named, versioned config (`weights_version`).
Model assignments per role live in config (`model_versions`). Every recommendation
stores both, plus `decision_mode`, so changes are auditable and A/B-able without
rewriting history.
