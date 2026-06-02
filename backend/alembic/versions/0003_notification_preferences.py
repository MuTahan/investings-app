"""notification preferences + log category

Revision ID: 0003_notif_prefs
Revises: 0002_valuation
Create Date: 2026-06-02
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_notif_prefs"
down_revision: str | None = "0002_valuation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "notification_log",
        sa.Column("category", sa.String(20), nullable=False, server_default="rating_change"),
    )
    op.create_table(
        "notification_preferences",
        sa.Column("user_id", sa.Uuid(), primary_key=True),
        sa.Column("categories", sa.JSON(), nullable=True),
        sa.Column("min_priority", sa.String(10), nullable=False, server_default="high"),
        sa.Column("max_risk", sa.String(10), nullable=False, server_default="high"),
        sa.Column("sectors", sa.JSON(), nullable=True),
        sa.Column("quiet_hours_start", sa.Integer(), nullable=True),
        sa.Column("quiet_hours_end", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE",
            name="fk_notification_preferences_user_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("notification_preferences")
    op.drop_column("notification_log", "category")
