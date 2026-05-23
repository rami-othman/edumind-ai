"""Lightweight ChromaDB client and connectivity helpers."""

from __future__ import annotations

from typing import Any

import chromadb
import httpx

from app.config import Settings, get_settings

DEFAULT_TIMEOUT_SECONDS = 3.0


class ChromaVectorStoreError(Exception):
    """Raised when ChromaDB vector store operations fail."""


class ChromaClient:
    """Small wrapper around ChromaDB HTTP collection access."""

    def __init__(
        self,
        host: str,
        port: int,
        collection_name: str,
        distance_function: str = "cosine",
    ) -> None:
        if not host.strip():
            raise ValueError("host must not be empty")
        if port <= 0:
            raise ValueError("port must be greater than 0")
        if not collection_name.strip():
            raise ValueError("collection_name must not be empty")
        if not distance_function.strip():
            raise ValueError("distance_function must not be empty")

        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.distance_function = distance_function
        self._client = chromadb.HttpClient(host=host, port=port)

    def get_or_create_collection(self) -> Any:
        """Return the configured ChromaDB collection, creating it if needed."""

        try:
            return self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self.distance_function},
                embedding_function=None,
            )
        except Exception as exc:  # pragma: no cover - depends on Chroma internals.
            raise ChromaVectorStoreError(
                f"Failed to get or create ChromaDB collection '{self.collection_name}': {exc}",
            ) from exc

    def heartbeat(self) -> bool:
        """Return whether ChromaDB responds to a heartbeat request."""

        try:
            self._client.heartbeat()
            return True
        except Exception as exc:  # pragma: no cover - depends on Chroma internals.
            raise ChromaVectorStoreError(
                f"ChromaDB heartbeat failed for {self.host}:{self.port}: {exc}",
            ) from exc


def build_chroma_client(settings: Settings | None = None) -> ChromaClient:
    """Build a Chroma client from application settings."""

    resolved_settings = settings or get_settings()
    return ChromaClient(
        host=resolved_settings.chroma_host,
        port=resolved_settings.chroma_port,
        collection_name=resolved_settings.chroma_collection_name,
        distance_function=resolved_settings.chroma_distance_function,
    )


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
