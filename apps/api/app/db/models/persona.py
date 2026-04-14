from __future__ import annotations

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin, jsonb_column


class Persona(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "personas"
    __table_args__ = (Index("ix_personas_slug", "slug"),)

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    risk_tolerance: Mapped[int] = mapped_column(nullable=False)
    leverage: Mapped[int] = mapped_column(nullable=False)
    speed_priority: Mapped[int] = mapped_column(nullable=False)
    privacy_sensitivity: Mapped[int] = mapped_column(nullable=False)
    liability_strictness: Mapped[int] = mapped_column(nullable=False)
    fallback_flexibility: Mapped[int] = mapped_column(nullable=False)
    tone: Mapped[str] = mapped_column(String(120), nullable=False)
    issue_positions: Mapped[dict[str, object]] = mapped_column(jsonb_column, default=dict, nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    negotiation_runs: Mapped[list["NegotiationRun"]] = relationship(
        "NegotiationRun", back_populates="persona"
    )
