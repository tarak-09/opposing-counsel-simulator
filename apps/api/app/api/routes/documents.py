from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.core.config import get_settings
from app.db.models import DocumentRole, DocumentType, SourceKind
from app.schemas.document import UploadDocumentResponse
from app.services.ingestion import ingest_document


router = APIRouter()


@router.post("/original", response_model=UploadDocumentResponse)
async def upload_original_document(
    name: str | None = Form(default=None),
    text_content: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    session: Session = Depends(get_db_session),
) -> UploadDocumentResponse:
    return await _ingest_from_request(
        session=session,
        role=DocumentRole.ORIGINAL,
        document_type=DocumentType.CONTRACT,
        name=name,
        text_content=text_content,
        file=file,
    )


@router.post("/revised", response_model=UploadDocumentResponse)
async def upload_revised_document(
    name: str | None = Form(default=None),
    text_content: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    session: Session = Depends(get_db_session),
) -> UploadDocumentResponse:
    return await _ingest_from_request(
        session=session,
        role=DocumentRole.REVISED,
        document_type=DocumentType.CONTRACT,
        name=name,
        text_content=text_content,
        file=file,
    )


@router.post("/evidence", response_model=UploadDocumentResponse)
async def upload_evidence_document(
    evidence_type: DocumentType = Form(default=DocumentType.PLAYBOOK),
    name: str | None = Form(default=None),
    text_content: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    session: Session = Depends(get_db_session),
) -> UploadDocumentResponse:
    return await _ingest_from_request(
        session=session,
        role=DocumentRole.EVIDENCE,
        document_type=evidence_type,
        name=name,
        text_content=text_content,
        file=file,
    )


async def _ingest_from_request(
    *,
    session: Session,
    role: DocumentRole,
    document_type: DocumentType,
    name: str | None,
    text_content: str | None,
    file: UploadFile | None,
) -> UploadDocumentResponse:
    if file is None and not (text_content and text_content.strip()):
        raise HTTPException(status_code=400, detail="Upload a file or provide pasted text.")
    if role == DocumentRole.EVIDENCE and document_type == DocumentType.CONTRACT:
        raise HTTPException(status_code=400, detail="Evidence uploads must use a non-contract evidence type.")

    payload = await file.read() if file is not None else None
    settings = get_settings()
    if payload and len(payload) > settings.upload_max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds the {settings.upload_max_mb} MB upload limit.",
        )
    source_kind = SourceKind.FILE if file is not None else SourceKind.TEXT
    document_name = name or (file.filename if file and file.filename else f"{role.value}-document")

    try:
        document, version, clauses, evidence_sources = ingest_document(
            session,
            name=document_name,
            role=role,
            document_type=document_type,
            source_kind=source_kind,
            filename=file.filename if file else None,
            mime_type=file.content_type if file else None,
            payload=payload,
            text_content=text_content,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return UploadDocumentResponse(
        document=document,
        version=version,
        clauses=clauses,
        evidence_sources=evidence_sources,
    )
