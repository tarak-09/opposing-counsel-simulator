from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher


WHITESPACE_RE = re.compile(r"\s+")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def normalize_whitespace(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value or "").strip()


def slugify(value: str) -> str:
    normalized = NON_ALNUM_RE.sub("-", normalize_whitespace(value).lower()).strip("-")
    return normalized or "clause"


def stable_short_hash(*parts: str, length: int = 12) -> str:
    digest = hashlib.sha1("||".join(parts).encode("utf-8")).hexdigest()
    return digest[:length]


def checksum_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sentence_lead(text: str, max_sentences: int = 1) -> str:
    pieces = [segment.strip() for segment in SENTENCE_SPLIT_RE.split(normalize_whitespace(text)) if segment]
    return " ".join(pieces[:max_sentences])


def fuzzy_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_whitespace(left), normalize_whitespace(right)).ratio()


def token_count(text: str) -> int:
    return len([token for token in normalize_whitespace(text).split(" ") if token])
