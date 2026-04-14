from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import APIModel, TimestampedRead
from app.schemas.document import ClauseRead, EvidenceSourceRead
from app.schemas.persona import PersonaRead


class CreateRunRequest(BaseModel):
    original_document_version_id: UUID
    revised_document_version_id: UUID
    persona_id: UUID
    evidence_document_version_ids: list[UUID] = Field(default_factory=list)
    run_async: bool = True


class RunRead(TimestampedRead):
    original_document_version_id: UUID
    revised_document_version_id: UUID
    persona_id: UUID
    status: str
    stage: str
    error_message: str | None = None
    input_snapshot: dict[str, object]
    summary_json: dict[str, object]
    total_changed_clauses: int
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RunStatusResponse(APIModel):
    run: RunRead


class RunAcceptedResponse(APIModel):
    run: RunRead
    task_mode: Literal["async", "sync"]


class RunOverview(APIModel):
    total_changed_clauses: int
    likely_pushback_count: int
    high_friction_clauses: int
    overall_negotiation_difficulty: float


class RetrievalHitRead(TimestampedRead):
    negotiation_run_id: UUID
    clause_change_id: UUID
    evidence_source_id: UUID
    rank: int
    vector_score: float
    lexical_score: float
    rerank_score: float
    snippet_text: str
    metadata_json: dict[str, object]
    evidence_source: EvidenceSourceRead


class SimulationResultRead(TimestampedRead):
    negotiation_run_id: UUID
    clause_change_id: UUID
    decision: str
    stance_strength: int
    business_reason: str
    legal_reason: str
    pushback_points: list[object]
    counterproposal_text: str
    strategy: str
    confidence: float
    critique_status: str
    grounded_evidence_count: int
    raw_model_output: dict[str, object]


class ScoringResultRead(TimestampedRead):
    negotiation_run_id: UUID
    clause_change_id: UUID
    pushback_probability: float
    negotiation_friction: float
    delay_risk: float
    severity: float
    friction_label: str
    explanation: str
    heuristic_details: dict[str, object]


class ClauseChangeRead(TimestampedRead):
    negotiation_run_id: UUID
    original_clause_id: UUID | None = None
    revised_clause_id: UUID | None = None
    clause_key: str
    change_type: str
    issue_type: str
    change_direction: str
    semantic_summary: str
    diff_details: dict[str, object]
    changed_tokens_count: int
    status: str


class ClauseReviewResult(APIModel):
    clause_change: ClauseChangeRead
    original_clause: ClauseRead | None = None
    revised_clause: ClauseRead | None = None
    simulation_result: SimulationResultRead | None = None
    scoring_result: ScoringResultRead | None = None
    retrieval_hits: list[RetrievalHitRead] = Field(default_factory=list)


class RunSummaryResponse(APIModel):
    run: RunRead
    persona: PersonaRead
    overview: RunOverview


class ClauseResultsResponse(APIModel):
    run: RunRead
    results: list[ClauseReviewResult]


class EvidenceForClauseResponse(APIModel):
    clause_change_id: UUID
    hits: list[RetrievalHitRead]

class SemanticChangeResponse(APIModel):
    summary: str
    changed_tokens_count: int
    added_phrases: list[str]
    removed_phrases: list[str]


class IssueClassificationResponse(APIModel):
    issue_type: str
    reasoning: str
    confidence: float


class ClauseSimulationOutput(APIModel):
    decision: Literal["accept", "push_back", "counter", "escalate"]
    stance_strength: int = Field(ge=1, le=5)
    business_reason: str
    legal_reason: str
    pushback_points: list[str]
    counterproposal_text: str
    strategy: str
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("pushback_points")
    @classmethod
    def validate_pushback_points(cls, value: list[str]) -> list[str]:
        return [item for item in value if item.strip()]


class CritiqueOutcome(APIModel):
    valid: bool
    critique_status: Literal["accepted", "repaired", "failed_safe"]
    issues: list[str] = Field(default_factory=list)
    repaired_output: ClauseSimulationOutput | None = None


class ClauseScoreOutput(APIModel):
    pushback_probability: float = Field(ge=0.0, le=1.0)
    negotiation_friction: float = Field(ge=0.0, le=1.0)
    delay_risk: float = Field(ge=0.0, le=1.0)
    severity: float = Field(ge=0.0, le=1.0)
    friction_label: Literal["low", "medium", "high"]
    explanation: str
    heuristic_details: dict[str, object]
