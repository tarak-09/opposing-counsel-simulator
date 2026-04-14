from __future__ import annotations

import io
from pathlib import Path

import fitz
from docx import Document as DocxDocument

from app.utils.text import normalize_whitespace


def extract_text_from_bytes(filename: str, payload: bytes, mime_type: str | None = None) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf" or mime_type == "application/pdf":
        return _extract_pdf_text(payload)
    if (
        suffix == ".docx"
        or mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        return _extract_docx_text(payload)
    return payload.decode("utf-8", errors="ignore")


def normalize_document_text(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    compacted = "\n".join(line for line in lines)
    return compacted.strip()


def _extract_pdf_text(payload: bytes) -> str:
    with fitz.open(stream=payload, filetype="pdf") as pdf:
        parts = [page.get_text("text") for page in pdf]
    return "\n".join(parts).strip()


def _extract_docx_text(payload: bytes) -> str:
    document = DocxDocument(io.BytesIO(payload))
    parts = [paragraph.text for paragraph in document.paragraphs if normalize_whitespace(paragraph.text)]
    return "\n".join(parts).strip()
