"""Lightweight ChromaDB connectivity helpers."""

import httpx

DEFAULT_TIMEOUT_SECONDS = 3.0


def check_chroma_health(
    *,
    host: str,
    port: int,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, str]:
    """Check whether ChromaDB is reachable without creating collections."""

    base_url = f"http://{host}:{port}"
    healthcheck_url = f"{base_url}/api/v2/healthcheck"
    heartbeat_url = f"{base_url}/api/v2/heartbeat"

    try:
        healthcheck_response = httpx.get(healthcheck_url, timeout=timeout_seconds)
        if healthcheck_response.is_success:
            return {"status": "ok", "url": base_url}

        heartbeat_response = httpx.get(heartbeat_url, timeout=timeout_seconds)
        if heartbeat_response.is_success:
            return {"status": "ok", "url": base_url}

        return {
            "status": "error",
            "url": base_url,
            "message": (
                "ChromaDB healthcheck failed "
                f"with status {healthcheck_response.status_code}; "
                f"heartbeat failed with status {heartbeat_response.status_code}"
            ),
        }
    except httpx.HTTPError as exc:
        return {
            "status": "error",
            "url": base_url,
            "message": str(exc),
        }
