from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.db.models import Document, DocumentRole, DocumentType, SourceKind
from app.db.models.base import Base
from app.db.session import SessionLocal, engine
from app.services.ingestion import ingest_document
from app.services.personas import sync_builtin_personas


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        sync_builtin_personas(session)
        sample_root = Path(__file__).resolve().parents[4] / "packages" / "sample-data"
        _seed_contract(
            session,
            name="Sample Original MSA",
            role=DocumentRole.ORIGINAL,
            path=sample_root / "contracts" / "original_msa.txt",
        )
        _seed_contract(
            session,
            name="Sample Revised MSA",
            role=DocumentRole.REVISED,
            path=sample_root / "contracts" / "revised_msa.txt",
        )
        _seed_evidence(
            session,
            name="Customer Playbook",
            document_type=DocumentType.PLAYBOOK,
            path=sample_root / "evidence" / "customer_playbook.txt",
        )
        _seed_evidence(
            session,
            name="Vendor Precedent",
            document_type=DocumentType.PRECEDENT,
            path=sample_root / "evidence" / "vendor_precedent.txt",
        )
        _seed_evidence(
            session,
            name="Fallback Clauses",
            document_type=DocumentType.FALLBACK,
            path=sample_root / "evidence" / "fallback_clauses.txt",
        )


def _seed_contract(session, *, name: str, role: DocumentRole, path: Path) -> None:
    existing = session.scalar(select(Document).where(Document.name == name))
    if existing is not None:
        return
    ingest_document(
        session,
        name=name,
        role=role,
        document_type=DocumentType.CONTRACT,
        source_kind=SourceKind.TEXT,
        text_content=path.read_text(encoding="utf-8"),
    )


def _seed_evidence(session, *, name: str, document_type: DocumentType, path: Path) -> None:
    existing = session.scalar(select(Document).where(Document.name == name))
    if existing is not None:
        return
    ingest_document(
        session,
        name=name,
        role=DocumentRole.EVIDENCE,
        document_type=document_type,
        source_kind=SourceKind.TEXT,
        text_content=path.read_text(encoding="utf-8"),
    )


if __name__ == "__main__":
    main()
