from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings


def load_prompt_template(name: str) -> str:
    settings = get_settings()
    path = settings.prompt_root / name
    return Path(path).read_text(encoding="utf-8")


def render_prompt_template(name: str, values: dict[str, object]) -> str:
    template = load_prompt_template(name)
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    return rendered
