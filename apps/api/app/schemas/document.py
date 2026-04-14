from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.schemas.common import APIModel, TimestampedRead


class ClauseRead(TimestampedRead):
    document_version_id: UUID
    stable_clause_id: str
    heading: str
    heading_path: str
    clause_number: str
    order_index: int
    text: str
    normalized_text: str
    source_span: dict[str, object]


class DocumentRead(TimestampedRead):
    name: str
    role: str
    document_type: str
    source_kind: str
    status: str
    metadata_json: dict[str, object]


class DocumentVersionRead(TimestampedRead):
    document_id: UUID
    version_number: int
    filename: str | None = None
    mime_type: str | None = None
    storage_path: str | None = None
    checksum: str | None = None
    extracted_text: str
    normalized_text: str
    section_map: list[dict[str, object]]
    parser_status: str
    is_active: bool


class EvidenceSourceRead(TimestampedRead):
    document_version_id: UUID
    evidence_type: str
    title: str
    section_label: str
    snippet_text: str
    full_text: str
    token_count: int
    metadata_json: dict[str, object]
    vector_id: str | None = None


class UploadDocumentResponse(APIModel):
    document: DocumentRead
    version: DocumentVersionRead
    clauses: list[ClauseRead] = Field(default_factory=list)
    evidence_sources: list[EvidenceSourceRead] = Field(default_factory=list)
