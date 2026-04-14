from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Persona


def sync_builtin_personas(session: Session) -> list[Persona]:
    settings = get_settings()
    payload = json.loads(settings.personas_path.read_text(encoding="utf-8"))
    personas: list[Persona] = []

    for item in payload:
        existing = session.scalar(select(Persona).where(Persona.slug == item["slug"]))
        if existing is None:
            existing = Persona(slug=item["slug"])
            session.add(existing)

        existing.name = item["name"]
        existing.description = item["description"]
        existing.risk_tolerance = item["risk_tolerance"]
        existing.leverage = item["leverage"]
        existing.speed_priority = item["speed_priority"]
        existing.privacy_sensitivity = item["privacy_sensitivity"]
        existing.liability_strictness = item["liability_strictness"]
        existing.fallback_flexibility = item["fallback_flexibility"]
        existing.tone = item["tone"]
        existing.issue_positions = item["issue_positions"]
        existing.is_builtin = True
        existing.is_active = True
        personas.append(existing)

    session.commit()
    for persona in personas:
        session.refresh(persona)
    return personas


def list_personas(session: Session) -> list[Persona]:
    return list(session.scalars(select(Persona).where(Persona.is_active.is_(True)).order_by(Persona.name)))
