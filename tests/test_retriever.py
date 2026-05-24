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
    def __init__(
        self,
        results: dict[str, object],
        keyword_results: dict[str, object] | None = None,
    ) -> None:
        self.results = results
        self.keyword_results = keyword_results or {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }
        self.query_call: dict[str, object] | None = None
        self.get_call: dict[str, object] | None = None

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
        return self.keyword_results


class FakeVectorStoreClient:
    def __init__(
        self,
        results: dict[str, object],
        keyword_results: dict[str, object] | None = None,
    ) -> None:
        self.collection = FakeCollection(results, keyword_results)

    def get_or_create_collection(self) -> FakeCollection:
        return self.collection


def _vector_results() -> dict[str, object]:
    return {
        "ids": [["chunk-1", "chunk-2"]],
        "documents": [["\u0642\u0627\u0646\u0648\u0646 \u0627\u0648\u0645", "\u0634\u0631\u062d \u0627\u0644\u0645\u0642\u0627\u0648\u0645\u0629"]],
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
        "\u0645\u0627 \u0647\u0648 \u0642\u0627\u0646\u0648\u0646 \u0627\u0648\u0645\u061f",
        FakeEmbeddingService([0.1, 0.2]),
        FakeVectorStoreClient(_vector_results()),
        retrieval_mode="vector",
    )

    assert chunks == [
        RetrievedChunk(
            chunk_id="chunk-1",
            text="\u0642\u0627\u0646\u0648\u0646 \u0627\u0648\u0645",
            metadata={"file_name": "physics.pdf", "page_number": 45},
            distance=0.12,
        ),
        RetrievedChunk(
            chunk_id="chunk-2",
            text="\u0634\u0631\u062d \u0627\u0644\u0645\u0642\u0627\u0648\u0645\u0629",
            metadata={"file_name": "physics.pdf", "page_number": 46},
            distance=0.24,
        ),
    ]


def test_retrieve_similar_chunks_sends_normalized_question_to_embedding_service() -> None:
    embedding_service = FakeEmbeddingService([0.1, 0.2])

    retrieve_similar_chunks(
        "  \u0645\u0627 \u0647\u0648 \u0642\u0627\u0646\u0648\u0646 \u0623\u0648\u0645\u061f  ",
        embedding_service,
        FakeVectorStoreClient(_vector_results()),
        retrieval_mode="vector",
    )

    assert embedding_service.received_question == (
        "\u0645\u0627 \u0647\u0648 \u0642\u0627\u0646\u0648\u0646 \u0627\u0648\u0645\u061f"
    )


def test_retrieve_similar_chunks_passes_embedding_top_k_and_where_to_vector_store() -> None:
    vector_store_client = FakeVectorStoreClient(_vector_results())

    retrieve_similar_chunks(
        "\u0645\u0627 \u0647\u0648 \u0642\u0627\u0646\u0648\u0646 \u0627\u0648\u0645\u061f",
        FakeEmbeddingService([0.1, 0.2]),
        vector_store_client,
        top_k=2,
        where={"subject": "physics"},
        retrieval_mode="vector",
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
        text="\u0642\u0627\u0646\u0648\u0646 \u0627\u0648\u0645",
        metadata={"page_number": 45},
        distance=0.12,
    )

    assert chunk.to_dict() == {
        "chunk_id": "chunk-1",
        "text": "\u0642\u0627\u0646\u0648\u0646 \u0627\u0648\u0645",
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
        retrieval_mode="vector",
    )

    assert chunks == []


def test_retrieve_similar_chunks_vector_only_mode_returns_vector_results() -> None:
    chunks = retrieve_similar_chunks(
        "\u0645\u0627 \u0647\u0648 \u0642\u0627\u0646\u0648\u0646 \u0627\u0648\u0645\u061f",
        FakeEmbeddingService([0.1, 0.2]),
        FakeVectorStoreClient(
            _vector_results(),
            keyword_results={
                "ids": ["keyword-1"],
                "documents": ["keyword text"],
                "metadatas": [{"page_number": 9}],
            },
        ),
        retrieval_mode="vector",
    )

    assert [chunk.chunk_id for chunk in chunks] == ["chunk-1", "chunk-2"]


def test_retrieve_similar_chunks_hybrid_mode_includes_keyword_matched_chunks() -> None:
    chunks = retrieve_similar_chunks(
        "\u0643\u064a\u0641 \u064a\u062d\u062f\u062b \u0627\u0644\u0627\u0646\u0642\u0633\u0627\u0645 \u0627\u0644\u0645\u0646\u0635\u0641\u061f",
        FakeEmbeddingService([0.1, 0.2]),
        FakeVectorStoreClient(
            _vector_results(),
            keyword_results={
                "ids": ["biology-1"],
                "documents": [
                    "\u064a\u062d\u062f\u062b \u0627\u0644\u0627\u0646\u0642\u0633\u0627\u0645 \u0627\u0644\u0645\u0646\u0635\u0641 \u0641\u064a \u0627\u0644\u062e\u0644\u064a\u0629",
                ],
                "metadatas": [{"subject": "biology"}],
            },
        ),
        top_k=3,
        retrieval_mode="hybrid",
    )

    assert "biology-1" in [chunk.chunk_id for chunk in chunks]


def test_retrieve_similar_chunks_hybrid_mode_deduplicates_vector_and_keyword_results() -> None:
    chunks = retrieve_similar_chunks(
        "\u0645\u0627 \u0627\u0647\u0645\u064a\u0629 \u0627\u0644\u0627\u0646\u0642\u0633\u0627\u0645\u061f",
        FakeEmbeddingService([0.1, 0.2]),
        FakeVectorStoreClient(
            _vector_results(),
            keyword_results={
                "ids": ["chunk-1"],
                "documents": ["\u0627\u0647\u0645\u064a\u0629 \u0627\u0644\u0627\u0646\u0642\u0633\u0627\u0645"],
                "metadatas": [{"subject": "biology"}],
            },
        ),
        retrieval_mode="hybrid",
    )

    assert [chunk.chunk_id for chunk in chunks].count("chunk-1") == 1


def test_retrieve_similar_chunks_hybrid_mode_prefers_strong_keyword_matches() -> None:
    chunks = retrieve_similar_chunks(
        "\u0627\u0644\u0627\u0646\u0642\u0633\u0627\u0645 \u0627\u0644\u0645\u0646\u0635\u0641 \u0627\u0644\u062e\u0644\u064a\u0629",
        FakeEmbeddingService([0.1, 0.2]),
        FakeVectorStoreClient(
            _vector_results(),
            keyword_results={
                "ids": ["biology-strong"],
                "documents": [
                    "\u0627\u0644\u0627\u0646\u0642\u0633\u0627\u0645 \u0627\u0644\u0645\u0646\u0635\u0641 \u064a\u062d\u062f\u062b \u0641\u064a \u0627\u0644\u062e\u0644\u064a\u0629",
                ],
                "metadatas": [{"subject": "biology"}],
            },
        ),
        top_k=3,
        retrieval_mode="hybrid",
    )

    assert chunks[0].chunk_id == "biology-strong"


def test_retrieve_similar_chunks_hybrid_mode_respects_top_k() -> None:
    chunks = retrieve_similar_chunks(
        "\u0627\u0644\u0627\u0646\u0642\u0633\u0627\u0645 \u0627\u0644\u0645\u0646\u0635\u0641 \u0627\u0644\u062e\u0644\u064a\u0629",
        FakeEmbeddingService([0.1, 0.2]),
        FakeVectorStoreClient(
            _vector_results(),
            keyword_results={
                "ids": ["biology-1", "biology-2"],
                "documents": [
                    "\u0627\u0644\u0627\u0646\u0642\u0633\u0627\u0645 \u0627\u0644\u0645\u0646\u0635\u0641",
                    "\u0627\u0644\u062e\u0644\u064a\u0629 \u0648\u0627\u0644\u0646\u0645\u0648",
                ],
                "metadatas": [{"subject": "biology"}, {"subject": "biology"}],
            },
        ),
        top_k=2,
        retrieval_mode="hybrid",
    )

    assert len(chunks) == 2
