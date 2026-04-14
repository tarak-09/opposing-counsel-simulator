from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import APIModel
from app.schemas.document import DocumentVersionRead
from app.schemas.persona import PersonaRead
from app.schemas.run import RunOverview, RunRead


class DemoHappyPathRequest(BaseModel):
    persona_slug: str = Field(default="big-tech-legal")
    run_async: bool = Field(default=False)


class DemoHappyPathResponse(APIModel):
    message: str
    task_mode: Literal["async", "sync"]
    persona: PersonaRead
    original_document_version: DocumentVersionRead
    revised_document_version: DocumentVersionRead
    evidence_document_versions: list[DocumentVersionRead]
    run: RunRead
    overview: RunOverview
