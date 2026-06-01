from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow, uuid_pk


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        Index("ix_reco_user_instrument_time", "user_id", "instrument_id", "generated_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[str] = mapped_column(String(12), nullable=False)
    anchor_rating: Mapped[str] = mapped_column(String(12), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    composite_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    time_horizon: Mapped[str] = mapped_column(String(10), nullable=False)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    risks: Mapped[list] = mapped_column(JSON, default=list)
    suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    personalization: Mapped[dict] = mapped_column(JSON, default=dict)
    chair_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    notif_priority: Mapped[str] = mapped_column(String(10), default="normal", nullable=False)
    decision_mode: Mapped[str] = mapped_column(String(20), default="empowered", nullable=False)
    weights_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)
    model_versions: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    agent_outputs: Mapped[list[AgentOutput]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan"
    )


class AgentOutput(Base):
    __tablename__ = "agent_outputs"
    __table_args__ = (Index("ix_agent_output_reco_agent", "recommendation_id", "agent"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False
    )
    agent: Mapped[str] = mapped_column(String(20), nullable=False)
    base_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    adjustment_delta: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    signal: Mapped[str | None] = mapped_column(String(10), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    adjustment_justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    recommendation: Mapped[Recommendation] = relationship(back_populates="agent_outputs")
