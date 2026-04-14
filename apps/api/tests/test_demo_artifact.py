from __future__ import annotations

import json
from pathlib import Path


def test_demo_happy_path_artifact_exists_and_has_expected_shape():
    artifact_path = (
        Path(__file__).resolve().parents[3] / "packages" / "sample-data" / "example-run" / "happy_path.json"
    )
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert payload["task_mode"] in {"sync", "async"}
    assert payload["persona"]["slug"]
    assert payload["overview"]["total_changed_clauses"] >= 1
    assert "run_id" in payload
