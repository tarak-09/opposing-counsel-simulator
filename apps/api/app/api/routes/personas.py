from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.persona import PersonaRead
from app.services.personas import list_personas


router = APIRouter()


@router.get("", response_model=list[PersonaRead])
def get_personas(session: Session = Depends(get_db_session)) -> list[PersonaRead]:
    return [PersonaRead.model_validate(persona) for persona in list_personas(session)]
