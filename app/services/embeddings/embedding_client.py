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
        timeout_seconds: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

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

        return self._request_embeddings(texts)

    def _request_embeddings(self, input_value: str | list[str]) -> list[list[float]]:
        embed_url = f"{self.base_url}/api/embed"
        payload = {
            "model": self.model,
            "input": input_value,
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(embed_url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
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


def _validate_embedding(embedding: Any) -> list[float]:
    if not isinstance(embedding, list):
        raise EmbeddingClientError("Ollama embedding response contains invalid embedding")

    try:
        return [float(value) for value in embedding]
    except (TypeError, ValueError) as exc:
        raise EmbeddingClientError("Ollama embedding response contains invalid values") from exc
