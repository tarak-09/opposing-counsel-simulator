from __future__ import annotations

from pathlib import Path
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.models import Document, DocumentRole, DocumentType, DocumentVersion, NegotiationRun, Persona, RunStatus
from app.db.models import SourceKind
from app.services.ingestion import ingest_document
from app.services.orchestration import build_run_overview, run_negotiation_workflow
from app.services.personas import sync_builtin_personas
from app.tasks.negotiation import run_workflow_task


def bootstrap_demo_happy_path(
    session: Session,
    *,
    persona_slug: str = "big-tech-legal",
    run_async: bool = False,
) -> tuple[
    NegotiationRun,
    Persona,
    DocumentVersion,
    DocumentVersion,
    list[DocumentVersion],
    Literal["async", "sync"],
]:
    settings = get_settings()
    sync_builtin_personas(session)

    _, original_version = _ensure_sample_document(
        session,
        name="Sample Original MSA",
        role=DocumentRole.ORIGINAL,
        document_type=DocumentType.CONTRACT,
        path=settings.sample_data_root / "contracts" / "original_msa.txt",
    )
    _, revised_version = _ensure_sample_document(
        session,
        name="Sample Revised MSA",
        role=DocumentRole.REVISED,
        document_type=DocumentType.CONTRACT,
        path=settings.sample_data_root / "contracts" / "revised_msa.txt",
    )
    evidence_versions = [
        _ensure_sample_document(
            session,
            name="Customer Playbook",
            role=DocumentRole.EVIDENCE,
            document_type=DocumentType.PLAYBOOK,
            path=settings.sample_data_root / "evidence" / "customer_playbook.txt",
        )[1],
        _ensure_sample_document(
            session,
            name="Vendor Precedent",
            role=DocumentRole.EVIDENCE,
            document_type=DocumentType.PRECEDENT,
            path=settings.sample_data_root / "evidence" / "vendor_precedent.txt",
        )[1],
        _ensure_sample_document(
            session,
            name="Fallback Clauses",
            role=DocumentRole.EVIDENCE,
            document_type=DocumentType.FALLBACK,
            path=settings.sample_data_root / "evidence" / "fallback_clauses.txt",
        )[1],
    ]

    persona = session.scalar(select(Persona).where(Persona.slug == persona_slug))
    if persona is None:
        persona = session.scalar(select(Persona).order_by(Persona.name.asc()))
    if persona is None:
        raise ValueError("No personas are available for the demo happy path.")

    run = NegotiationRun(
        original_document_version_id=original_version.id,
        revised_document_version_id=revised_version.id,
        persona_id=persona.id,
        status=RunStatus.QUEUED,
        stage="queued",
        input_snapshot={
            "demo_happy_path": True,
            "evidence_document_version_ids": [str(version.id) for version in evidence_versions],
        },
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    task_mode: Literal["async", "sync"] = "async"
    if run_async and not settings.celery_task_always_eager:
        run_workflow_task.delay(str(run.id))
    else:
        task_mode = "sync"
        run = run_negotiation_workflow(session, run.id)
        run.summary_json = run.summary_json or build_run_overview(run)
        session.commit()
        session.refresh(run)

    return run, persona, original_version, revised_version, evidence_versions, task_mode


def _ensure_sample_document(
    session: Session,
    *,
    name: str,
    role: DocumentRole,
    document_type: DocumentType,
    path: Path,
) -> tuple[Document, DocumentVersion]:
    existing = session.scalar(
        select(Document)
        .where(Document.name == name)
        .options(selectinload(Document.versions))
    )
    if existing is not None and existing.versions:
        version = sorted(existing.versions, key=lambda item: item.version_number, reverse=True)[0]
        return existing, version

    document, version, _, _ = ingest_document(
        session,
        name=name,
        role=role,
        document_type=document_type,
        source_kind=SourceKind.TEXT,
        text_content=path.read_text(encoding="utf-8"),
    )
    return document, version
