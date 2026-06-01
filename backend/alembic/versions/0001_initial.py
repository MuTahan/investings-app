"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "instruments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("exchange", sa.String(40), nullable=True),
        sa.Column("sector", sa.String(80), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("symbol", name="uq_instruments_symbol"),
    )
    op.create_index("ix_instruments_symbol", "instruments", ["symbol"])

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("apple_sub", sa.String(), nullable=True),
        sa.Column("display_name", sa.String(120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("apple_sub", name="uq_users_apple_sub"),
        sa.CheckConstraint(
            "password_hash IS NOT NULL OR apple_sub IS NOT NULL",
            name="ck_users_auth_method_present",
        ),
    )

    op.create_table(
        "user_risk_profiles",
        sa.Column("user_id", sa.Uuid(), primary_key=True),
        sa.Column("risk_tolerance", sa.String(20), nullable=False),
        sa.Column("time_horizon", sa.String(10), nullable=False),
        sa.Column("objectives", sa.JSON(), nullable=True),
        sa.Column("max_position_pct", sa.Numeric(5, 2), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_user_risk_profiles_user_id"
        ),
    )

    op.create_table(
        "watchlists",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_watchlists_user_id"
        ),
    )
    op.create_index("ix_watchlists_user_id", "watchlists", ["user_id"])

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("watchlist_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["watchlist_id"], ["watchlists.id"], ondelete="CASCADE",
            name="fk_watchlist_items_watchlist_id",
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instruments.id"], ondelete="CASCADE",
            name="fk_watchlist_items_instrument_id",
        ),
        sa.UniqueConstraint("watchlist_id", "instrument_id", name="uq_watchlist_items_pair"),
    )
    op.create_index("ix_watchlist_items_watchlist_id", "watchlist_items", ["watchlist_id"])

    op.create_table(
        "portfolios",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_portfolios_user_id"
        ),
    )
    op.create_index("ix_portfolios_user_id", "portfolios", ["user_id"])

    op.create_table(
        "holdings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("avg_cost", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["portfolio_id"], ["portfolios.id"], ondelete="CASCADE",
            name="fk_holdings_portfolio_id",
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instruments.id"], ondelete="RESTRICT",
            name="fk_holdings_instrument_id",
        ),
        sa.UniqueConstraint("portfolio_id", "instrument_id", name="uq_holdings_pair"),
    )
    op.create_index("ix_holdings_portfolio_id", "holdings", ["portfolio_id"])

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.String(12), nullable=False),
        sa.Column("anchor_rating", sa.String(12), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=False),
        sa.Column("composite_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("time_horizon", sa.String(10), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=True),
        sa.Column("risks", sa.JSON(), nullable=True),
        sa.Column("suggested_action", sa.Text(), nullable=True),
        sa.Column("personalization", sa.JSON(), nullable=True),
        sa.Column("chair_rationale", sa.Text(), nullable=True),
        sa.Column("notif_priority", sa.String(10), nullable=False),
        sa.Column("decision_mode", sa.String(20), nullable=False),
        sa.Column("weights_version", sa.String(20), nullable=False),
        sa.Column("model_versions", sa.JSON(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_recommendations_user_id"
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instruments.id"], ondelete="CASCADE",
            name="fk_recommendations_instrument_id",
        ),
    )
    op.create_index(
        "ix_reco_user_instrument_time",
        "recommendations",
        ["user_id", "instrument_id", "generated_at"],
    )

    op.create_table(
        "agent_outputs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("recommendation_id", sa.Uuid(), nullable=False),
        sa.Column("agent", sa.String(20), nullable=False),
        sa.Column("base_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("adjustment_delta", sa.Numeric(5, 2), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=False),
        sa.Column("signal", sa.String(10), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("adjustment_justification", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["recommendation_id"], ["recommendations.id"], ondelete="CASCADE",
            name="fk_agent_outputs_recommendation_id",
        ),
    )
    op.create_index(
        "ix_agent_output_reco_agent", "agent_outputs", ["recommendation_id", "agent"]
    )

    op.create_table(
        "news_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("instrument_id", sa.Uuid(), nullable=True),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("source", sa.String(120), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sentiment", sa.Numeric(5, 2), nullable=True),
        sa.Column("category", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instruments.id"], ondelete="CASCADE",
            name="fk_news_items_instrument_id",
        ),
        sa.UniqueConstraint("url", name="uq_news_items_url"),
    )
    op.create_index(
        "ix_news_instrument_published", "news_items", ["instrument_id", "published_at"]
    )

    op.create_table(
        "devices",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("device_token", sa.String(400), nullable=False),
        sa.Column("platform", sa.String(10), nullable=False),
        sa.Column("is_valid", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_devices_user_id"
        ),
        sa.UniqueConstraint("user_id", "device_token", name="uq_devices_pair"),
    )
    op.create_index("ix_devices_user_id", "devices", ["user_id"])

    op.create_table(
        "notification_log",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("recommendation_id", sa.Uuid(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(10), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_notification_log_user_id"
        ),
        sa.ForeignKeyConstraint(
            ["recommendation_id"], ["recommendations.id"], ondelete="SET NULL",
            name="fk_notification_log_recommendation_id",
        ),
    )
    op.create_index("ix_notification_log_user_id", "notification_log", ["user_id"])


def downgrade() -> None:
    for table in (
        "notification_log",
        "devices",
        "news_items",
        "agent_outputs",
        "recommendations",
        "holdings",
        "portfolios",
        "watchlist_items",
        "watchlists",
        "user_risk_profiles",
        "users",
        "instruments",
    ):
        op.drop_table(table)
