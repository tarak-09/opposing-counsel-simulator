from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin, jsonb_column

if TYPE_CHECKING:
    from .document import ClauseChange, DocumentVersion, EvidenceSource
    from .persona import Persona


class RunStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SimulationDecision(StrEnum):
    ACCEPT = "accept"
    PUSH_BACK = "push_back"
    COUNTER = "counter"
    ESCALATE = "escalate"


class NegotiationRun(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "negotiation_runs"
    __table_args__ = (Index("ix_negotiation_runs_status_stage", "status", "stage"),)

    original_document_version_id: Mapped[object] = mapped_column(
        ForeignKey("document_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    revised_document_version_id: Mapped[object] = mapped_column(
        ForeignKey("document_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    persona_id: Mapped[object] = mapped_column(
        ForeignKey("personas.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, native_enum=False), default=RunStatus.QUEUED, nullable=False
    )
    stage: Mapped[str] = mapped_column(String(120), default="queued", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    input_snapshot: Mapped[dict[str, object]] = mapped_column(jsonb_column, default=dict, nullable=False)
    summary_json: Mapped[dict[str, object]] = mapped_column(jsonb_column, default=dict, nullable=False)
    total_changed_clauses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    original_document_version: Mapped["DocumentVersion"] = relationship(
        "DocumentVersion", foreign_keys=[original_document_version_id]
    )
    revised_document_version: Mapped["DocumentVersion"] = relationship(
        "DocumentVersion", foreign_keys=[revised_document_version_id]
    )
    persona: Mapped["Persona"] = relationship("Persona", back_populates="negotiation_runs")
    clause_changes: Mapped[list["ClauseChange"]] = relationship(
        "ClauseChange", back_populates="negotiation_run", cascade="all, delete-orphan"
    )
    retrieval_hits: Mapped[list["RetrievalHit"]] = relationship(
        "RetrievalHit", back_populates="negotiation_run", cascade="all, delete-orphan"
    )
    simulation_results: Mapped[list["SimulationResult"]] = relationship(
        "SimulationResult", back_populates="negotiation_run", cascade="all, delete-orphan"
    )
    scoring_results: Mapped[list["ScoringResult"]] = relationship(
        "ScoringResult", back_populates="negotiation_run", cascade="all, delete-orphan"
    )


class RetrievalHit(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "retrieval_hits"
    __table_args__ = (Index("ix_retrieval_hits_run_clause_rank", "negotiation_run_id", "clause_change_id", "rank"),)

    negotiation_run_id: Mapped[object] = mapped_column(
        ForeignKey("negotiation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clause_change_id: Mapped[object] = mapped_column(
        ForeignKey("clause_changes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_source_id: Mapped[object] = mapped_column(
        ForeignKey("evidence_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    lexical_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rerank_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    snippet_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(jsonb_column, default=dict, nullable=False)

    negotiation_run: Mapped["NegotiationRun"] = relationship("NegotiationRun", back_populates="retrieval_hits")
    clause_change: Mapped["ClauseChange"] = relationship("ClauseChange", back_populates="retrieval_hits")
    evidence_source: Mapped["EvidenceSource"] = relationship("EvidenceSource", back_populates="retrieval_hits")


class SimulationResult(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "simulation_results"
    __table_args__ = (Index("ix_simulation_results_run_clause", "negotiation_run_id", "clause_change_id"),)

    negotiation_run_id: Mapped[object] = mapped_column(
        ForeignKey("negotiation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clause_change_id: Mapped[object] = mapped_column(
        ForeignKey("clause_changes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    decision: Mapped[SimulationDecision] = mapped_column(
        Enum(SimulationDecision, native_enum=False), nullable=False
    )
    stance_strength: Mapped[int] = mapped_column(Integer, nullable=False)
    business_reason: Mapped[str] = mapped_column(Text, nullable=False)
    legal_reason: Mapped[str] = mapped_column(Text, nullable=False)
    pushback_points: Mapped[list[object]] = mapped_column(jsonb_column, default=list, nullable=False)
    counterproposal_text: Mapped[str] = mapped_column(Text, nullable=False)
    strategy: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    critique_status: Mapped[str] = mapped_column(String(50), default="accepted", nullable=False)
    grounded_evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    raw_model_output: Mapped[dict[str, object]] = mapped_column(jsonb_column, default=dict, nullable=False)

    negotiation_run: Mapped["NegotiationRun"] = relationship("NegotiationRun", back_populates="simulation_results")
    clause_change: Mapped["ClauseChange"] = relationship("ClauseChange", back_populates="simulation_result")


class ScoringResult(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "scoring_results"
    __table_args__ = (Index("ix_scoring_results_run_clause", "negotiation_run_id", "clause_change_id"),)

    negotiation_run_id: Mapped[object] = mapped_column(
        ForeignKey("negotiation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clause_change_id: Mapped[object] = mapped_column(
        ForeignKey("clause_changes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    pushback_probability: Mapped[float] = mapped_column(Float, nullable=False)
    negotiation_friction: Mapped[float] = mapped_column(Float, nullable=False)
    delay_risk: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[float] = mapped_column(Float, nullable=False)
    friction_label: Mapped[str] = mapped_column(String(32), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    heuristic_details: Mapped[dict[str, object]] = mapped_column(jsonb_column, default=dict, nullable=False)

    negotiation_run: Mapped["NegotiationRun"] = relationship("NegotiationRun", back_populates="scoring_results")
    clause_change: Mapped["ClauseChange"] = relationship("ClauseChange", back_populates="scoring_result")
