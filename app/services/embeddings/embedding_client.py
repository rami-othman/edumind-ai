"""Ollama embedding client."""

from __future__ import annotations

from typing import Any

import httpx


class EmbeddingClientError(Exception):
    """Raised when embedding generation fails."""


class OllamaEmbeddingClient:
    """Client for Ollama local embedding generation."""

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: float = 180.0,
        batch_size: int = 32,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0")
        self.batch_size = batch_size

    def embed_text(self, text: str) -> list[float]:
        """Embed one text value."""
        _validate_text(text)

        embeddings = self._request_embeddings(text)
        if not embeddings:
            raise EmbeddingClientError("Ollama embedding response did not include an embedding")

        return embeddings[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text values."""
        _validate_texts(texts)

        embeddings: list[list[float]] = []
        for batch_index, batch in enumerate(_batch_texts(texts, self.batch_size), start=1):
            batch_embeddings = self._request_embeddings(batch, batch_index=batch_index)
            if len(batch_embeddings) != len(batch):
                raise EmbeddingClientError(
                    f"Ollama embedding batch {batch_index} returned "
                    f"{len(batch_embeddings)} embeddings for {len(batch)} texts",
                )
            embeddings.extend(batch_embeddings)

        return embeddings

    def _request_embeddings(
        self,
        input_value: str | list[str],
        batch_index: int | None = None,
    ) -> list[list[float]]:
        embed_url = f"{self.base_url}/api/embed"
        payload = {
            "model": self.model,
            "input": input_value,
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(embed_url, json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if batch_index is not None:
                raise EmbeddingClientError(
                    "Ollama embedding batch "
                    f"{batch_index} failed with status {exc.response.status_code}",
                ) from exc
            raise EmbeddingClientError("Ollama embedding request failed") from exc
        except httpx.HTTPError as exc:
            if batch_index is not None:
                raise EmbeddingClientError(
                    f"Ollama embedding batch {batch_index} failed: {exc.__class__.__name__}",
                ) from exc
            raise EmbeddingClientError("Ollama embedding request failed") from exc

        response_payload = response.json()
        embeddings = response_payload.get("embeddings")
        if not isinstance(embeddings, list):
            raise EmbeddingClientError("Ollama embedding response missing embeddings")

        return [_validate_embedding(embedding) for embedding in embeddings]


def _validate_text(text: str) -> None:
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not text.strip():
        raise ValueError("text must not be empty")


def _validate_texts(texts: list[str]) -> None:
    if not texts:
        raise ValueError("texts must not be empty")

    for text in texts:
        _validate_text(text)


def _batch_texts(texts: list[str], batch_size: int) -> list[list[str]]:
    return [texts[index : index + batch_size] for index in range(0, len(texts), batch_size)]


def _validate_embedding(embedding: Any) -> list[float]:
    if not isinstance(embedding, list):
        raise EmbeddingClientError("Ollama embedding response contains invalid embedding")

    try:
        return [float(value) for value in embedding]
    except (TypeError, ValueError) as exc:
        raise EmbeddingClientError("Ollama embedding response contains invalid values") from exc
