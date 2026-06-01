from __future__ import annotations

import uuid

from sqlalchemy import JSON, Boolean, CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "password_hash IS NOT NULL OR apple_sub IS NOT NULL",
            name="auth_method_present",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    apple_sub: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    risk_profile: Mapped[UserRiskProfile | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserRiskProfile(Base):
    __tablename__ = "user_risk_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    risk_tolerance: Mapped[str] = mapped_column(String(20), default="moderate", nullable=False)
    time_horizon: Mapped[str] = mapped_column(String(10), default="long", nullable=False)
    objectives: Mapped[list] = mapped_column(JSON, default=list)
    max_position_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    user: Mapped[User] = relationship(back_populates="risk_profile")
