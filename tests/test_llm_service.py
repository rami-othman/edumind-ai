from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from app.services.llm.llm_service import generate_answer, get_llm_client
from app.services.llm.ollama_client import LLMClientError, OllamaChatClient


class MockResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://ollama.test/api/chat")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("HTTP error", request=request, response=response)

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeLLMClient:
    def __init__(self) -> None:
        self.system_prompt: str | None = None
        self.user_prompt: str | None = None

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        return "answer from fake client"


def _settings(provider: str = "ollama") -> SimpleNamespace:
    return SimpleNamespace(
        llm_provider=provider,
        ollama_llm_base_url="https://ollama.test",
        ollama_base_url="http://legacy-ollama.test",
        ollama_llm_model="deepseek-v4-pro:cloud",
        ollama_api_key="secret-token",
    )


def test_ollama_chat_client_sends_expected_chat_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_post(
        self: httpx.Client,
        url: str,
        json: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> MockResponse:
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return MockResponse({"message": {"role": "assistant", "content": "إجابة"}, "done": True})

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    client = OllamaChatClient(
        base_url="https://ollama.test",
        model="deepseek-v4-pro:cloud",
        api_key="secret-token",
    )

    assert client.generate("system prompt", "user prompt") == "إجابة"
    assert captured["url"] == "https://ollama.test/api/chat"
    assert captured["json"] == {
        "model": "deepseek-v4-pro:cloud",
        "messages": [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "user prompt"},
        ],
        "stream": False,
    }


def test_ollama_chat_client_uses_authorization_header_when_api_key_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_post(
        self: httpx.Client,
        url: str,
        json: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> MockResponse:
        captured["headers"] = headers
        return MockResponse({"message": {"content": "answer"}, "done": True})

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    OllamaChatClient("https://ollama.test", "model", api_key="secret-token").generate(
        "system",
        "user",
    )

    assert captured["headers"] == {"Authorization": "Bearer secret-token"}


@pytest.mark.parametrize("api_key", [None, ""])
def test_ollama_chat_client_omits_authorization_header_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
    api_key: str | None,
) -> None:
    captured: dict[str, Any] = {}

    def fake_post(
        self: httpx.Client,
        url: str,
        json: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> MockResponse:
        captured["headers"] = headers
        return MockResponse({"message": {"content": "answer"}, "done": True})

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    OllamaChatClient("https://ollama.test", "model", api_key=api_key).generate("system", "user")

    assert captured["headers"] is None


def test_ollama_chat_client_raises_for_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(
        self: httpx.Client,
        url: str,
        json: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> MockResponse:
        return MockResponse({"error": "failed"}, status_code=500)

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    with pytest.raises(LLMClientError, match="Ollama chat request failed"):
        OllamaChatClient("https://ollama.test", "model").generate("system", "user")


def test_ollama_chat_client_raises_for_invalid_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(
        self: httpx.Client,
        url: str,
        json: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> MockResponse:
        return MockResponse({"done": True})

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    with pytest.raises(LLMClientError, match="Ollama chat response missing assistant content"):
        OllamaChatClient("https://ollama.test", "model").generate("system", "user")


def test_ollama_chat_client_rejects_empty_user_prompt() -> None:
    with pytest.raises(ValueError, match="user_prompt must not be empty"):
        OllamaChatClient("https://ollama.test", "model").generate("system", "   ")


def test_get_llm_client_uses_ollama_settings() -> None:
    client = get_llm_client(settings=_settings())

    assert isinstance(client, OllamaChatClient)
    assert client.base_url == "https://ollama.test"
    assert client.model == "deepseek-v4-pro:cloud"
    assert client.api_key == "secret-token"


def test_generate_answer_uses_injected_client() -> None:
    client = FakeLLMClient()

    assert generate_answer("system prompt", "user prompt", client=client) == "answer from fake client"
    assert client.system_prompt == "system prompt"
    assert client.user_prompt == "user prompt"
