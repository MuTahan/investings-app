"""add valuation column to recommendations

Revision ID: 0002_valuation
Revises: 0001_initial
Create Date: 2026-06-02
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_valuation"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("recommendations", sa.Column("valuation", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("recommendations", "valuation")
