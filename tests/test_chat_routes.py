from typing import Any

from fastapi.testclient import TestClient

from app.dependencies import get_rag_service
from app.main import app
from app.services.rag.rag_service import RagAnswer


class FakeRagService:
    def __init__(self) -> None:
        self.received_question: str | None = None
        self.received_top_k: int | None = None
        self.received_where: dict[str, object] | None = None

    def answer_question(
        self,
        question: str,
        top_k: int = 5,
        where: dict[str, object] | None = None,
    ) -> RagAnswer:
        self.received_question = question
        self.received_top_k = top_k
        self.received_where = where
        return RagAnswer(
            answer="قانون أوم يربط بين التوتر والتيار والمقاومة.",
            sources=[
                {
                    "chunk_id": "physics_book_2026:chunk:12",
                    "file_name": "physics.pdf",
                    "page_number": 45,
                    "subject": "physics",
                    "grade": "12",
                    "chunk_index": 12,
                    "distance": 0.123,
                },
            ],
            retrieved_chunks=[
                {
                    "chunk_id": "physics_book_2026:chunk:12",
                    "text": "قانون أوم يربط بين التوتر والتيار والمقاومة.",
                    "metadata": {"file_name": "physics.pdf", "page_number": 45},
                    "distance": 0.123,
                },
            ],
        )


class ErrorRagService:
    def __init__(self, exc: Exception) -> None:
        self.exc = exc

    def answer_question(
        self,
        question: str,
        top_k: int = 5,
        where: dict[str, object] | None = None,
    ) -> RagAnswer:
        raise self.exc


def _client_with_rag_service(rag_service: Any) -> TestClient:
    app.dependency_overrides[get_rag_service] = lambda: rag_service
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_chat_ask_returns_answer_sources_and_retrieved_chunks() -> None:
    client = _client_with_rag_service(FakeRagService())

    response = client.post(
        "/api/v1/chat/ask",
        json={
            "question": "ما هو قانون أوم؟",
            "top_k": 5,
            "filters": {"subject": "physics", "grade": "12"},
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "قانون أوم يربط بين التوتر والتيار والمقاومة.",
        "sources": [
            {
                "chunk_id": "physics_book_2026:chunk:12",
                "file_name": "physics.pdf",
                "page_number": 45,
                "subject": "physics",
                "grade": "12",
                "chunk_index": 12,
                "distance": 0.123,
            },
        ],
        "retrieved_chunks": [
            {
                "chunk_id": "physics_book_2026:chunk:12",
                "text": "قانون أوم يربط بين التوتر والتيار والمقاومة.",
                "metadata": {"file_name": "physics.pdf", "page_number": 45},
                "distance": 0.123,
            },
        ],
    }


def test_chat_ask_passes_question_top_k_and_filters_to_rag_service() -> None:
    rag_service = FakeRagService()
    client = _client_with_rag_service(rag_service)

    response = client.post(
        "/api/v1/chat/ask",
        json={
            "question": "ما هو قانون أوم؟",
            "top_k": 3,
            "filters": {"subject": "physics"},
        },
    )

    assert response.status_code == 200
    assert rag_service.received_question == "ما هو قانون أوم؟"
    assert rag_service.received_top_k == 3
    assert rag_service.received_where == {"subject": "physics"}


def test_chat_ask_preserves_arabic_question() -> None:
    rag_service = FakeRagService()
    client = _client_with_rag_service(rag_service)

    response = client.post(
        "/api/v1/chat/ask",
        json={"question": "اشرح قانون أوم بالعربية"},
    )

    assert response.status_code == 200
    assert rag_service.received_question == "اشرح قانون أوم بالعربية"


def test_chat_ask_rejects_empty_question() -> None:
    client = _client_with_rag_service(FakeRagService())

    response = client.post("/api/v1/chat/ask", json={"question": "   "})

    assert response.status_code == 422


def test_chat_ask_rejects_invalid_top_k() -> None:
    client = _client_with_rag_service(FakeRagService())

    response = client.post(
        "/api/v1/chat/ask",
        json={"question": "ما هو قانون أوم؟", "top_k": 0},
    )

    assert response.status_code == 422


def test_chat_ask_returns_400_for_rag_value_error() -> None:
    client = _client_with_rag_service(ErrorRagService(ValueError("invalid question")))

    response = client.post("/api/v1/chat/ask", json={"question": "ما هو قانون أوم؟"})

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid question"}


def test_chat_ask_returns_500_for_unexpected_rag_error() -> None:
    client = _client_with_rag_service(ErrorRagService(RuntimeError("boom")))

    response = client.post("/api/v1/chat/ask", json={"question": "ما هو قانون أوم؟"})

    assert response.status_code == 500
    assert response.json() == {"detail": "RAG service failed"}


def test_health_endpoint_still_works() -> None:
    client = _client_with_rag_service(FakeRagService())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
