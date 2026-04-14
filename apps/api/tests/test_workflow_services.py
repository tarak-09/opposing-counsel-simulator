from __future__ import annotations

from uuid import uuid4

from app.db.models import Clause, ClauseChange, ClauseChangeType, EvidenceSource, IssueType
from app.db.models import ChangeDirection, DocumentType
from app.services.classification import classify_clause_change
from app.services.critique import critique_simulation_output
from app.services.diffing import diff_clauses
from app.services.parsing import parse_contract_text
from app.services.retrieval import EvidenceHitCandidate
from app.services.scoring import score_clause
from app.services.simulation import simulate_clause_response


def test_clause_workflow_runs_end_to_end(sample_data_root, sample_persona):
    original_text = (sample_data_root / "contracts" / "original_msa.txt").read_text(encoding="utf-8")
    revised_text = (sample_data_root / "contracts" / "revised_msa.txt").read_text(encoding="utf-8")

    original_clauses = _materialize_clauses(parse_contract_text(original_text).clauses)
    revised_clauses = _materialize_clauses(parse_contract_text(revised_text).clauses)

    candidates = diff_clauses(original_clauses, revised_clauses)
    assert candidates

    candidate = next(change for change in candidates if change.change_type == ClauseChangeType.MODIFIED)
    clause_change = ClauseChange(
        negotiation_run_id=uuid4(),
        original_clause_id=candidate.original_clause.id if candidate.original_clause else None,
        revised_clause_id=candidate.revised_clause.id if candidate.revised_clause else None,
        clause_key=candidate.clause_key,
        change_type=ClauseChangeType.MODIFIED,
        issue_type=IssueType.GENERAL,
        change_direction=ChangeDirection.CUSTOMER_FAVORABLE,
        semantic_summary=candidate.semantic_summary,
        diff_details=candidate.diff_details,
        changed_tokens_count=candidate.changed_tokens_count,
        status="pending",
    )
    clause_change.original_clause = candidate.original_clause
    clause_change.revised_clause = candidate.revised_clause

    classification = classify_clause_change(clause_change)
    clause_change.issue_type = IssueType(classification.issue_type)

    evidence_source = EvidenceSource(
        document_version_id=uuid4(),
        evidence_type=DocumentType.FALLBACK,
        title="Fallback Clauses",
        section_label="Balanced Liability Cap",
        snippet_text="Each party's aggregate liability remains capped at twelve months of fees with standard carve-outs.",
        full_text="Each party's aggregate liability remains capped at twelve months of fees with standard carve-outs.",
        token_count=18,
        metadata_json={},
    )
    evidence_hit = EvidenceHitCandidate(
        evidence_source=evidence_source,
        vector_score=0.88,
        lexical_score=0.71,
        rerank_score=0.82,
        snippet_text=evidence_source.snippet_text,
        metadata={"title": evidence_source.title},
    )

    simulated = simulate_clause_response(clause_change, sample_persona, [evidence_hit])
    critique = critique_simulation_output(
        clause_change=clause_change,
        persona=sample_persona,
        evidence_hits=[evidence_hit],
        output=simulated,
    )
    final_output = critique.repaired_output or simulated
    score = score_clause(clause_change, final_output, sample_persona)

    assert clause_change.issue_type in {IssueType.LIMITATION_OF_LIABILITY, IssueType.PAYMENT_TERMS, IssueType.TERMINATION, IssueType.GENERAL}
    assert final_output.decision in {"accept", "push_back", "counter", "escalate"}
    assert score.friction_label in {"low", "medium", "high"}
    assert score.pushback_probability >= 0


def _materialize_clauses(parsed_clauses):
    document_version_id = uuid4()
    return [
        Clause(
            id=uuid4(),
            document_version_id=document_version_id,
            stable_clause_id=clause.stable_clause_id,
            heading=clause.heading,
            heading_path=clause.heading_path,
            clause_number=clause.clause_number,
            order_index=clause.order_index,
            text=clause.text,
            normalized_text=clause.normalized_text,
            source_span=clause.source_span,
        )
        for clause in parsed_clauses
    ]
