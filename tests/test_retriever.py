import pytest

from app.services.rag.retriever import RetrievedChunk, retrieve_similar_chunks


class FakeEmbeddingService:
    def __init__(self, embedding: list[float]) -> None:
        self.embedding = embedding
        self.received_question: str | None = None

    def embed_text(self, text: str) -> list[float]:
        self.received_question = text
        return self.embedding


class FakeCollection:
    def __init__(self, results: dict[str, object]) -> None:
        self.results = results
        self.query_call: dict[str, object] | None = None

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
        return self.results


class FakeVectorStoreClient:
    def __init__(self, results: dict[str, object]) -> None:
        self.collection = FakeCollection(results)

    def get_or_create_collection(self) -> FakeCollection:
        return self.collection


def _vector_results() -> dict[str, object]:
    return {
        "ids": [["chunk-1", "chunk-2"]],
        "documents": [["قانون أوم", "شرح المقاومة"]],
        "metadatas": [
            [
                {"file_name": "physics.pdf", "page_number": 45},
                {"file_name": "physics.pdf", "page_number": 46},
            ],
        ],
        "distances": [[0.12, 0.24]],
    }


def test_retrieve_similar_chunks_returns_retrieved_chunks_for_valid_question() -> None:
    chunks = retrieve_similar_chunks(
        "ما هو قانون أوم؟",
        FakeEmbeddingService([0.1, 0.2]),
        FakeVectorStoreClient(_vector_results()),
    )

    assert chunks == [
        RetrievedChunk(
            chunk_id="chunk-1",
            text="قانون أوم",
            metadata={"file_name": "physics.pdf", "page_number": 45},
            distance=0.12,
        ),
        RetrievedChunk(
            chunk_id="chunk-2",
            text="شرح المقاومة",
            metadata={"file_name": "physics.pdf", "page_number": 46},
            distance=0.24,
        ),
    ]


def test_retrieve_similar_chunks_sends_original_question_to_embedding_service() -> None:
    embedding_service = FakeEmbeddingService([0.1, 0.2])

    retrieve_similar_chunks(
        "  ما هو قانون أوم؟  ",
        embedding_service,
        FakeVectorStoreClient(_vector_results()),
    )

    assert embedding_service.received_question == "  ما هو قانون أوم؟  "


def test_retrieve_similar_chunks_passes_embedding_top_k_and_where_to_vector_store() -> None:
    vector_store_client = FakeVectorStoreClient(_vector_results())

    retrieve_similar_chunks(
        "ما هو قانون أوم؟",
        FakeEmbeddingService([0.1, 0.2]),
        vector_store_client,
        top_k=2,
        where={"subject": "physics"},
    )

    assert vector_store_client.collection.query_call == {
        "query_embeddings": [[0.1, 0.2]],
        "n_results": 2,
        "where": {"subject": "physics"},
        "include": ["documents", "metadatas", "distances"],
    }


def test_retrieved_chunk_to_dict_returns_normalized_dictionary() -> None:
    chunk = RetrievedChunk(
        chunk_id="chunk-1",
        text="قانون أوم",
        metadata={"page_number": 45},
        distance=0.12,
    )

    assert chunk.to_dict() == {
        "chunk_id": "chunk-1",
        "text": "قانون أوم",
        "metadata": {"page_number": 45},
        "distance": 0.12,
    }


def test_retrieve_similar_chunks_rejects_empty_question() -> None:
    with pytest.raises(ValueError, match="question must not be empty"):
        retrieve_similar_chunks("   ", FakeEmbeddingService([0.1]), FakeVectorStoreClient({}))


def test_retrieve_similar_chunks_rejects_non_string_question() -> None:
    with pytest.raises(TypeError, match="question must be a string"):
        retrieve_similar_chunks(None, FakeEmbeddingService([0.1]), FakeVectorStoreClient({}))  # type: ignore[arg-type]


def test_retrieve_similar_chunks_rejects_invalid_top_k() -> None:
    with pytest.raises(ValueError, match="top_k must be greater than 0"):
        retrieve_similar_chunks("question", FakeEmbeddingService([0.1]), FakeVectorStoreClient({}), top_k=0)


def test_retrieve_similar_chunks_returns_empty_list_for_empty_results() -> None:
    chunks = retrieve_similar_chunks(
        "question",
        FakeEmbeddingService([0.1]),
        FakeVectorStoreClient(
            {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            },
        ),
    )

    assert chunks == []
