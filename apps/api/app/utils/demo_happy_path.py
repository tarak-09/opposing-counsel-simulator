from __future__ import annotations

import json
from pathlib import Path

from app.db import base  # noqa: F401
from app.db.models.base import Base
from app.db.session import SessionLocal, engine
from app.services.demo import bootstrap_demo_happy_path
from app.services.orchestration import build_run_overview


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        run, persona, original_version, revised_version, evidence_versions, task_mode = bootstrap_demo_happy_path(
            session,
            persona_slug="big-tech-legal",
            run_async=False,
        )
        payload = {
            "message": "Sample matter loaded and analysis completed.",
            "task_mode": task_mode,
            "persona": {"id": str(persona.id), "name": persona.name, "slug": persona.slug},
            "original_document_version_id": str(original_version.id),
            "revised_document_version_id": str(revised_version.id),
            "evidence_document_version_ids": [str(item.id) for item in evidence_versions],
            "run_id": str(run.id),
            "overview": run.summary_json or build_run_overview(run),
        }
        output_path = (
            Path(__file__).resolve().parents[4] / "packages" / "sample-data" / "example-run" / "happy_path.json"
        )
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
