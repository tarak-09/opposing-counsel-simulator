from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import ClauseChange, DocumentVersion, IssueType, NegotiationRun, RetrievalHit, RunStatus
from app.db.models import ScoringResult, SimulationDecision, SimulationResult
from app.services.classification import classify_clause_change
from app.services.critique import critique_simulation_output
from app.services.diffing import diff_clauses
from app.services.retrieval import EvidenceHitCandidate, retrieve_supporting_evidence
from app.services.scoring import score_clause
from app.services.simulation import simulate_clause_response


logger = logging.getLogger(__name__)


def run_negotiation_workflow(session: Session, run_id: UUID) -> NegotiationRun:
    run = _load_run(session, run_id)
    run.status = RunStatus.PROCESSING
    run.stage = "diffing"
    run.started_at = datetime.now(timezone.utc)
    run.error_message = None
    session.commit()
    logger.info("Run %s stage=%s", run.id, run.stage)

    try:
        _clear_previous_results(session, run)
        original_clauses = list(run.original_document_version.clauses)
        revised_clauses = list(run.revised_document_version.clauses)
        candidates = diff_clauses(original_clauses, revised_clauses)
        logger.info("Run %s diffed %s changed clauses", run.id, len(candidates))

        clause_changes: list[ClauseChange] = []
        for candidate in candidates:
            clause_change = ClauseChange(
                negotiation_run_id=run.id,
                original_clause_id=candidate.original_clause.id if candidate.original_clause else None,
                revised_clause_id=candidate.revised_clause.id if candidate.revised_clause else None,
                clause_key=candidate.clause_key,
                change_type=candidate.change_type,
                semantic_summary=candidate.semantic_summary,
                diff_details=candidate.diff_details,
                changed_tokens_count=candidate.changed_tokens_count,
                change_direction=candidate.change_direction,
            )
            session.add(clause_change)
            clause_changes.append(clause_change)
        session.commit()

        run.stage = "classification"
        session.commit()
        logger.info("Run %s stage=%s", run.id, run.stage)
        for clause_change in clause_changes:
            session.refresh(clause_change)
            classification = classify_clause_change(clause_change)
            clause_change.issue_type = IssueType(classification.issue_type)
            clause_change.status = "classified"
        session.commit()

        run.stage = "retrieval"
        session.commit()
        logger.info("Run %s stage=%s", run.id, run.stage)
        for clause_change in clause_changes:
            hits = retrieve_supporting_evidence(
                session,
                clause_change,
                evidence_document_version_ids=[
                    UUID(value) for value in run.input_snapshot.get("evidence_document_version_ids", [])
                ],
            )
            for rank, hit in enumerate(hits, start=1):
                session.add(
                    RetrievalHit(
                        negotiation_run_id=run.id,
                        clause_change_id=clause_change.id,
                        evidence_source_id=hit.evidence_source.id,
                        rank=rank,
                        vector_score=hit.vector_score,
                        lexical_score=hit.lexical_score,
                        rerank_score=hit.rerank_score,
                        snippet_text=hit.snippet_text,
                        metadata_json=hit.metadata,
                    )
                )
            clause_change.status = "retrieved"
        session.commit()

        run.stage = "simulation"
        session.commit()
        logger.info("Run %s stage=%s", run.id, run.stage)
        for clause_change in _load_clause_changes(session, run.id):
            evidence_hits = [_hit_candidate_from_retrieval_hit(hit) for hit in clause_change.retrieval_hits]
            simulated = simulate_clause_response(clause_change, run.persona, evidence_hits)
            critique = critique_simulation_output(
                clause_change=clause_change,
                persona=run.persona,
                evidence_hits=evidence_hits,
                output=simulated,
            )
            final_output = critique.repaired_output or simulated
            score = score_clause(clause_change, final_output, run.persona)

            session.add(
                SimulationResult(
                    negotiation_run_id=run.id,
                    clause_change_id=clause_change.id,
                    decision=SimulationDecision(final_output.decision),
                    stance_strength=final_output.stance_strength,
                    business_reason=final_output.business_reason,
                    legal_reason=final_output.legal_reason,
                    pushback_points=final_output.pushback_points,
                    counterproposal_text=final_output.counterproposal_text,
                    strategy=final_output.strategy,
                    confidence=final_output.confidence,
                    critique_status=critique.critique_status,
                    grounded_evidence_count=len(evidence_hits),
                    raw_model_output=final_output.model_dump(),
                )
            )
            session.add(
                ScoringResult(
                    negotiation_run_id=run.id,
                    clause_change_id=clause_change.id,
                    pushback_probability=score.pushback_probability,
                    negotiation_friction=score.negotiation_friction,
                    delay_risk=score.delay_risk,
                    severity=score.severity,
                    friction_label=score.friction_label,
                    explanation=score.explanation,
                    heuristic_details=score.heuristic_details,
                )
            )
            clause_change.status = "completed"
        session.commit()

        run = _load_run(session, run.id)
        run.stage = "completed"
        run.status = RunStatus.COMPLETED
        run.total_changed_clauses = len(clause_changes)
        run.summary_json = build_run_overview(run)
        run.completed_at = datetime.now(timezone.utc)
        session.commit()
        logger.info("Run %s stage=%s status=%s", run.id, run.stage, run.status)
    except Exception as exc:
        logger.exception("Negotiation workflow failed for run %s", run.id)
        run.status = RunStatus.FAILED
        run.stage = "failed"
        run.error_message = str(exc)
        session.commit()
        raise

    return _load_run(session, run.id)


def build_run_overview(run: NegotiationRun) -> dict[str, object]:
    high_friction = sum(1 for score in run.scoring_results if score.friction_label == "high")
    likely_pushback = sum(1 for score in run.scoring_results if score.pushback_probability >= 0.6)
    overall_difficulty = (
        round(sum(score.negotiation_friction for score in run.scoring_results) / len(run.scoring_results), 2)
        if run.scoring_results
        else 0.0
    )
    return {
        "total_changed_clauses": len(run.clause_changes),
        "likely_pushback_count": likely_pushback,
        "high_friction_clauses": high_friction,
        "overall_negotiation_difficulty": overall_difficulty,
    }


def _clear_previous_results(session: Session, run: NegotiationRun) -> None:
    session.execute(delete(RetrievalHit).where(RetrievalHit.negotiation_run_id == run.id))
    session.execute(delete(SimulationResult).where(SimulationResult.negotiation_run_id == run.id))
    session.execute(delete(ScoringResult).where(ScoringResult.negotiation_run_id == run.id))
    session.execute(delete(ClauseChange).where(ClauseChange.negotiation_run_id == run.id))
    session.commit()


def _load_run(session: Session, run_id: UUID) -> NegotiationRun:
    statement = (
        select(NegotiationRun)
        .where(NegotiationRun.id == run_id)
        .options(
            selectinload(NegotiationRun.persona),
            selectinload(NegotiationRun.clause_changes),
            selectinload(NegotiationRun.simulation_results),
            selectinload(NegotiationRun.scoring_results),
            selectinload(NegotiationRun.original_document_version).selectinload(DocumentVersion.clauses),
            selectinload(NegotiationRun.revised_document_version).selectinload(DocumentVersion.clauses),
        )
    )
    run = session.scalar(statement)
    if run is None:
        raise ValueError(f"Negotiation run {run_id} was not found.")
    return run


def _load_clause_changes(session: Session, run_id: UUID) -> list[ClauseChange]:
    statement = (
        select(ClauseChange)
        .where(ClauseChange.negotiation_run_id == run_id)
        .order_by(ClauseChange.created_at.asc())
        .options(
            selectinload(ClauseChange.original_clause),
            selectinload(ClauseChange.revised_clause),
            selectinload(ClauseChange.retrieval_hits).selectinload(RetrievalHit.evidence_source),
        )
    )
    return list(session.scalars(statement))


def _hit_candidate_from_retrieval_hit(hit: RetrievalHit) -> EvidenceHitCandidate:
    return EvidenceHitCandidate(
        evidence_source=hit.evidence_source,
        vector_score=hit.vector_score,
        lexical_score=hit.lexical_score,
        rerank_score=hit.rerank_score,
        snippet_text=hit.snippet_text,
        metadata=hit.metadata_json,
    )
