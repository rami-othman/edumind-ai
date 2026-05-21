from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from app.services.embeddings.embedding_client import (
    EmbeddingClientError,
    OllamaEmbeddingClient,
)
from app.services.embeddings.embedding_service import (
    UnsupportedEmbeddingProviderError,
    embed_text,
    embed_texts,
)


class MockResponse:
    def __init__(
        self,
        payload: dict[str, Any],
        status_code: int = 200,
    ) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://ollama.test/api/embed")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("HTTP error", request=request, response=response)

    def json(self) -> dict[str, Any]:
        return self._payload


def _settings(provider: str = "ollama") -> SimpleNamespace:
    return SimpleNamespace(
        embedding_provider=provider,
        ollama_base_url="http://ollama.test",
        ollama_embedding_model="nomic-embed-text",
    )


def test_embed_text_returns_embedding_from_mocked_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(self: httpx.Client, url: str, json: dict[str, Any]) -> MockResponse:
        assert url == "http://ollama.test/api/embed"
        assert json == {"model": "nomic-embed-text", "input": "hello"}
        return MockResponse({"embeddings": [[0.1, 0.2, 0.3]]})

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    assert embed_text("hello", settings=_settings()) == [0.1, 0.2, 0.3]


def test_embed_texts_returns_embeddings_for_multiple_texts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(self: httpx.Client, url: str, json: dict[str, Any]) -> MockResponse:
        assert json["input"] == ["first", "second"]
        return MockResponse({"embeddings": [[0.1, 0.2], [0.3, 0.4]]})

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    assert embed_texts(["first", "second"], settings=_settings()) == [
        [0.1, 0.2],
        [0.3, 0.4],
    ]


def test_embed_text_rejects_empty_text() -> None:
    client = OllamaEmbeddingClient("http://ollama.test", "nomic-embed-text")

    with pytest.raises(ValueError, match="text must not be empty"):
        client.embed_text("   ")


def test_embed_texts_rejects_empty_list() -> None:
    client = OllamaEmbeddingClient("http://ollama.test", "nomic-embed-text")

    with pytest.raises(ValueError, match="texts must not be empty"):
        client.embed_texts([])


def test_embed_text_rejects_non_string_text() -> None:
    client = OllamaEmbeddingClient("http://ollama.test", "nomic-embed-text")

    with pytest.raises(TypeError, match="text must be a string"):
        client.embed_text(None)  # type: ignore[arg-type]


def test_unsupported_provider_raises_error() -> None:
    with pytest.raises(UnsupportedEmbeddingProviderError, match="Unsupported embedding provider"):
        embed_text("hello", settings=_settings(provider="google"))


def test_http_error_from_ollama_raises_embedding_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(self: httpx.Client, url: str, json: dict[str, Any]) -> MockResponse:
        return MockResponse({"error": "model missing"}, status_code=500)

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    with pytest.raises(EmbeddingClientError, match="Ollama embedding request failed"):
        embed_text("hello", settings=_settings())


def test_invalid_ollama_response_without_embeddings_raises_embedding_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(self: httpx.Client, url: str, json: dict[str, Any]) -> MockResponse:
        return MockResponse({"embedding": [0.1, 0.2]})

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    with pytest.raises(EmbeddingClientError, match="Ollama embedding response missing embeddings"):
        embed_text("hello", settings=_settings())
