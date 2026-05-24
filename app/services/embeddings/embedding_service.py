"""Provider-level embedding service abstraction."""

from __future__ import annotations

from app.config import Settings, get_settings
from app.services.embeddings.embedding_client import OllamaEmbeddingClient


class UnsupportedEmbeddingProviderError(Exception):
    """Raised when the configured embedding provider is not implemented."""


def get_embedding_client(settings: Settings | None = None) -> OllamaEmbeddingClient:
    """Return the configured embedding client."""
    active_settings = settings or get_settings()
    provider = active_settings.embedding_provider.lower()

    if provider == "ollama":
        return OllamaEmbeddingClient(
            base_url=getattr(active_settings, "ollama_embedding_base_url", None)
            or active_settings.ollama_base_url,
            model=active_settings.ollama_embedding_model,
            timeout_seconds=getattr(
                active_settings,
                "ollama_embedding_timeout_seconds",
                180,
            ),
            batch_size=getattr(active_settings, "embedding_batch_size", 32),
        )

    # TODO: Add a Google embedding provider in a later milestone.
    raise UnsupportedEmbeddingProviderError(f"Unsupported embedding provider: {provider}")


def embed_text(text: str, settings: Settings | None = None) -> list[float]:
    """Embed one text value using the configured provider."""
    return get_embedding_client(settings).embed_text(text)


def embed_texts(texts: list[str], settings: Settings | None = None) -> list[list[float]]:
    """Embed multiple text values using the configured provider."""
    return get_embedding_client(settings).embed_texts(texts)
