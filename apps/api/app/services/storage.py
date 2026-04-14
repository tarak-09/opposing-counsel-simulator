from __future__ import annotations

from pathlib import Path
from uuid import UUID

from app.core.config import get_settings


def ensure_storage_root() -> Path:
    settings = get_settings()
    settings.file_storage_root.mkdir(parents=True, exist_ok=True)
    return settings.file_storage_root


def build_upload_path(document_id: UUID, version_id: UUID, filename: str) -> Path:
    safe_name = "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in filename)
    return ensure_storage_root() / "uploads" / str(document_id) / f"{version_id}_{safe_name}"


def write_upload(document_id: UUID, version_id: UUID, filename: str, payload: bytes) -> str:
    target = build_upload_path(document_id, version_id, filename)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return str(target)
