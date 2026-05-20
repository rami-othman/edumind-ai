"""Lightweight Ollama connectivity helpers."""

import httpx

DEFAULT_TIMEOUT_SECONDS = 3.0


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
