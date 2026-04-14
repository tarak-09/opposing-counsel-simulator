from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db_session
from app.core.config import get_settings
from app.db.models import ClauseChange, DocumentRole, DocumentVersion, NegotiationRun, Persona, RetrievalHit
from app.db.models import RunStatus
from app.schemas.run import ClauseResultsResponse, ClauseReviewResult, CreateRunRequest
from app.schemas.run import EvidenceForClauseResponse, RunAcceptedResponse, RunStatusResponse, RunSummaryResponse
from app.services.orchestration import build_run_overview, run_negotiation_workflow
from app.tasks.negotiation import run_workflow_task


router = APIRouter()


@router.post("", response_model=RunAcceptedResponse)
def create_run(
    payload: CreateRunRequest,
    session: Session = Depends(get_db_session),
) -> RunAcceptedResponse:
    original = session.get(DocumentVersion, payload.original_document_version_id)
    revised = session.get(DocumentVersion, payload.revised_document_version_id)
    persona = session.get(Persona, payload.persona_id)
    if original is None or revised is None or persona is None:
        raise HTTPException(status_code=404, detail="One or more run inputs could not be found.")
    if original.document.role != DocumentRole.ORIGINAL or revised.document.role != DocumentRole.REVISED:
        raise HTTPException(
            status_code=400,
            detail="Run inputs must use an uploaded original contract version and a revised contract version.",
        )
    evidence_version_ids = list(dict.fromkeys(payload.evidence_document_version_ids))
    validated_evidence_ids: list[str] = []
    if evidence_version_ids:
        evidence_versions = list(
            session.scalars(
                select(DocumentVersion)
                .where(DocumentVersion.id.in_(evidence_version_ids))
                .options(selectinload(DocumentVersion.document))
            )
        )
        if len(evidence_versions) != len(evidence_version_ids):
            raise HTTPException(status_code=404, detail="One or more evidence document versions could not be found.")
        invalid_evidence = [item for item in evidence_versions if item.document.role != DocumentRole.EVIDENCE]
        if invalid_evidence:
            raise HTTPException(status_code=400, detail="Evidence inputs must come from evidence documents.")
        validated_evidence_ids = [str(item.id) for item in evidence_versions]

    run = NegotiationRun(
        original_document_version_id=original.id,
        revised_document_version_id=revised.id,
        persona_id=persona.id,
        status=RunStatus.QUEUED,
        stage="queued",
        input_snapshot={
            "evidence_document_version_ids": validated_evidence_ids,
        },
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    settings = get_settings()
    task_mode = "async"
    if payload.run_async and not settings.celery_task_always_eager:
        run_workflow_task.delay(str(run.id))
    else:
        task_mode = "sync"
        run = run_negotiation_workflow(session, run.id)

    return RunAcceptedResponse(run=run, task_mode=task_mode)


@router.get("/{run_id}/status", response_model=RunStatusResponse)
def get_run_status(run_id: UUID, session: Session = Depends(get_db_session)) -> RunStatusResponse:
    run = _get_run_or_404(session, run_id)
    return RunStatusResponse(run=run)


@router.get("/{run_id}/summary", response_model=RunSummaryResponse)
def get_run_summary(run_id: UUID, session: Session = Depends(get_db_session)) -> RunSummaryResponse:
    run = _get_run_or_404(session, run_id)
    overview = run.summary_json or build_run_overview(run)
    return RunSummaryResponse(run=run, persona=run.persona, overview=overview)


@router.get("/{run_id}/clauses", response_model=ClauseResultsResponse)
def get_clause_results(run_id: UUID, session: Session = Depends(get_db_session)) -> ClauseResultsResponse:
    run = _get_run_or_404(session, run_id)
    clause_changes = list(
        session.scalars(
            select(ClauseChange)
            .where(ClauseChange.negotiation_run_id == run_id)
            .order_by(ClauseChange.created_at.asc())
            .options(
                selectinload(ClauseChange.original_clause),
                selectinload(ClauseChange.revised_clause),
                selectinload(ClauseChange.simulation_result),
                selectinload(ClauseChange.scoring_result),
                selectinload(ClauseChange.retrieval_hits).selectinload(RetrievalHit.evidence_source),
            )
        )
    )
    results = [
        ClauseReviewResult(
            clause_change=change,
            original_clause=change.original_clause,
            revised_clause=change.revised_clause,
            simulation_result=change.simulation_result,
            scoring_result=change.scoring_result,
            retrieval_hits=change.retrieval_hits,
        )
        for change in clause_changes
    ]
    return ClauseResultsResponse(run=run, results=results)


@router.get(
    "/{run_id}/clauses/{clause_change_id}/evidence",
    response_model=EvidenceForClauseResponse,
)
def get_clause_evidence(
    run_id: UUID,
    clause_change_id: UUID,
    session: Session = Depends(get_db_session),
) -> EvidenceForClauseResponse:
    _get_run_or_404(session, run_id)
    hits = list(
        session.scalars(
            select(RetrievalHit)
            .where(
                RetrievalHit.negotiation_run_id == run_id,
                RetrievalHit.clause_change_id == clause_change_id,
            )
            .options(selectinload(RetrievalHit.evidence_source))
            .order_by(RetrievalHit.rank.asc())
        )
    )
    return EvidenceForClauseResponse(clause_change_id=clause_change_id, hits=hits)


def _get_run_or_404(session: Session, run_id: UUID) -> NegotiationRun:
    statement = (
        select(NegotiationRun)
        .where(NegotiationRun.id == run_id)
        .options(
            selectinload(NegotiationRun.persona),
            selectinload(NegotiationRun.clause_changes),
            selectinload(NegotiationRun.scoring_results),
            selectinload(NegotiationRun.simulation_results),
        )
    )
    run = session.scalar(statement)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return run
