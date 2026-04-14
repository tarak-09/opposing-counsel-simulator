from __future__ import annotations

import logging
from collections import defaultdict

from app.db.models import ClauseChange, IssueType
from app.llm.provider import get_reasoning_provider
from app.schemas.run import IssueClassificationResponse
from app.utils.prompt_loader import render_prompt_template


logger = logging.getLogger(__name__)


ISSUE_KEYWORDS: dict[IssueType, tuple[str, ...]] = {
    IssueType.LIMITATION_OF_LIABILITY: ("liability", "damages", "cap", "consequential"),
    IssueType.INDEMNITY: ("indemn", "defend", "hold harmless"),
    IssueType.CONFIDENTIALITY: ("confidential", "non-disclosure", "disclose"),
    IssueType.IP_OWNERSHIP: ("intellectual property", "ownership", "license", "work product"),
    IssueType.PAYMENT_TERMS: ("fees", "invoice", "payment", "late payment", "net 30"),
    IssueType.WARRANTIES: ("warrant", "as is", "disclaimer", "conform"),
    IssueType.TERMINATION: ("terminate", "termination", "notice", "cure period"),
    IssueType.DATA_PROTECTION: ("personal data", "privacy", "data processing", "gdpr"),
    IssueType.SECURITY: ("security", "incident", "breach", "encryption", "soc 2"),
    IssueType.GOVERNING_LAW: ("governing law", "jurisdiction", "venue", "forum"),
    IssueType.SERVICE_LEVELS: ("uptime", "service level", "sla", "credits"),
    IssueType.AUDIT_RIGHTS: ("audit", "inspection", "records", "assess"),
}


def classify_clause_change(clause_change: ClauseChange) -> IssueClassificationResponse:
    combined_text = " ".join(
        filter(
            None,
            [
                clause_change.semantic_summary.lower(),
                clause_change.original_clause.text.lower() if clause_change.original_clause else "",
                clause_change.revised_clause.text.lower() if clause_change.revised_clause else "",
            ],
        )
    )
    scores: dict[IssueType, int] = defaultdict(int)
    for issue_type, keywords in ISSUE_KEYWORDS.items():
        for keyword in keywords:
            scores[issue_type] += combined_text.count(keyword)

    best_issue = max(scores, key=scores.get, default=IssueType.GENERAL)
    best_score = scores.get(best_issue, 0)
    if best_score > 0:
        confidence = min(0.95, 0.35 + (best_score * 0.12))
        logger.debug(
            "classify clause=%s path=heuristic issue=%s score=%d confidence=%.2f",
            clause_change.id, best_issue.value, best_score, confidence,
        )
        return IssueClassificationResponse(
            issue_type=best_issue.value,
            reasoning=f"Heuristic keyword match favored {best_issue.value.replace('_', ' ')}.",
            confidence=round(confidence, 2),
        )

    provider = get_reasoning_provider()
    if provider is not None:
        try:
            result = provider.generate_json(
                system_prompt="Classify changed contract clauses into a single issue type as strict JSON.",
                user_prompt=render_prompt_template(
                    "issue_classification.md",
                    {
                        "semantic_summary": clause_change.semantic_summary,
                        "original_text": clause_change.original_clause.text if clause_change.original_clause else "",
                        "revised_text": clause_change.revised_clause.text if clause_change.revised_clause else "",
                    },
                ),
                response_model=IssueClassificationResponse,
            )
            logger.debug(
                "classify clause=%s path=llm issue=%s confidence=%.2f",
                clause_change.id, result.issue_type, result.confidence,
            )
            return result
        except Exception:
            logger.warning(
                "classify clause=%s path=llm failed; falling back to general",
                clause_change.id, exc_info=True,
            )

    logger.debug("classify clause=%s path=fallback issue=general", clause_change.id)
    return IssueClassificationResponse(
        issue_type=IssueType.GENERAL.value,
        reasoning="No strong deterministic signal was present, so the clause was left as general.",
        confidence=0.25,
    )
