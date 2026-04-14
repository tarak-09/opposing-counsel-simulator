from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Clause, Document, DocumentRole, DocumentType, DocumentVersion, EvidenceSource, SourceKind
from app.services.extraction import extract_text_from_bytes, normalize_document_text
from app.services.parsing import parse_contract_text
from app.services.retrieval import index_evidence_sources
from app.services.storage import write_upload
from app.utils.text import checksum_bytes, token_count


def ingest_document(
    session: Session,
    *,
    name: str,
    role: DocumentRole,
    document_type: DocumentType,
    source_kind: SourceKind,
    filename: str | None = None,
    mime_type: str | None = None,
    payload: bytes | None = None,
    text_content: str | None = None,
    metadata: dict[str, object] | None = None,
) -> tuple[Document, DocumentVersion, list[Clause], list[EvidenceSource]]:
    if not payload and not (text_content and text_content.strip()):
        raise ValueError("Either a file upload or text content is required.")

    document = Document(
        name=name,
        role=role,
        document_type=document_type,
        source_kind=source_kind,
        metadata_json=metadata or {},
    )
    session.add(document)
    session.flush()

    extracted_text = (
        normalize_document_text(extract_text_from_bytes(filename or "document.txt", payload or b"", mime_type))
        if payload
        else normalize_document_text(text_content or "")
    )
    if not extracted_text.strip():
        raise ValueError("Uploaded document contained no readable text.")
    parsed = parse_contract_text(extracted_text)

    version = DocumentVersion(
        document_id=document.id,
        version_number=1,
        filename=filename,
        mime_type=mime_type,
        checksum=checksum_bytes(payload) if payload else None,
        raw_text_input=text_content,
        extracted_text=extracted_text,
        normalized_text=parsed.normalized_text,
        section_map=parsed.section_map,
    )
    session.add(version)
    session.flush()

    if payload and filename:
        version.storage_path = write_upload(document.id, version.id, filename, payload)

    clauses = [
        Clause(
            document_version_id=version.id,
            stable_clause_id=clause.stable_clause_id,
            heading=clause.heading,
            heading_path=clause.heading_path,
            clause_number=clause.clause_number,
            order_index=clause.order_index,
            text=clause.text,
            normalized_text=clause.normalized_text,
            source_span=clause.source_span,
        )
        for clause in parsed.clauses
    ]
    session.add_all(clauses)

    evidence_sources: list[EvidenceSource] = []
    if role == DocumentRole.EVIDENCE:
        evidence_sources = [
            EvidenceSource(
                document_version_id=version.id,
                evidence_type=document_type,
                title=document.name,
                section_label=clause.heading,
                snippet_text=clause.text[:600],
                full_text=clause.text,
                token_count=token_count(clause.text),
                metadata_json={
                    "clause_number": clause.clause_number,
                    "stable_clause_id": clause.stable_clause_id,
                    "heading_path": clause.heading_path,
                },
            )
            for clause in clauses
        ]
        session.add_all(evidence_sources)

    session.commit()

    for entity in [document, version, *clauses, *evidence_sources]:
        session.refresh(entity)

    if evidence_sources:
        index_evidence_sources(evidence_sources)
        session.commit()

    return document, version, clauses, evidence_sources
