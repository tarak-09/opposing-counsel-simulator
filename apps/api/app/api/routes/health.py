from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.health import HealthResponse


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(session: Session = Depends(get_db_session)) -> HealthResponse:
    session.execute(text("SELECT 1"))
    return HealthResponse(status="ok", service="opposing-counsel-simulator-api")
