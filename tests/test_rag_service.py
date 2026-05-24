import pytest

from app.services.rag.rag_service import RagAnswer, answer_question_with_rag


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
        return {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }


class FakeVectorStoreClient:
    def __init__(self, results: dict[str, object]) -> None:
        self.collection = FakeCollection(results)

    def get_or_create_collection(self) -> FakeCollection:
        return self.collection


class FakeLLMService:
    def __init__(self, answer: str = "الإجابة النهائية") -> None:
        self.answer = answer
        self.system_prompt: str | None = None
        self.user_prompt: str | None = None

    def generate_answer(self, system_prompt: str, user_prompt: str) -> str:
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        return self.answer


def _vector_results() -> dict[str, object]:
    return {
        "ids": [["physics_book_2026:chunk:12"]],
        "documents": [["قانون أوم يربط بين التوتر والتيار والمقاومة."]],
        "metadatas": [
            [
                {
                    "file_name": "physics.pdf",
                    "page_number": 45,
                    "subject": "physics",
                    "chunk_index": 12,
                },
            ],
        ],
        "distances": [[0.123]],
    }


def _empty_vector_results() -> dict[str, object]:
    return {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }


def test_answer_question_with_rag_returns_rag_answer_for_valid_question() -> None:
    result = answer_question_with_rag(
        question="ما هو قانون أوم؟",
        embedding_service=FakeEmbeddingService([0.1, 0.2]),
        vector_store_client=FakeVectorStoreClient(_vector_results()),
        llm_service=FakeLLMService("قانون أوم يشرح العلاقة بين التوتر والتيار والمقاومة."),
    )

    assert result == RagAnswer(
        answer="قانون أوم يشرح العلاقة بين التوتر والتيار والمقاومة.",
        sources=[
            {
                "chunk_id": "physics_book_2026:chunk:12",
                "distance": 0.123,
                "file_name": "physics.pdf",
                "page_number": 45,
                "subject": "physics",
                "chunk_index": 12,
            },
        ],
        retrieved_chunks=[
            {
                "chunk_id": "physics_book_2026:chunk:12",
                "text": "قانون أوم يربط بين التوتر والتيار والمقاومة.",
                "metadata": {
                    "file_name": "physics.pdf",
                    "page_number": 45,
                    "subject": "physics",
                    "chunk_index": 12,
                },
                "distance": 0.123,
            },
        ],
    )


def test_answer_question_with_rag_passes_question_top_k_and_where_to_retriever_flow() -> None:
    embedding_service = FakeEmbeddingService([0.1, 0.2])
    vector_store_client = FakeVectorStoreClient(_vector_results())

    answer_question_with_rag(
        question="ما هو قانون أوم؟",
        embedding_service=embedding_service,
        vector_store_client=vector_store_client,
        llm_service=FakeLLMService(),
        top_k=3,
        where={"subject": "physics"},
    )

    assert embedding_service.received_question == "\u0645\u0627 \u0647\u0648 \u0642\u0627\u0646\u0648\u0646 \u0627\u0648\u0645\u061f"
    assert vector_store_client.collection.query_call == {
        "query_embeddings": [[0.1, 0.2]],
        "n_results": 3,
        "where": {"subject": "physics"},
        "include": ["documents", "metadatas", "distances"],
    }


def test_answer_question_with_rag_sends_prompts_to_llm_service() -> None:
    llm_service = FakeLLMService()

    answer_question_with_rag(
        question="ما هو قانون أوم؟",
        embedding_service=FakeEmbeddingService([0.1, 0.2]),
        vector_store_client=FakeVectorStoreClient(_vector_results()),
        llm_service=llm_service,
    )

    assert llm_service.system_prompt is not None
    assert "استخدم السياق المقدم فقط" in llm_service.system_prompt
    assert llm_service.user_prompt is not None
    assert "ما هو قانون أوم؟" in llm_service.user_prompt
    assert "قانون أوم يربط بين التوتر والتيار والمقاومة." in llm_service.user_prompt


def test_answer_question_with_rag_empty_retrieval_still_calls_llm_with_fallback_prompt() -> None:
    llm_service = FakeLLMService("لا أملك معلومات كافية من المحتوى المتوفر للإجابة بدقة.")

    result = answer_question_with_rag(
        question="ما هو قانون أوم؟",
        embedding_service=FakeEmbeddingService([0.1]),
        vector_store_client=FakeVectorStoreClient(_empty_vector_results()),
        llm_service=llm_service,
    )

    assert result.answer == "لا أملك معلومات كافية من المحتوى المتوفر للإجابة بدقة."
    assert result.sources == []
    assert result.retrieved_chunks == []
    assert llm_service.user_prompt is not None
    assert "لا يوجد سياق مسترجع ذو صلة." in llm_service.user_prompt
    assert "لا أملك معلومات كافية من المحتوى المتوفر للإجابة بدقة." in llm_service.user_prompt


def test_answer_question_with_rag_rejects_empty_question() -> None:
    with pytest.raises(ValueError, match="question must not be empty"):
        answer_question_with_rag(
            question="   ",
            embedding_service=FakeEmbeddingService([0.1]),
            vector_store_client=FakeVectorStoreClient(_empty_vector_results()),
            llm_service=FakeLLMService(),
        )


def test_answer_question_with_rag_rejects_non_string_question() -> None:
    with pytest.raises(TypeError, match="question must be a string"):
        answer_question_with_rag(
            question=None,  # type: ignore[arg-type]
            embedding_service=FakeEmbeddingService([0.1]),
            vector_store_client=FakeVectorStoreClient(_empty_vector_results()),
            llm_service=FakeLLMService(),
        )
