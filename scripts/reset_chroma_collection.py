"""Reset the configured ChromaDB collection after retrieval-setting changes."""

from __future__ import annotations

import sys
from pathlib import Path

import chromadb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    collection_name = settings.chroma_collection_name
    client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)

    try:
        client.delete_collection(name=collection_name)
        print(f"Deleted ChromaDB collection: {collection_name}")
    except Exception as exc:
        message = str(exc).lower()
        if "does not exist" not in message and "not found" not in message:
            raise
        print(f"ChromaDB collection did not exist: {collection_name}")

    client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": settings.chroma_distance_function},
        embedding_function=None,
    )
    print(f"Ready ChromaDB collection: {collection_name}")


if __name__ == "__main__":
    main()
