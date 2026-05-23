"""Lightweight Ollama connectivity helpers and chat client."""

from __future__ import annotations

import httpx

DEFAULT_TIMEOUT_SECONDS = 3.0


class LLMClientError(Exception):
    """Raised when LLM generation fails."""


class OllamaChatClient:
    """Client for Ollama chat generation."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        if not base_url.strip():
            raise ValueError("base_url must not be empty")
        if not model.strip():
            raise ValueError("model must not be empty")

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key.strip() if api_key and api_key.strip() else None
        self.timeout_seconds = timeout_seconds

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate an answer from system and user prompts."""

        _validate_prompt(system_prompt, "system_prompt", allow_empty=True)
        _validate_prompt(user_prompt, "user_prompt")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        headers = (
            {"Authorization": f"Bearer {self.api_key}"}
            if self.api_key is not None
            else None
        )

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMClientError("Ollama chat request failed") from exc

        response_payload = response.json()
        message = response_payload.get("message")
        if not isinstance(message, dict):
            raise LLMClientError("Ollama chat response missing assistant content")

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMClientError("Ollama chat response missing assistant content")

        return content


def check_ollama_health(
    *,
    base_url: str,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, str]:
    """Check whether the Ollama API is reachable without generating text."""

    normalized_base_url = base_url.rstrip("/")
    tags_url = f"{normalized_base_url}/api/tags"

    try:
        response = httpx.get(tags_url, timeout=timeout_seconds)
        if response.is_success:
            return {"status": "ok", "url": normalized_base_url}

        return {
            "status": "error",
            "url": normalized_base_url,
            "message": f"Ollama tags endpoint failed with status {response.status_code}",
        }
    except httpx.HTTPError as exc:
        return {
            "status": "error",
            "url": normalized_base_url,
            "message": str(exc),
        }


def _validate_prompt(prompt: str, field_name: str, allow_empty: bool = False) -> None:
    if not isinstance(prompt, str):
        raise TypeError(f"{field_name} must be a string")

    if not allow_empty and not prompt.strip():
        raise ValueError(f"{field_name} must not be empty")
