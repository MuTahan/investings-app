# 04 — Database Schema (PostgreSQL)

Schema for the MVP. Managed with **SQLAlchemy 2.0 (async)** models and **Alembic**
migrations. Conventions: `snake_case`, UUID v4 primary keys, `created_at` /
`updated_at` timestamptz on every table, soft references via FKs with `ON DELETE`
rules noted.

---

## Entity overview

```
users ──┬──< watchlists ──< watchlist_items >── instruments
        ├──< portfolios ──< holdings >──────────┘
        ├──< recommendations >── instruments
        │        └──< agent_outputs
        ├──< devices
        └──  user_risk_profiles (1:1)

instruments ──< news_items
```

---

## Tables

### `users`
| Column            | Type          | Notes                                  |
|-------------------|---------------|----------------------------------------|
| id                | uuid PK       |                                        |
| email             | citext UNIQUE | nullable (Apple-only users may omit)   |
| password_hash     | text          | nullable (null for Apple-only)         |
| apple_sub         | text UNIQUE   | nullable; Apple subject identifier     |
| display_name      | text          | nullable                               |
| is_active         | bool          | default true                           |
| created_at        | timestamptz   | default now()                          |
| updated_at        | timestamptz   |                                        |

Constraint: at least one of (`password_hash`, `apple_sub`) must be non-null.

### `user_risk_profiles` (1:1 with users)
| Column             | Type        | Notes                                                  |
|--------------------|-------------|--------------------------------------------------------|
| user_id            | uuid PK FK  | → users.id ON DELETE CASCADE                           |
| risk_tolerance     | text        | enum: `conservative|moderate|aggressive`              |
| time_horizon       | text        | enum: `short|medium|long`                             |
| objectives         | jsonb       | e.g. ["growth","income"]                              |
| max_position_pct   | numeric(5,2)| optional concentration preference                      |
| updated_at         | timestamptz |                                                        |

Drives the **Portfolio-Fit** and **Risk** agents' personalization.

### `instruments`
Reference data for tradable symbols (stocks + ETFs).
| Column        | Type        | Notes                                  |
|---------------|-------------|----------------------------------------|
| id            | uuid PK     |                                        |
| symbol        | text UNIQUE | e.g. AAPL, SPY                         |
| name          | text        |                                        |
| type          | text        | enum: `stock|etf`                     |
| exchange      | text        | e.g. NASDAQ                            |
| sector        | text        | nullable                               |
| currency      | text        | default 'USD'                          |
| is_active     | bool        | default true                           |
| created_at    | timestamptz |                                        |

> Quotes/candles are **not** stored as tables — they're fetched live and cached.
> Only durable reference data and derived AI outputs are persisted.

### `watchlists`
| Column     | Type        | Notes                               |
|------------|-------------|-------------------------------------|
| id         | uuid PK     |                                     |
| user_id    | uuid FK     | → users.id ON DELETE CASCADE        |
| name       | text        | default 'My Watchlist'              |
| created_at | timestamptz |                                     |

### `watchlist_items`
| Column        | Type      | Notes                                         |
|---------------|-----------|-----------------------------------------------|
| id            | uuid PK   |                                               |
| watchlist_id  | uuid FK   | → watchlists.id ON DELETE CASCADE             |
| instrument_id | uuid FK   | → instruments.id ON DELETE CASCADE            |
| added_at      | timestamptz |                                             |

Unique: (`watchlist_id`, `instrument_id`).

### `portfolios`
| Column     | Type        | Notes                               |
|------------|-------------|-------------------------------------|
| id         | uuid PK     |                                     |
| user_id    | uuid FK     | → users.id ON DELETE CASCADE        |
| name       | text        | default 'My Portfolio'              |
| created_at | timestamptz |                                     |

### `holdings`
| Column        | Type          | Notes                                       |
|---------------|---------------|---------------------------------------------|
| id            | uuid PK       |                                             |
| portfolio_id  | uuid FK       | → portfolios.id ON DELETE CASCADE           |
| instrument_id | uuid FK       | → instruments.id ON DELETE RESTRICT         |
| quantity      | numeric(18,6) |                                             |
| avg_cost      | numeric(18,4) | per-share cost basis                        |
| created_at    | timestamptz   |                                             |
| updated_at    | timestamptz   |                                             |

Unique: (`portfolio_id`, `instrument_id`). Used by Risk + Portfolio-Fit agents for
concentration, sector exposure, and diversification.

### `recommendations`
One row per committee evaluation (history is kept for trend + audit).
| Column           | Type          | Notes                                                  |
|------------------|---------------|--------------------------------------------------------|
| id               | uuid PK       |                                                        |
| user_id          | uuid FK       | → users.id ON DELETE CASCADE (personalized per user)   |
| instrument_id    | uuid FK       | → instruments.id ON DELETE CASCADE                     |
| rating           | text          | final rating: `STRONG_BUY|BUY|HOLD|WATCH|AVOID`       |
| anchor_rating    | text          | deterministic anchor rating (audit; Chair within ±1)   |
| confidence       | numeric(5,2)  | 0..100                                                 |
| composite_score  | numeric(5,2)  | 0..100 deterministic weighted score                    |
| time_horizon     | text          | enum: `short|medium|long`                             |
| reasons          | jsonb         | list of {label, detail}                                |
| risks            | jsonb         | list of {label, detail, severity}                      |
| suggested_action | text          | human-readable                                         |
| personalization  | jsonb         | fit reasoning relative to user profile/holdings        |
| chair_rationale  | text          | Chair's justification (esp. for any deviation from anchor) |
| notif_priority   | text          | enum: `low|normal|high|critical`                      |
| decision_mode    | text          | enum: `deterministic|chair_assisted|empowered`        |
| weights_version  | text          | which weight config produced this (audit)              |
| model_versions   | jsonb         | model used per role (agents/chair) for audit           |
| generated_at     | timestamptz   | default now()                                          |

Index: (`user_id`, `instrument_id`, `generated_at desc`) — powers freshness gate and
"latest per symbol".

### `agent_outputs`
Per-agent contribution to a recommendation (full explainability + audit).
| Column           | Type          | Notes                                                  |
|------------------|---------------|--------------------------------------------------------|
| id               | uuid PK       |                                                        |
| recommendation_id| uuid FK       | → recommendations.id ON DELETE CASCADE                 |
| agent            | text          | enum: `news|technical|fundamental|macro|risk|portfolio_fit` |
| base_score       | numeric(5,2)  | deterministic anchor score 0..100 (nullable for risk)  |
| score            | numeric(5,2)  | final score after bounded ±10 LLM adjustment           |
| adjustment_delta | numeric(5,2)  | score - base_score (audit; 0 in deterministic mode)    |
| confidence       | numeric(5,2)  | 0..100                                                  |
| signal           | text          | nullable: e.g. `bullish|neutral|bearish`              |
| payload          | jsonb         | agent-specific structured evidence (indicators, signals) |
| explanation      | text          | LLM reasoning or templated narration                   |
| adjustment_justification | text  | nullable; why the LLM moved off the anchor             |
| created_at       | timestamptz   |                                                        |

Index: (`recommendation_id`, `agent`).

### `news_items`
Cached/ingested news used by the News & Sentiment agent (also surfaced in the app).
| Column        | Type        | Notes                                          |
|---------------|-------------|------------------------------------------------|
| id            | uuid PK     |                                                |
| instrument_id | uuid FK     | → instruments.id ON DELETE CASCADE (nullable for macro) |
| headline      | text        |                                                |
| summary       | text        | nullable                                       |
| url           | text        |                                                |
| source        | text        |                                                |
| published_at  | timestamptz |                                                |
| sentiment     | numeric(5,2)| nullable; -100..100 if scored                  |
| category      | text        | enum: `company|macro|analyst`                 |
| created_at    | timestamptz |                                                |

Unique: (`url`) to dedupe. Index: (`instrument_id`, `published_at desc`).

### `devices`
APNS device registrations.
| Column        | Type        | Notes                                   |
|---------------|-------------|-----------------------------------------|
| id            | uuid PK     |                                         |
| user_id       | uuid FK     | → users.id ON DELETE CASCADE            |
| device_token  | text        |                                         |
| platform      | text        | enum: `ios`                            |
| is_valid      | bool        | default true (pruned on APNS rejection) |
| created_at    | timestamptz |                                         |
| last_seen_at  | timestamptz |                                         |

Unique: (`user_id`, `device_token`).

### `notification_log` (optional, MVP-light)
| Column           | Type        | Notes                                  |
|------------------|-------------|----------------------------------------|
| id               | uuid PK     |                                        |
| user_id          | uuid FK     | → users.id ON DELETE CASCADE           |
| recommendation_id| uuid FK     | → recommendations.id ON DELETE SET NULL|
| sent_at          | timestamptz |                                        |
| status           | text        | enum: `sent|failed`                   |

Used to enforce per-run notification caps and quiet hours, and for debugging.

---

## Enum strategy
Enums are stored as `text` with `CHECK` constraints (or Postgres native enums) and
mirrored as Python `str` Enums in `app/domain/enums.py`. Text+CHECK is chosen for the
MVP so adding a value doesn't require an `ALTER TYPE` migration dance.

## Migrations
- `alembic revision --autogenerate` per schema change; reviewed by hand.
- Initial migration creates all tables above + indexes + a seed of common
  instruments (S&P 100 + top ETFs) for the demo.

## What is intentionally NOT stored
- Live quotes / OHLC candles (fetched + cached, not a table).
- Raw provider payloads (only derived `agent_outputs.payload` is kept).
- Brokerage/account/money data (out of scope — informational product).
