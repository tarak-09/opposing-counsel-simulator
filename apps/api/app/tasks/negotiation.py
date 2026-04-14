from __future__ import annotations

from uuid import UUID

from app.db.session import SessionLocal
from app.services.orchestration import run_negotiation_workflow
from app.workers.celery_app import celery_app


@celery_app.task(name="negotiation.run_workflow")
def run_workflow_task(run_id: str) -> str:
    with SessionLocal() as session:
        run_negotiation_workflow(session, UUID(run_id))
    return run_id
