from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Iterable
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ClauseChange, DocumentType, EvidenceSource
from app.llm.provider import get_embedding_provider
from app.utils.text import normalize_whitespace


logger = logging.getLogger(__name__)

# Legal-domain synonym expansion per issue type.
# Expanding the query before BM25 scoring improves recall for clause text
# that uses different terminology for the same legal concept.
_QUERY_EXPANSION: dict[str, list[str]] = {
    "limitation_of_liability": ["liability cap", "damages ceiling", "consequential loss", "aggregate limit"],
    "indemnity": ["indemnification", "hold harmless", "defend", "third-party claims"],
    "confidentiality": ["nda", "non-disclosure", "proprietary information", "trade secret"],
    "ip_ownership": ["intellectual property", "work product", "assignment", "license grant"],
    "payment_terms": ["invoice", "net 30", "late fee", "payment schedule", "overdue"],
    "warranties": ["representation", "as-is", "disclaimer", "fitness for purpose"],
    "termination": ["termination for cause", "termination for convenience", "notice period", "cure"],
    "data_protection": ["gdpr", "personal data", "data processing agreement", "privacy"],
    "security": ["soc 2", "iso 27001", "incident response", "encryption", "breach notification"],
    "governing_law": ["choice of law", "jurisdiction", "venue", "arbitration"],
    "service_levels": ["sla", "uptime", "availability", "service credits", "response time"],
    "audit_rights": ["inspection rights", "audit trail", "record keeping", "compliance review"],
}


@dataclass(slots=True)
class EvidenceHitCandidate:
    evidence_source: EvidenceSource
    vector_score: float
    lexical_score: float
    rerank_score: float
    snippet_text: str
    metadata: dict[str, object]


@dataclass
class RetrievalMetrics:
    """Diagnostic counters logged per retrieve call — useful for offline evaluation."""
    candidate_count: int = 0
    returned_count: int = 0
    vector_available: bool = False
    lexical_only_count: int = 0        # hits where vector_score == 0
    avg_rerank_score: float = 0.0
    top_rerank_score: float = 0.0
    query_terms: int = 0
    expanded_terms: int = 0


def index_evidence_sources(sources: Iterable[EvidenceSource]) -> None:
    source_list = list(sources)
    if not source_list:
        return

    client = _get_qdrant_client()
    if client is None:
        logger.warning("Qdrant unavailable during evidence indexing; continuing without vector indexing")
        return

    settings = get_settings()
    embedding_provider = get_embedding_provider()
    try:
        _ensure_collection(client)
        vectors = embedding_provider.embed([source.full_text for source in source_list])
        points = []
        for source, vector in zip(source_list, vectors, strict=False):
            source.vector_id = str(source.id)
            points.append(
                qdrant_models.PointStruct(
                    id=str(source.id),
                    vector=vector,
                    payload={
                        "evidence_source_id": str(source.id),
                        "document_version_id": str(source.document_version_id),
                        "evidence_type": source.evidence_type.value,
                        "title": source.title,
                        "section_label": source.section_label,
                        "snippet_text": source.snippet_text,
                    },
                )
            )
        client.upsert(collection_name=settings.qdrant_collection, points=points)
    except Exception:
        logger.exception("Vector indexing failed; continuing with lexical retrieval only")


def retrieve_supporting_evidence(
    session: Session,
    clause_change: ClauseChange,
    *,
    evidence_document_version_ids: list[UUID] | None = None,
    top_k: int = 5,
) -> list[EvidenceHitCandidate]:
    statement = select(EvidenceSource).where(
        EvidenceSource.evidence_type.in_(
            [DocumentType.PLAYBOOK, DocumentType.PRECEDENT, DocumentType.FALLBACK, DocumentType.BENCHMARK]
        )
    )
    if evidence_document_version_ids:
        statement = statement.where(EvidenceSource.document_version_id.in_(evidence_document_version_ids))
    sources = list(session.scalars(statement))
    if not sources:
        logger.debug("retrieve clause=%s: no evidence sources found", clause_change.id)
        return []

    settings = get_settings()
    lexical_weight = settings.retrieval_lexical_weight
    vector_weight = settings.retrieval_vector_weight

    query, expanded_query = _build_query_text(clause_change)
    lexical_scores = _lexical_scores(expanded_query, sources)
    vector_scores = _vector_scores(query, sources)

    max_lexical = max(lexical_scores.values(), default=1.0) or 1.0
    max_vector = max(vector_scores.values(), default=1.0) or 1.0
    vector_available = bool(vector_scores)

    ranked: list[EvidenceHitCandidate] = []
    for source in sources:
        lexical = lexical_scores.get(source.id, 0.0)
        vector = vector_scores.get(source.id, 0.0)
        rerank = (lexical_weight * (lexical / max_lexical)) + (vector_weight * (vector / max_vector))
        ranked.append(
            EvidenceHitCandidate(
                evidence_source=source,
                vector_score=round(vector, 4),
                lexical_score=round(lexical, 4),
                rerank_score=round(rerank, 4),
                snippet_text=source.snippet_text,
                metadata={
                    "section_label": source.section_label,
                    "evidence_type": source.evidence_type.value,
                    "title": source.title,
                },
            )
        )
    ranked.sort(key=lambda item: item.rerank_score, reverse=True)
    results = ranked[:top_k]

    metrics = RetrievalMetrics(
        candidate_count=len(sources),
        returned_count=len(results),
        vector_available=vector_available,
        lexical_only_count=sum(1 for h in results if h.vector_score == 0.0),
        avg_rerank_score=round(sum(h.rerank_score for h in results) / len(results), 4) if results else 0.0,
        top_rerank_score=results[0].rerank_score if results else 0.0,
        query_terms=len(_tokenize(query)),
        expanded_terms=len(_tokenize(expanded_query)),
    )
    logger.info(
        "retrieve clause=%s issue=%s candidates=%d returned=%d vector=%s "
        "lexical_only=%d top_score=%.4f avg_score=%.4f query_terms=%d expanded_terms=%d",
        clause_change.id,
        clause_change.issue_type.value,
        metrics.candidate_count,
        metrics.returned_count,
        metrics.vector_available,
        metrics.lexical_only_count,
        metrics.top_rerank_score,
        metrics.avg_rerank_score,
        metrics.query_terms,
        metrics.expanded_terms,
    )
    return results


def _tokenize(text: str) -> list[str]:
    """Regex tokenizer: lowercase, strip punctuation, drop single-char tokens.

    Compared to `.split()` this handles hyphenated terms like 'non-disclosure'
    and punctuation attached to words like 'liable.' or '(sla)'.
    """
    return [tok for tok in re.findall(r"[a-z][a-z0-9]*", text.lower()) if len(tok) > 1]


def _build_query_text(clause_change: ClauseChange) -> tuple[str, str]:
    """Return (base_query, expanded_query).

    base_query   — used for vector retrieval (dense embeddings already capture semantics).
    expanded_query — used for BM25 with synonym expansion to improve lexical recall.
    """
    original_text = clause_change.original_clause.text if clause_change.original_clause else ""
    revised_text = clause_change.revised_clause.text if clause_change.revised_clause else ""
    base_query = normalize_whitespace(
        " ".join([
            clause_change.issue_type.value.replace("_", " "),
            clause_change.semantic_summary,
            original_text,
            revised_text,
        ])
    )
    expansions = _QUERY_EXPANSION.get(clause_change.issue_type.value, [])
    expanded_query = base_query if not expansions else normalize_whitespace(
        base_query + " " + " ".join(expansions)
    )
    return base_query, expanded_query


def _lexical_scores(query: str, sources: list[EvidenceSource]) -> dict[object, float]:
    corpus = [_tokenize(source.full_text) for source in sources]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(_tokenize(query))
    return {source.id: float(score) for source, score in zip(sources, scores, strict=False)}


def _vector_scores(query: str, sources: list[EvidenceSource]) -> dict[object, float]:
    client = _get_qdrant_client()
    if client is None:
        return {}

    settings = get_settings()
    provider = get_embedding_provider()
    vector = provider.embed([query])[0]
    id_lookup = {str(source.id): source.id for source in sources}
    try:
        matches = _search_vector_matches(
            client,
            collection_name=settings.qdrant_collection,
            vector=vector,
            limit=max(10, len(sources)),
        )
    except Exception:
        logger.exception("Vector retrieval failed; continuing with lexical retrieval only")
        return {}

    scores: dict[object, float] = {}
    for match in matches:
        evidence_source_id = match.payload.get("evidence_source_id") if match.payload else None
        if evidence_source_id in id_lookup:
            scores[id_lookup[evidence_source_id]] = float(match.score or 0.0)
    return scores


def _ensure_collection(client: QdrantClient) -> None:
    settings = get_settings()
    try:
        exists = client.collection_exists(collection_name=settings.qdrant_collection)
    except TypeError:
        exists = client.collection_exists(settings.qdrant_collection)
    if exists:
        return
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=qdrant_models.VectorParams(
            size=settings.embedding_dimension,
            distance=qdrant_models.Distance.COSINE,
        ),
    )


def _get_qdrant_client() -> QdrantClient | None:
    settings = get_settings()
    try:
        return QdrantClient(url=settings.qdrant_url)
    except Exception:
        logger.exception("Failed to create Qdrant client")
        return None


def _search_vector_matches(
    client: QdrantClient,
    *,
    collection_name: str,
    vector: list[float],
    limit: int,
) -> list[object]:
    if hasattr(client, "query_points"):
        response = client.query_points(collection_name=collection_name, query=vector, limit=limit)
        return list(getattr(response, "points", response))
    return list(client.search(collection_name=collection_name, query_vector=vector, limit=limit))
