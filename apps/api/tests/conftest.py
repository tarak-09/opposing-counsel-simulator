from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.db.models import Persona


@pytest.fixture()
def sample_data_root() -> Path:
    return Path(__file__).resolve().parents[3] / "packages" / "sample-data"


@pytest.fixture()
def builtin_personas() -> list[dict[str, object]]:
    path = Path(__file__).resolve().parents[3] / "packages" / "personas" / "builtin_personas.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture()
def sample_persona(builtin_personas: list[dict[str, object]]) -> Persona:
    data = builtin_personas[1]
    return Persona(
        slug=data["slug"],
        name=data["name"],
        description=data["description"],
        risk_tolerance=data["risk_tolerance"],
        leverage=data["leverage"],
        speed_priority=data["speed_priority"],
        privacy_sensitivity=data["privacy_sensitivity"],
        liability_strictness=data["liability_strictness"],
        fallback_flexibility=data["fallback_flexibility"],
        tone=data["tone"],
        issue_positions=data["issue_positions"],
        is_builtin=True,
        is_active=True,
    )
