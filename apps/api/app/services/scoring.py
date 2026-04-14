from __future__ import annotations

from app.db.models import ClauseChange, Persona
from app.schemas.run import ClauseScoreOutput, ClauseSimulationOutput


SEVERITY_BY_ISSUE = {
    "limitation_of_liability": 0.95,
    "indemnity": 0.93,
    "data_protection": 0.92,
    "security": 0.9,
    "ip_ownership": 0.82,
    "termination": 0.78,
    "warranties": 0.74,
    "confidentiality": 0.68,
    "payment_terms": 0.63,
    "service_levels": 0.58,
    "audit_rights": 0.7,
    "governing_law": 0.5,
    "general": 0.45,
}

DECISION_WEIGHT = {
    "accept": 0.15,
    "push_back": 0.68,
    "counter": 0.76,
    "escalate": 0.92,
}


def score_clause(
    clause_change: ClauseChange,
    simulation_output: ClauseSimulationOutput,
    persona: Persona,
) -> ClauseScoreOutput:
    base_severity = SEVERITY_BY_ISSUE.get(clause_change.issue_type.value, 0.45)
    decision_factor = DECISION_WEIGHT[simulation_output.decision]
    leverage_factor = persona.leverage / 5
    rigidity_factor = persona.liability_strictness / 5
    speed_factor = 1 - (persona.speed_priority / 10)
    stance_factor = simulation_output.stance_strength / 5
    fallback_factor = 1 - (persona.fallback_flexibility / 10)

    pushback_probability = _clamp(
        0.35 * base_severity
        + 0.3 * decision_factor
        + 0.15 * leverage_factor
        + 0.2 * stance_factor
    )
    negotiation_friction = _clamp(
        0.25 * base_severity
        + 0.25 * decision_factor
        + 0.15 * rigidity_factor
        + 0.2 * fallback_factor
        + 0.15 * speed_factor
    )
    delay_risk = _clamp(0.4 * negotiation_friction + 0.3 * leverage_factor + 0.3 * speed_factor)
    severity = _clamp(0.5 * base_severity + 0.3 * rigidity_factor + 0.2 * leverage_factor)
    friction_label = "low" if negotiation_friction < 0.4 else "medium" if negotiation_friction < 0.72 else "high"
    explanation = (
        "Heuristic score driven by issue sensitivity, persona leverage/strictness, fallback flexibility, "
        "and the simulated clause outcome. This is not a trained predictive model."
    )
    return ClauseScoreOutput(
        pushback_probability=round(pushback_probability, 2),
        negotiation_friction=round(negotiation_friction, 2),
        delay_risk=round(delay_risk, 2),
        severity=round(severity, 2),
        friction_label=friction_label,
        explanation=explanation,
        heuristic_details={
            "base_severity": round(base_severity, 2),
            "decision_factor": round(decision_factor, 2),
            "leverage_factor": round(leverage_factor, 2),
            "rigidity_factor": round(rigidity_factor, 2),
            "speed_factor": round(speed_factor, 2),
            "fallback_factor": round(fallback_factor, 2),
        },
    )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
