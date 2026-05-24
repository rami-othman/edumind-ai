import pytest

from app.services.ingestion.metadata_builder import ChunkRecord
from app.services.vector_store.vector_store_service import (
    add_chunk_records,
    get_chunks_for_keyword_search,
    query_similar_chunks,
)


class FakeCollection:
    def __init__(self) -> None:
        self.add_call: dict[str, object] | None = None
        self.query_call: dict[str, object] | None = None
        self.get_call: dict[str, object] | None = None

    def add(
        self,
        *,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, object]],
        embeddings: list[list[float]],
    ) -> None:
        self.add_call = {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas,
            "embeddings": embeddings,
        }

    def query(
        self,
        *,
        query_embeddings: list[list[float]],
        n_results: int,
        where: dict[str, object] | None = None,
        include: list[str],
    ) -> dict[str, object]:
        self.query_call = {
            "query_embeddings": query_embeddings,
            "n_results": n_results,
            "where": where,
            "include": include,
        }
        return {
            "ids": [["chunk-1", "chunk-2"]],
            "documents": [["first text", "second text"]],
            "metadatas": [[{"page_number": 1}, {"page_number": 2}]],
            "distances": [[0.1, 0.2]],
        }

    def get(
        self,
        *,
        where: dict[str, object] | None = None,
        limit: int | None = None,
        include: list[str],
    ) -> dict[str, object]:
        self.get_call = {
            "where": where,
            "limit": limit,
            "include": include,
        }
        return {
            "ids": ["chunk-1", "chunk-2"],
            "documents": ["first text", "second text"],
            "metadatas": [{"page_number": 1}, {"page_number": 2}],
        }


class FakeClient:
    def __init__(self, collection: FakeCollection) -> None:
        self.collection = collection

    def get_or_create_collection(self) -> FakeCollection:
        return self.collection


def _record(chunk_id: str = "chunk-1") -> ChunkRecord:
    return ChunkRecord(
        chunk_id=chunk_id,
        text="chunk text",
        metadata={
            "document_id": "document-1",
            "file_name": "book.pdf",
            "page_number": 1,
            "chunk_index": 0,
        },
    )


def test_add_chunk_records_calls_collection_add_with_expected_payload() -> None:
    collection = FakeCollection()
    client = FakeClient(collection)
    records = [_record("chunk-1"), _record("chunk-2")]
    embeddings = [[0.1, 0.2], [0.3, 0.4]]

    stored_count = add_chunk_records(records, embeddings, client)

    assert stored_count == 2
    assert collection.add_call == {
        "ids": ["chunk-1", "chunk-2"],
        "documents": ["chunk text", "chunk text"],
        "metadatas": [
            {
                "document_id": "document-1",
                "file_name": "book.pdf",
                "page_number": 1,
                "chunk_index": 0,
            },
            {
                "document_id": "document-1",
                "file_name": "book.pdf",
                "page_number": 1,
                "chunk_index": 0,
            },
        ],
        "embeddings": embeddings,
    }


def test_add_chunk_records_rejects_empty_records() -> None:
    with pytest.raises(ValueError, match="records must not be empty"):
        add_chunk_records([], [[0.1]], FakeClient(FakeCollection()))


def test_add_chunk_records_rejects_empty_embeddings() -> None:
    with pytest.raises(ValueError, match="embeddings must not be empty"):
        add_chunk_records([_record()], [], FakeClient(FakeCollection()))


def test_add_chunk_records_rejects_mismatched_record_and_embedding_count() -> None:
    with pytest.raises(ValueError, match="records and embeddings must have the same length"):
        add_chunk_records([_record(), _record("chunk-2")], [[0.1]], FakeClient(FakeCollection()))


@pytest.mark.parametrize(
    "embedding",
    [
        [],
        ["0.1"],
        [0.1, None],
    ],
)
def test_add_chunk_records_rejects_invalid_embeddings(embedding: object) -> None:
    with pytest.raises(ValueError, match="embedding must be a non-empty list of numbers"):
        add_chunk_records([_record()], [embedding], FakeClient(FakeCollection()))  # type: ignore[list-item]


def test_query_similar_chunks_calls_collection_query_with_expected_arguments() -> None:
    collection = FakeCollection()
    client = FakeClient(collection)

    query_similar_chunks([0.1, 0.2], client, top_k=2, where={"subject": "physics"})

    assert collection.query_call == {
        "query_embeddings": [[0.1, 0.2]],
        "n_results": 2,
        "where": {"subject": "physics"},
        "include": ["documents", "metadatas", "distances"],
    }


def test_query_similar_chunks_returns_normalized_results() -> None:
    results = query_similar_chunks([0.1, 0.2], FakeClient(FakeCollection()), top_k=2)

    assert results == [
        {
            "id": "chunk-1",
            "text": "first text",
            "metadata": {"page_number": 1},
            "distance": 0.1,
        },
        {
            "id": "chunk-2",
            "text": "second text",
            "metadata": {"page_number": 2},
            "distance": 0.2,
        },
    ]


def test_query_similar_chunks_rejects_invalid_query_embedding() -> None:
    with pytest.raises(ValueError, match="query_embedding must be a non-empty list of numbers"):
        query_similar_chunks([], FakeClient(FakeCollection()))


def test_query_similar_chunks_rejects_invalid_top_k() -> None:
    with pytest.raises(ValueError, match="top_k must be greater than 0"):
        query_similar_chunks([0.1], FakeClient(FakeCollection()), top_k=0)


def test_get_chunks_for_keyword_search_calls_collection_get_with_expected_arguments() -> None:
    collection = FakeCollection()
    client = FakeClient(collection)

    get_chunks_for_keyword_search(
        client,
        where={"subject": "biology"},
        limit=100,
    )

    assert collection.get_call == {
        "where": {"subject": "biology"},
        "limit": 100,
        "include": ["documents", "metadatas"],
    }


def test_get_chunks_for_keyword_search_returns_normalized_chunk_dictionaries() -> None:
    results = get_chunks_for_keyword_search(FakeClient(FakeCollection()))

    assert results == [
        {
            "id": "chunk-1",
            "text": "first text",
            "metadata": {"page_number": 1},
            "distance": None,
        },
        {
            "id": "chunk-2",
            "text": "second text",
            "metadata": {"page_number": 2},
            "distance": None,
        },
    ]
