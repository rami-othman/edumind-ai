"""Retrieve source chunks for future source-grounded RAG flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import get_settings
from app.services.vector_store.vector_store_service import (
    get_chunks_for_keyword_search,
    query_similar_chunks,
)
from app.utils.arabic_text_utils import (
    extract_search_terms,
    normalize_arabic_for_search,
)


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: dict[str, object]
    distance: float | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a serializable representation of the retrieved chunk."""

        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "metadata": self.metadata,
            "distance": self.distance,
        }


def retrieve_similar_chunks(
    question: str,
    embedding_service,
    vector_store_client,
    top_k: int = 5,
    where: dict[str, object] | None = None,
    retrieval_mode: str | None = None,
    keyword_candidate_limit: int | None = None,
    keyword_top_k: int | None = None,
) -> list[RetrievedChunk]:
    """Embed a question and retrieve similar source chunks from the vector store."""

    if not isinstance(question, str):
        raise TypeError("question must be a string")
    if not question.strip():
        raise ValueError("question must not be empty")
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    settings = get_settings()
    resolved_retrieval_mode = (retrieval_mode or settings.retrieval_mode).lower()
    resolved_keyword_candidate_limit = (
        keyword_candidate_limit or settings.keyword_candidate_limit
    )
    resolved_keyword_top_k = keyword_top_k or settings.keyword_top_k

    normalized_question = normalize_arabic_for_search(question)
    query_embedding = embedding_service.embed_text(normalized_question)
    vector_results = query_similar_chunks(
        query_embedding=query_embedding,
        client=vector_store_client,
        top_k=top_k,
        where=where,
    )

    if resolved_retrieval_mode == "vector":
        return [_build_retrieved_chunk(result) for result in vector_results]
    if resolved_retrieval_mode != "hybrid":
        raise ValueError("retrieval_mode must be 'vector' or 'hybrid'")

    keyword_results = _retrieve_keyword_matches(
        question=normalized_question,
        vector_store_client=vector_store_client,
        where=where,
        candidate_limit=resolved_keyword_candidate_limit,
        keyword_top_k=resolved_keyword_top_k,
    )
    merged_results = _merge_retrieval_results(vector_results, keyword_results)

    return [_build_retrieved_chunk(result) for result in merged_results[:top_k]]


def _retrieve_keyword_matches(
    *,
    question: str,
    vector_store_client,
    where: dict[str, object] | None,
    candidate_limit: int,
    keyword_top_k: int,
) -> list[dict[str, Any]]:
    if candidate_limit <= 0:
        raise ValueError("keyword_candidate_limit must be greater than 0")
    if keyword_top_k <= 0:
        raise ValueError("keyword_top_k must be greater than 0")

    search_terms = extract_search_terms(question)
    if not search_terms:
        return []

    candidates = get_chunks_for_keyword_search(
        vector_store_client,
        where=where,
        limit=candidate_limit,
    )
    scored_results: list[dict[str, Any]] = []

    for candidate in candidates:
        normalized_text = normalize_arabic_for_search(str(candidate.get("text", "")))
        keyword_score = _score_keyword_match(search_terms, normalized_text)
        if keyword_score <= 0:
            continue

        scored_candidate = dict(candidate)
        scored_candidate["_keyword_score"] = keyword_score
        scored_results.append(scored_candidate)

    scored_results.sort(key=lambda result: int(result["_keyword_score"]), reverse=True)
    return scored_results[:keyword_top_k]


def _score_keyword_match(search_terms: list[str], normalized_text: str) -> int:
    score = sum(1 for term in search_terms if term in normalized_text)

    for first_term, second_term in zip(search_terms, search_terms[1:], strict=False):
        forward_phrase = f"{first_term} {second_term}"
        reversed_phrase = f"{second_term} {first_term}"
        if forward_phrase in normalized_text or reversed_phrase in normalized_text:
            score += 2

    return score


def _merge_retrieval_results(
    vector_results: list[dict[str, Any]],
    keyword_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged_by_id: dict[str, dict[str, Any]] = {}

    for index, result in enumerate(vector_results):
        result_with_rank = dict(result)
        result_with_rank["_vector_rank"] = index
        result_with_rank["_keyword_score"] = 0
        merged_by_id[str(result["id"])] = result_with_rank

    for index, result in enumerate(keyword_results):
        result_id = str(result["id"])
        keyword_score = int(result.get("_keyword_score", 0))
        if result_id in merged_by_id:
            merged_by_id[result_id]["_keyword_score"] = keyword_score
            continue

        result_with_rank = dict(result)
        result_with_rank["_keyword_rank"] = index
        result_with_rank["_vector_rank"] = len(vector_results) + index
        merged_by_id[result_id] = result_with_rank

    return sorted(merged_by_id.values(), key=_retrieval_sort_key)


def _retrieval_sort_key(result: dict[str, Any]) -> tuple[int, int, int]:
    keyword_score = int(result.get("_keyword_score", 0))
    strong_keyword_match = 0 if keyword_score >= 2 else 1
    return (
        strong_keyword_match,
        -keyword_score,
        int(result.get("_vector_rank", 1_000_000)),
    )


def _build_retrieved_chunk(result: dict[str, Any]) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=str(result["id"]),
        text=str(result["text"]),
        metadata=_normalize_metadata(result.get("metadata")),
        distance=_normalize_distance(result.get("distance")),
    )


def _normalize_metadata(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value

    return {}


def _normalize_distance(value: object) -> float | None:
    if value is None:
        return None

    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)

    raise ValueError("distance must be a number or None")
