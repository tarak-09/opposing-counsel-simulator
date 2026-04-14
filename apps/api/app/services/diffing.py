from __future__ import annotations

from dataclasses import dataclass
from difflib import ndiff

from app.db.models import ChangeDirection, Clause, ClauseChangeType
from app.llm.provider import get_reasoning_provider
from app.schemas.run import SemanticChangeResponse
from app.utils.prompt_loader import render_prompt_template
from app.utils.text import fuzzy_similarity, normalize_whitespace


@dataclass(slots=True)
class ClauseChangeCandidate:
    original_clause: Clause | None
    revised_clause: Clause | None
    change_type: ClauseChangeType
    semantic_summary: str
    diff_details: dict[str, object]
    changed_tokens_count: int
    change_direction: ChangeDirection

    @property
    def clause_key(self) -> str:
        if self.revised_clause:
            return self.revised_clause.stable_clause_id
        if self.original_clause:
            return self.original_clause.stable_clause_id
        return "unmatched-clause"


def diff_clauses(original_clauses: list[Clause], revised_clauses: list[Clause]) -> list[ClauseChangeCandidate]:
    original_by_key = {clause.stable_clause_id: clause for clause in original_clauses}
    unmatched_original = {clause.id: clause for clause in original_clauses}
    matched_original_ids: set[object] = set()
    changes: list[ClauseChangeCandidate] = []

    for revised in revised_clauses:
        original = original_by_key.get(revised.stable_clause_id)
        if original is None:
            original = _best_original_match(revised, list(unmatched_original.values()))

        if original is None:
            summary = _semantic_change_summary(None, revised.text)
            changes.append(
                ClauseChangeCandidate(
                    original_clause=None,
                    revised_clause=revised,
                    change_type=ClauseChangeType.ADDED,
                    semantic_summary=summary.summary,
                    diff_details={
                        "added_phrases": summary.added_phrases,
                        "removed_phrases": summary.removed_phrases,
                    },
                    changed_tokens_count=summary.changed_tokens_count,
                    change_direction=_infer_change_direction("", revised.text),
                )
            )
            continue

        matched_original_ids.add(original.id)
        unmatched_original.pop(original.id, None)

        if normalize_whitespace(original.text) == normalize_whitespace(revised.text):
            continue

        summary = _semantic_change_summary(original.text, revised.text)
        changes.append(
            ClauseChangeCandidate(
                original_clause=original,
                revised_clause=revised,
                change_type=ClauseChangeType.MODIFIED,
                semantic_summary=summary.summary,
                diff_details={
                    "added_phrases": summary.added_phrases,
                    "removed_phrases": summary.removed_phrases,
                    "similarity": round(fuzzy_similarity(original.text, revised.text), 3),
                },
                changed_tokens_count=summary.changed_tokens_count,
                change_direction=_infer_change_direction(original.text, revised.text),
            )
        )

    for original in unmatched_original.values():
        summary = _semantic_change_summary(original.text, None)
        changes.append(
            ClauseChangeCandidate(
                original_clause=original,
                revised_clause=None,
                change_type=ClauseChangeType.REMOVED,
                semantic_summary=summary.summary,
                diff_details={
                    "added_phrases": summary.added_phrases,
                    "removed_phrases": summary.removed_phrases,
                },
                changed_tokens_count=summary.changed_tokens_count,
                change_direction=_infer_change_direction(original.text, ""),
            )
        )
    return changes


def _best_original_match(revised_clause: Clause, candidates: list[Clause]) -> Clause | None:
    best_clause: Clause | None = None
    best_score = 0.0
    for candidate in candidates:
        score = max(
            fuzzy_similarity(revised_clause.heading, candidate.heading),
            fuzzy_similarity(revised_clause.text, candidate.text),
        )
        if score > best_score:
            best_score = score
            best_clause = candidate
    if best_score >= 0.76:
        return best_clause
    return None


def _semantic_change_summary(original_text: str | None, revised_text: str | None) -> SemanticChangeResponse:
    provider = get_reasoning_provider()
    if provider is not None:
        try:
            return provider.generate_json(
                system_prompt="Summarize clause-level legal redlines as strict JSON only.",
                user_prompt=render_prompt_template(
                    "semantic_change.md",
                    {
                        "original_text": original_text or "",
                        "revised_text": revised_text or "",
                    },
                ),
                response_model=SemanticChangeResponse,
            )
        except Exception:
            pass

    before = normalize_whitespace(original_text or "")
    after = normalize_whitespace(revised_text or "")
    diff = list(ndiff(before.split(), after.split()))
    added_phrases = [part[2:] for part in diff if part.startswith("+ ")][:8]
    removed_phrases = [part[2:] for part in diff if part.startswith("- ")][:8]
    if original_text and revised_text:
        summary = "Clause language was revised to change scope, obligations, or risk allocation."
    elif revised_text and not original_text:
        summary = "A new clause was introduced in the revised draft."
    else:
        summary = "A clause from the original draft was removed from the revised draft."
    return SemanticChangeResponse(
        summary=summary,
        changed_tokens_count=len(added_phrases) + len(removed_phrases),
        added_phrases=added_phrases,
        removed_phrases=removed_phrases,
    )


def _infer_change_direction(original_text: str, revised_text: str) -> ChangeDirection:
    customer_favorable_signals = {
        "unlimited liability",
        "indemnify",
        "data breach",
        "terminate for convenience",
        "audit",
        "service credits",
        "security incident",
        "refund",
    }
    vendor_favorable_signals = {
        "sole remedy",
        "aggregate liability cap",
        "as is",
        "disclaim",
        "non-refundable",
        "exclusive remedy",
        "commercially reasonable",
        "thirty days",
    }
    before = normalize_whitespace(original_text.lower())
    after = normalize_whitespace(revised_text.lower())
    customer_delta = sum(after.count(signal) - before.count(signal) for signal in customer_favorable_signals)
    vendor_delta = sum(after.count(signal) - before.count(signal) for signal in vendor_favorable_signals)
    if customer_delta > vendor_delta and customer_delta > 0:
        return ChangeDirection.CUSTOMER_FAVORABLE
    if vendor_delta > customer_delta and vendor_delta > 0:
        return ChangeDirection.VENDOR_FAVORABLE
    return ChangeDirection.MUTUAL_OR_NEUTRAL
