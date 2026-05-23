"""Vector store operations for precomputed chunk embeddings."""

from __future__ import annotations

from typing import Any

from app.services.ingestion.metadata_builder import ChunkRecord
from app.services.vector_store.chroma_client import ChromaClient


def add_chunk_records(
    records: list[ChunkRecord],
    embeddings: list[list[float]],
    client: ChromaClient,
) -> int:
    """Store chunk records with precomputed embeddings in ChromaDB."""

    if not records:
        raise ValueError("records must not be empty")
    if not embeddings:
        raise ValueError("embeddings must not be empty")
    if len(records) != len(embeddings):
        raise ValueError("records and embeddings must have the same length")

    for embedding in embeddings:
        _validate_embedding(embedding, "embedding")

    collection = client.get_or_create_collection()
    collection.add(
        ids=[record.chunk_id for record in records],
        documents=[record.text for record in records],
        metadatas=[record.metadata for record in records],
        embeddings=embeddings,
    )

    return len(records)


def query_similar_chunks(
    query_embedding: list[float],
    client: ChromaClient,
    top_k: int = 5,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Query ChromaDB for chunks similar to a precomputed query embedding."""

    _validate_embedding(query_embedding, "query_embedding")
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    collection = client.get_or_create_collection()
    raw_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    return _normalize_query_results(raw_results)


def _validate_embedding(embedding: object, field_name: str) -> None:
    if not isinstance(embedding, list) or not embedding:
        raise ValueError(f"{field_name} must be a non-empty list of numbers")

    if not all(
        isinstance(value, int | float) and not isinstance(value, bool)
        for value in embedding
    ):
        raise ValueError(f"{field_name} must be a non-empty list of numbers")


def _normalize_query_results(raw_results: dict[str, Any]) -> list[dict[str, Any]]:
    ids = _first_result_group(raw_results.get("ids"))
    documents = _first_result_group(raw_results.get("documents"))
    metadatas = _first_result_group(raw_results.get("metadatas"))
    distances = _first_result_group(raw_results.get("distances"))

    normalized_results: list[dict[str, Any]] = []
    for index, result_id in enumerate(ids):
        normalized_results.append(
            {
                "id": result_id,
                "text": documents[index] if index < len(documents) else "",
                "metadata": metadatas[index] if index < len(metadatas) else {},
                "distance": distances[index] if index < len(distances) else None,
            },
        )

    return normalized_results


def _first_result_group(value: object) -> list[Any]:
    if not isinstance(value, list) or not value:
        return []

    first_group = value[0]
    if not isinstance(first_group, list):
        return []

    return first_group
