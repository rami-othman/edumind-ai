"""Retrieve source chunks for future source-grounded RAG flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.vector_store.vector_store_service import query_similar_chunks


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
) -> list[RetrievedChunk]:
    """Embed a question and retrieve similar source chunks from the vector store."""

    if not isinstance(question, str):
        raise TypeError("question must be a string")
    if not question.strip():
        raise ValueError("question must not be empty")
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    query_embedding = embedding_service.embed_text(question)
    results = query_similar_chunks(
        query_embedding=query_embedding,
        client=vector_store_client,
        top_k=top_k,
        where=where,
    )

    return [_build_retrieved_chunk(result) for result in results]


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
