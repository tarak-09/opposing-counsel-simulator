from __future__ import annotations

import re
from dataclasses import dataclass

from app.utils.text import normalize_whitespace, sentence_lead, slugify, stable_short_hash


HEADING_RE = re.compile(
    r"^(?:(Section|SECTION|Article|ARTICLE)\s+)?(?P<number>\d+(?:\.\d+)*|[IVXLC]+)?[\.\)]?\s*(?P<title>[A-Z][^\n]{0,120})$"
)
ALL_CAPS_RE = re.compile(r"^[A-Z0-9\s\-/&,]{4,120}$")


@dataclass(slots=True)
class ParsedClause:
    stable_clause_id: str
    heading: str
    heading_path: str
    clause_number: str
    order_index: int
    text: str
    normalized_text: str
    source_span: dict[str, object]


@dataclass(slots=True)
class ParsedDocument:
    normalized_text: str
    clauses: list[ParsedClause]
    section_map: list[dict[str, object]]


def parse_contract_text(text: str) -> ParsedDocument:
    raw_lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [line.rstrip() for line in raw_lines]
    normalized_text = "\n".join(lines).strip()

    clauses: list[ParsedClause] = []
    section_map: list[dict[str, object]] = []
    block_lines: list[str] = []
    current_heading = ""
    current_clause_number = ""
    current_start_line = 1

    def flush(end_line: int) -> None:
        nonlocal block_lines, current_heading, current_clause_number, current_start_line
        content_lines = [line for line in block_lines if normalize_whitespace(line)]
        if not content_lines:
            block_lines = []
            return
        body = "\n".join(content_lines).strip()
        if not body:
            block_lines = []
            return
        order_index = len(clauses) + 1
        heading = current_heading or _derive_heading(body, order_index)
        clause_number = current_clause_number or str(order_index)
        heading_path = heading
        stable_key_source = current_clause_number or heading or sentence_lead(body)
        stable_clause_id = slugify(stable_key_source)[:60]
        if stable_clause_id == "clause":
            stable_clause_id = f"clause-{stable_short_hash(body)}"
        clause = ParsedClause(
            stable_clause_id=stable_clause_id,
            heading=heading,
            heading_path=heading_path,
            clause_number=clause_number,
            order_index=order_index,
            text=body,
            normalized_text=normalize_whitespace(body),
            source_span={"start_line": current_start_line, "end_line": end_line},
        )
        clauses.append(clause)
        section_map.append(
            {
                "heading": heading,
                "clause_number": clause_number,
                "stable_clause_id": stable_clause_id,
                "start_line": current_start_line,
                "end_line": end_line,
            }
        )
        block_lines = []

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            if block_lines:
                block_lines.append("")
            continue

        heading_match = _match_heading(stripped)
        if heading_match:
            if block_lines:
                flush(line_number - 1)
            current_start_line = line_number
            current_clause_number = heading_match["number"]
            current_heading = heading_match["title"]
            block_lines = [stripped]
            continue

        if not block_lines:
            current_start_line = line_number
            current_heading = ""
            current_clause_number = ""
        block_lines.append(stripped)

    if block_lines:
        flush(len(lines))

    if not clauses:
        clauses = _fallback_paragraph_parse(normalized_text)
        section_map = [
            {
                "heading": clause.heading,
                "clause_number": clause.clause_number,
                "stable_clause_id": clause.stable_clause_id,
                "start_line": clause.source_span["start_line"],
                "end_line": clause.source_span["end_line"],
            }
            for clause in clauses
        ]

    return ParsedDocument(normalized_text=normalized_text, clauses=clauses, section_map=section_map)


def _fallback_paragraph_parse(text: str) -> list[ParsedClause]:
    paragraphs = [part.strip() for part in text.split("\n\n") if normalize_whitespace(part)]
    clauses: list[ParsedClause] = []
    for index, paragraph in enumerate(paragraphs, start=1):
        heading = _derive_heading(paragraph, index)
        stable_clause_id = f"clause-{index}-{stable_short_hash(paragraph)}"
        clauses.append(
            ParsedClause(
                stable_clause_id=stable_clause_id,
                heading=heading,
                heading_path=heading,
                clause_number=str(index),
                order_index=index,
                text=paragraph,
                normalized_text=normalize_whitespace(paragraph),
                source_span={"start_line": index, "end_line": index},
            )
        )
    return clauses


def _match_heading(value: str) -> dict[str, str] | None:
    match = HEADING_RE.match(value)
    if match and (match.group("number") or ALL_CAPS_RE.match(value)):
        number = (match.group("number") or "").strip()
        title = (match.group("title") or value).strip()
        return {"number": number, "title": title}
    if ALL_CAPS_RE.match(value):
        return {"number": "", "title": value.title()}
    return None


def _derive_heading(text: str, index: int) -> str:
    lead = sentence_lead(text, max_sentences=1)[:90].strip()
    return lead or f"Clause {index}"
