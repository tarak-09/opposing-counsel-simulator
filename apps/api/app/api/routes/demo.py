from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.demo import DemoHappyPathRequest, DemoHappyPathResponse
from app.services.demo import bootstrap_demo_happy_path
from app.services.orchestration import build_run_overview


router = APIRouter()


@router.post("/happy-path", response_model=DemoHappyPathResponse)
def run_demo_happy_path(
    payload: DemoHappyPathRequest,
    session: Session = Depends(get_db_session),
) -> DemoHappyPathResponse:
    try:
        run, persona, original_version, revised_version, evidence_versions, task_mode = (
            bootstrap_demo_happy_path(
                session,
                persona_slug=payload.persona_slug,
                run_async=payload.run_async,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    overview = run.summary_json or build_run_overview(run)
    return DemoHappyPathResponse(
        message=(
            "Sample matter loaded and analysis completed."
            if task_mode == "sync"
            else "Sample matter loaded and analysis launched."
        ),
        task_mode=task_mode,
        persona=persona,
        original_document_version=original_version,
        revised_document_version=revised_version,
        evidence_document_versions=evidence_versions,
        run=run,
        overview=overview,
    )
