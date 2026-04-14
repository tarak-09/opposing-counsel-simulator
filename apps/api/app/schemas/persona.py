from __future__ import annotations

from app.schemas.common import TimestampedRead


class PersonaRead(TimestampedRead):
    slug: str
    name: str
    description: str
    risk_tolerance: int
    leverage: int
    speed_priority: int
    privacy_sensitivity: int
    liability_strictness: int
    fallback_flexibility: int
    tone: str
    issue_positions: dict[str, object]
    is_builtin: bool
    is_active: bool
