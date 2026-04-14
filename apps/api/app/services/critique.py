from __future__ import annotations

from collections.abc import Sequence

from app.db.models import ClauseChange, Persona
from app.schemas.run import ClauseSimulationOutput, CritiqueOutcome
from app.llm.provider import get_reasoning_provider, json_dumps_pretty
from app.services.retrieval import EvidenceHitCandidate
from app.utils.prompt_loader import render_prompt_template


def critique_simulation_output(
    *,
    clause_change: ClauseChange,
    persona: Persona,
    evidence_hits: Sequence[EvidenceHitCandidate],
    output: ClauseSimulationOutput,
    max_retries: int = 2,
) -> CritiqueOutcome:
    current_output = output
    issues = _find_issues(clause_change, persona, evidence_hits, current_output)
    retries = 0
    while issues and retries < max_retries:
        repaired = _repair_with_model(clause_change, persona, current_output, issues)
        current_output = repaired or _repair_output(clause_change, persona, evidence_hits, current_output, issues)
        retries += 1
        issues = _find_issues(clause_change, persona, evidence_hits, current_output)

    if issues:
        safe_output = _safe_fail_output(clause_change, persona, evidence_hits, current_output, issues)
        return CritiqueOutcome(
            valid=False,
            critique_status="failed_safe",
            issues=issues,
            repaired_output=safe_output,
        )

    if retries:
        return CritiqueOutcome(
            valid=True,
            critique_status="repaired",
            issues=[],
            repaired_output=current_output,
        )
    return CritiqueOutcome(valid=True, critique_status="accepted", issues=[], repaired_output=current_output)


def _find_issues(
    clause_change: ClauseChange,
    persona: Persona,
    evidence_hits: Sequence[EvidenceHitCandidate],
    output: ClauseSimulationOutput,
) -> list[str]:
    issues: list[str] = []
    issue_position = persona.issue_positions.get(clause_change.issue_type.value, {})
    if output.decision == "accept" and issue_position.get("non_negotiable"):
        issues.append("Decision accepts language on a persona non-negotiable issue.")
    if not output.business_reason.strip():
        issues.append("Missing business rationale.")
    if not output.legal_reason.strip():
        issues.append("Missing legal rationale.")
    if output.decision in {"counter", "push_back", "escalate"} and not output.pushback_points:
        issues.append("Missing pushback points for a non-accept decision.")
    if output.decision in {"counter", "push_back"} and not output.counterproposal_text.strip():
        issues.append("Missing counterproposal text.")
    if evidence_hits and "Retrieved" not in output.legal_reason and "Supporting evidence" not in output.business_reason:
        issues.append("Available evidence was not reflected in the rationale.")
    return issues


def _repair_with_model(
    clause_change: ClauseChange,
    persona: Persona,
    output: ClauseSimulationOutput,
    issues: list[str],
) -> ClauseSimulationOutput | None:
    provider = get_reasoning_provider()
    if provider is None:
        return None
    try:
        critique = provider.generate_json(
            system_prompt="Validate and repair clause-level negotiation output as strict JSON only.",
            user_prompt=render_prompt_template(
                "simulation_critic.md",
                {
                    "persona": json_dumps_pretty(
                        {
                            "name": persona.name,
                            "description": persona.description,
                            "tone": persona.tone,
                            "issue_positions": persona.issue_positions,
                        }
                    ),
                    "issue_type": clause_change.issue_type.value,
                    "issues": "\n".join(f"- {item}" for item in issues),
                    "candidate_output": output.model_dump_json(indent=2),
                },
            ),
            response_model=CritiqueOutcome,
        )
    except Exception:
        return None
    return critique.repaired_output


def _repair_output(
    clause_change: ClauseChange,
    persona: Persona,
    evidence_hits: Sequence[EvidenceHitCandidate],
    output: ClauseSimulationOutput,
    issues: list[str],
) -> ClauseSimulationOutput:
    repaired = output.model_copy(deep=True)
    if "Decision accepts language on a persona non-negotiable issue." in issues:
        repaired.decision = "counter"
    if "Missing business rationale." in issues:
        repaired.business_reason = (
            f"{persona.name} is unlikely to move quickly on {clause_change.issue_type.value.replace('_', ' ')} "
            "without policy support and a reciprocal concession."
        )
    if "Missing legal rationale." in issues:
        repaired.legal_reason = (
            f"The clause changes core {clause_change.issue_type.value.replace('_', ' ')} risk allocation and needs "
            "support from approved playbook or precedent language."
        )
    if "Missing pushback points for a non-accept decision." in issues:
        repaired.pushback_points = [
            "The current edit changes risk allocation beyond the selected persona's default posture.",
            "A narrower fallback is available and should be proposed instead of accepting the full redline.",
        ]
    if "Missing counterproposal text." in issues:
        repaired.counterproposal_text = (
            clause_change.original_clause.text
            if clause_change.original_clause
            else "Offer a narrower fallback aligned to approved policy language."
        )
    if "Available evidence was not reflected in the rationale." in issues and evidence_hits:
        best = evidence_hits[0]
        repaired.legal_reason += (
            f" Retrieved evidence: {best.evidence_source.title} / {best.evidence_source.section_label}."
        )
    return repaired


def _safe_fail_output(
    clause_change: ClauseChange,
    persona: Persona,
    evidence_hits: Sequence[EvidenceHitCandidate],
    output: ClauseSimulationOutput,
    issues: list[str],
) -> ClauseSimulationOutput:
    repaired = _repair_output(clause_change, persona, evidence_hits, output, issues)
    repaired.decision = "escalate"
    repaired.stance_strength = max(repaired.stance_strength, 4)
    repaired.strategy = "Escalate for human review because the automated pass could not fully validate this clause."
    repaired.confidence = min(repaired.confidence, 0.55)
    return repaired
