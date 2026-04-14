from __future__ import annotations

from app.services.parsing import parse_contract_text


def test_parse_contract_text_extracts_structured_clauses(sample_data_root):
    text = (sample_data_root / "contracts" / "original_msa.txt").read_text(encoding="utf-8")
    parsed = parse_contract_text(text)

    assert len(parsed.clauses) >= 6
    assert parsed.clauses[0].heading
    assert parsed.clauses[0].stable_clause_id
    assert parsed.section_map[0]["start_line"] >= 1
