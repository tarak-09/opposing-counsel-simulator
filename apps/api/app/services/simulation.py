from __future__ import annotations

import logging
from collections.abc import Sequence

from app.db.models import ClauseChange, Persona
from app.llm.provider import get_reasoning_provider, json_dumps_pretty
from app.schemas.run import ClauseSimulationOutput
from app.services.retrieval import EvidenceHitCandidate
from app.utils.prompt_loader import render_prompt_template


logger = logging.getLogger(__name__)


ISSUE_SEVERITY = {
    "limitation_of_liability": 5,
    "indemnity": 5,
    "data_protection": 5,
    "security": 5,
    "confidentiality": 3,
    "ip_ownership": 4,
    "payment_terms": 3,
    "warranties": 4,
    "termination": 4,
    "governing_law": 2,
    "service_levels": 3,
    "audit_rights": 4,
    "general": 2,
}


def simulate_clause_response(
    clause_change: ClauseChange,
    persona: Persona,
    evidence_hits: Sequence[EvidenceHitCandidate],
) -> ClauseSimulationOutput:
    provider = get_reasoning_provider()
    if provider is not None:
        try:
            evidence_payload = [
                {
                    "title": hit.evidence_source.title,
                    "type": hit.evidence_source.evidence_type.value,
                    "section_label": hit.evidence_source.section_label,
                    "snippet_text": hit.snippet_text,
                    "rerank_score": hit.rerank_score,
                }
                for hit in evidence_hits
            ]
            result = provider.generate_json(
                system_prompt="You simulate opposing counsel clause-by-clause. Respond with strict JSON only.",
                user_prompt=render_prompt_template(
                    "clause_simulation.md",
                    {
                        "persona": json_dumps_pretty(
                            {
                                "name": persona.name,
                                "description": persona.description,
                                "risk_tolerance": persona.risk_tolerance,
                                "leverage": persona.leverage,
                                "speed_priority": persona.speed_priority,
                                "privacy_sensitivity": persona.privacy_sensitivity,
                                "liability_strictness": persona.liability_strictness,
                                "fallback_flexibility": persona.fallback_flexibility,
                                "tone": persona.tone,
                                "issue_positions": persona.issue_positions,
                            }
                        ),
                        "issue_type": clause_change.issue_type.value,
                        "change_direction": clause_change.change_direction.value,
                        "semantic_summary": clause_change.semantic_summary,
                        "original_text": clause_change.original_clause.text if clause_change.original_clause else "",
                        "revised_text": clause_change.revised_clause.text if clause_change.revised_clause else "",
                        "evidence": json_dumps_pretty({"evidence": evidence_payload}),
                    },
                ),
                response_model=ClauseSimulationOutput,
            )
            logger.debug(
                "simulate clause=%s path=llm decision=%s confidence=%.2f",
                clause_change.id, result.decision, result.confidence,
            )
            return result
        except Exception:
            logger.warning(
                "simulate clause=%s path=llm failed; using rule-based fallback",
                clause_change.id, exc_info=True,
            )

    issue_key = clause_change.issue_type.value
    position = persona.issue_positions.get(issue_key, {})
    severity = ISSUE_SEVERITY.get(issue_key, 2)
    leverage_factor = persona.leverage / 5
    strictness = max(persona.liability_strictness, severity)
    adverse = clause_change.change_direction.value == "customer_favorable" and persona.slug != "aggressive-procurement"

    decision = "accept"
    if position.get("non_negotiable"):
        decision = "escalate" if severity >= 5 and leverage_factor >= 0.8 else "counter"
    elif adverse or severity >= 4 or strictness >= 4:
        decision = "counter" if persona.fallback_flexibility >= 3 else "push_back"
    elif severity >= 3:
        decision = "push_back"

    logger.debug(
        "simulate clause=%s path=rule-based issue=%s severity=%d decision=%s adverse=%s",
        clause_change.id, issue_key, severity, decision, adverse,
    )
    stance_strength = min(5, max(1, round((severity + persona.leverage + persona.liability_strictness) / 3)))
    evidence_summary = _best_evidence_text(evidence_hits)
    counterproposal_text = _counterproposal_text(position, issue_key, evidence_hits, clause_change)
    return ClauseSimulationOutput(
        decision=decision,
        stance_strength=stance_strength,
        business_reason=_business_reason(persona, issue_key, evidence_summary),
        legal_reason=_legal_reason(issue_key, evidence_summary),
        pushback_points=_pushback_points(persona, position, issue_key, evidence_summary, decision),
        counterproposal_text=counterproposal_text,
        strategy=_strategy(persona, decision, issue_key),
        confidence=round(min(0.92, 0.45 + severity * 0.08 + leverage_factor * 0.1), 2),
    )


def _best_evidence_text(evidence_hits: Sequence[EvidenceHitCandidate]) -> str:
    if not evidence_hits:
        return ""
    best = evidence_hits[0]
    return f"{best.evidence_source.title} / {best.evidence_source.section_label}: {best.snippet_text[:220]}"


def _counterproposal_text(
    position: dict[str, object],
    issue_key: str,
    evidence_hits: Sequence[EvidenceHitCandidate],
    clause_change: ClauseChange,
) -> str:
    fallback_source = next(
        (hit for hit in evidence_hits if hit.evidence_source.evidence_type.value == "fallback"),
        None,
    )
    if fallback_source:
        return fallback_source.evidence_source.full_text
    preferred = position.get("fallback_clause")
    if isinstance(preferred, str) and preferred.strip():
        return preferred
    revised_text = clause_change.revised_clause.text if clause_change.revised_clause else ""
    original_text = clause_change.original_clause.text if clause_change.original_clause else ""
    if issue_key == "limitation_of_liability":
        return (
            "Each party's aggregate liability will be capped at fees paid or payable in the twelve months "
            "preceding the claim, excluding breaches of confidentiality, fraud, or willful misconduct."
        )
    if issue_key == "indemnity":
        return (
            "Indemnity should be limited to third-party claims arising from infringement, bodily injury, "
            "property damage, or a party's breach of law, subject to prompt notice and control of defense."
        )
    return original_text or revised_text or "Retain balanced language anchored to market fallback terms."


def _business_reason(persona: Persona, issue_key: str, evidence_summary: str) -> str:
    reason = (
        f"{persona.name} prioritizes {issue_key.replace('_', ' ')} positions that preserve leverage, "
        f"limit operational drag, and stay aligned with internal policy."
    )
    if evidence_summary:
        reason += f" Supporting evidence: {evidence_summary}"
    return reason


def _legal_reason(issue_key: str, evidence_summary: str) -> str:
    base = (
        f"The revised {issue_key.replace('_', ' ')} language changes legal risk allocation and should be "
        "measured against approved fallbacks and prior negotiation precedent."
    )
    if evidence_summary:
        base += f" Retrieved evidence points to: {evidence_summary}"
    return base


def _pushback_points(
    persona: Persona,
    position: dict[str, object],
    issue_key: str,
    evidence_summary: str,
    decision: str,
) -> list[str]:
    points = [
        f"{persona.name} will test whether the proposed {issue_key.replace('_', ' ')} change exceeds approved policy.",
    ]
    if decision in {"counter", "push_back", "escalate"}:
        points.append("The current redline shifts risk materially without a matching commercial concession.")
    if position.get("non_negotiable"):
        points.append("This issue is treated as a non-negotiable or escalation trigger for the selected persona.")
    if evidence_summary:
        points.append(f"Retrieved playbook or precedent support exists for a narrower fallback: {evidence_summary}")
    return points[:4]


def _strategy(persona: Persona, decision: str, issue_key: str) -> str:
    if decision == "accept":
        return f"Accept the revised {issue_key.replace('_', ' ')} language to preserve speed."
    if decision == "escalate":
        return "Escalate internally while holding the line on the highest-risk terms."
    if persona.speed_priority >= 4:
        return "Offer a narrow fallback quickly to keep the deal moving while avoiding unnecessary concessions."
    return "Use the retrieved fallback language as a clause-specific counterproposal and anchor the next round."
