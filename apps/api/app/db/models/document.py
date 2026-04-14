from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin, jsonb_column

if TYPE_CHECKING:
    from .run import NegotiationRun, RetrievalHit, ScoringResult, SimulationResult


class DocumentRole(StrEnum):
    ORIGINAL = "original"
    REVISED = "revised"
    EVIDENCE = "evidence"


class DocumentType(StrEnum):
    CONTRACT = "contract"
    PLAYBOOK = "playbook"
    PRECEDENT = "precedent"
    FALLBACK = "fallback"
    BENCHMARK = "benchmark"


class SourceKind(StrEnum):
    FILE = "file"
    TEXT = "text"


class ParserStatus(StrEnum):
    PENDING = "pending"
    PARSED = "parsed"
    FAILED = "failed"


class ClauseChangeType(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


class ChangeDirection(StrEnum):
    VENDOR_FAVORABLE = "vendor_favorable"
    CUSTOMER_FAVORABLE = "customer_favorable"
    MUTUAL_OR_NEUTRAL = "mutual_or_neutral"
    UNKNOWN = "unknown"


class IssueType(StrEnum):
    LIMITATION_OF_LIABILITY = "limitation_of_liability"
    INDEMNITY = "indemnity"
    CONFIDENTIALITY = "confidentiality"
    IP_OWNERSHIP = "ip_ownership"
    PAYMENT_TERMS = "payment_terms"
    WARRANTIES = "warranties"
    TERMINATION = "termination"
    DATA_PROTECTION = "data_protection"
    SECURITY = "security"
    GOVERNING_LAW = "governing_law"
    SERVICE_LEVELS = "service_levels"
    AUDIT_RIGHTS = "audit_rights"
    GENERAL = "general"


class Document(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[DocumentRole] = mapped_column(Enum(DocumentRole, native_enum=False), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, native_enum=False), nullable=False
    )
    source_kind: Mapped[SourceKind] = mapped_column(
        Enum(SourceKind, native_enum=False), nullable=False, default=SourceKind.FILE
    )
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(jsonb_column, default=dict, nullable=False)

    versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentVersion(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "document_versions"
    __table_args__ = (Index("ix_document_versions_document_id_version_number", "document_id", "version_number"),)

    document_id: Mapped[object] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    filename: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(255))
    storage_path: Mapped[str | None] = mapped_column(String(500))
    checksum: Mapped[str | None] = mapped_column(String(64))
    raw_text_input: Mapped[str | None] = mapped_column(Text)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    section_map: Mapped[list[dict[str, object]]] = mapped_column(jsonb_column, default=list, nullable=False)
    parser_status: Mapped[ParserStatus] = mapped_column(
        Enum(ParserStatus, native_enum=False), default=ParserStatus.PARSED, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    document: Mapped["Document"] = relationship("Document", back_populates="versions")
    clauses: Mapped[list["Clause"]] = relationship(
        "Clause", back_populates="document_version", cascade="all, delete-orphan"
    )
    evidence_sources: Mapped[list["EvidenceSource"]] = relationship(
        "EvidenceSource", back_populates="document_version", cascade="all, delete-orphan"
    )


class Clause(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "clauses"
    __table_args__ = (
        Index("ix_clauses_document_version_id_order_index", "document_version_id", "order_index"),
        Index("ix_clauses_document_version_id_stable_clause_id", "document_version_id", "stable_clause_id"),
    )

    document_version_id: Mapped[object] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stable_clause_id: Mapped[str] = mapped_column(String(120), nullable=False)
    heading: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    heading_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    clause_number: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_span: Mapped[dict[str, object]] = mapped_column(jsonb_column, default=dict, nullable=False)

    document_version: Mapped["DocumentVersion"] = relationship("DocumentVersion", back_populates="clauses")
    original_changes: Mapped[list["ClauseChange"]] = relationship(
        "ClauseChange", foreign_keys="ClauseChange.original_clause_id", back_populates="original_clause"
    )
    revised_changes: Mapped[list["ClauseChange"]] = relationship(
        "ClauseChange", foreign_keys="ClauseChange.revised_clause_id", back_populates="revised_clause"
    )


class ClauseChange(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "clause_changes"
    __table_args__ = (
        Index("ix_clause_changes_run_id_clause_key", "negotiation_run_id", "clause_key"),
        Index("ix_clause_changes_run_id_issue_type", "negotiation_run_id", "issue_type"),
    )

    negotiation_run_id: Mapped[object] = mapped_column(
        ForeignKey("negotiation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_clause_id: Mapped[object | None] = mapped_column(ForeignKey("clauses.id", ondelete="SET NULL"))
    revised_clause_id: Mapped[object | None] = mapped_column(ForeignKey("clauses.id", ondelete="SET NULL"))
    clause_key: Mapped[str] = mapped_column(String(120), nullable=False)
    change_type: Mapped[ClauseChangeType] = mapped_column(
        Enum(ClauseChangeType, native_enum=False), nullable=False
    )
    issue_type: Mapped[IssueType] = mapped_column(
        Enum(IssueType, native_enum=False), default=IssueType.GENERAL, nullable=False
    )
    change_direction: Mapped[ChangeDirection] = mapped_column(
        Enum(ChangeDirection, native_enum=False), default=ChangeDirection.UNKNOWN, nullable=False
    )
    semantic_summary: Mapped[str] = mapped_column(Text, nullable=False)
    diff_details: Mapped[dict[str, object]] = mapped_column(jsonb_column, default=dict, nullable=False)
    changed_tokens_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)

    negotiation_run: Mapped["NegotiationRun"] = relationship("NegotiationRun", back_populates="clause_changes")
    original_clause: Mapped["Clause | None"] = relationship(
        "Clause", foreign_keys=[original_clause_id], back_populates="original_changes"
    )
    revised_clause: Mapped["Clause | None"] = relationship(
        "Clause", foreign_keys=[revised_clause_id], back_populates="revised_changes"
    )
    retrieval_hits: Mapped[list["RetrievalHit"]] = relationship(
        "RetrievalHit", back_populates="clause_change", cascade="all, delete-orphan"
    )
    simulation_result: Mapped["SimulationResult | None"] = relationship(
        "SimulationResult", back_populates="clause_change", uselist=False, cascade="all, delete-orphan"
    )
    scoring_result: Mapped["ScoringResult | None"] = relationship(
        "ScoringResult", back_populates="clause_change", uselist=False, cascade="all, delete-orphan"
    )


class EvidenceSource(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "evidence_sources"
    __table_args__ = (Index("ix_evidence_sources_document_version_id_title", "document_version_id", "title"),)

    document_version_id: Mapped[object] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, native_enum=False), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    section_label: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    snippet_text: Mapped[str] = mapped_column(Text, nullable=False)
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(jsonb_column, default=dict, nullable=False)
    vector_id: Mapped[str | None] = mapped_column(String(120))

    document_version: Mapped["DocumentVersion"] = relationship(
        "DocumentVersion", back_populates="evidence_sources"
    )
    retrieval_hits: Mapped[list["RetrievalHit"]] = relationship(
        "RetrievalHit", back_populates="evidence_source"
    )
