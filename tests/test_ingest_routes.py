from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.config import Settings
from app.dependencies import get_app_settings, get_ingestion_service, get_rag_service
from app.main import app
from app.services.ingestion.ingestion_service import IngestionStorageResult
from app.services.rag.rag_service import RagAnswer


class FakeIngestionService:
    def __init__(self, failing_names: set[str] | None = None) -> None:
        self.failing_names = failing_names or set()
        self.calls: list[dict[str, Any]] = []

    def ingest_pdf(
        self,
        *,
        file_path: str | Path,
        document_metadata: Any,
        chunk_size: int,
        chunk_overlap: int,
    ) -> IngestionStorageResult:
        self.calls.append(
            {
                "file_path": Path(file_path),
                "metadata": document_metadata,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            },
        )
        if Path(file_path).name in self.failing_names:
            raise ValueError("failed to ingest test file")

        return IngestionStorageResult(
            document_id=document_metadata.document_id,
            file_name=document_metadata.file_name,
            source_path=str(file_path),
            page_count=2,
            total_chunks=3,
            stored_chunks=3,
            empty_pages=[2],
        )


class FakeRagService:
    def answer_question(
        self,
        question: str,
        top_k: int = 5,
        where: dict[str, object] | None = None,
    ) -> RagAnswer:
        return RagAnswer(answer="answer", sources=[], retrieved_chunks=[])


def _client(
    ingestion_service: FakeIngestionService,
    books_dir: Path,
) -> TestClient:
    app.dependency_overrides[get_ingestion_service] = lambda: ingestion_service
    app.dependency_overrides[get_rag_service] = lambda: FakeRagService()
    app.dependency_overrides[get_app_settings] = lambda: Settings(
        books_dir=str(books_dir),
        books_grade="12",
        books_language="arabic",
        books_source_type="admin_uploaded_book",
        chunk_size=900,
        chunk_overlap=120,
    )
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def _write_pdf(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4 fake pdf bytes")
    return path


def test_pdf_ingest_uses_default_books_dir_from_settings(tmp_path: Path) -> None:
    books_dir = tmp_path / "data" / "uploads" / "books"
    _write_pdf(books_dir / "physics" / "physics bac 2026.pdf")
    ingestion_service = FakeIngestionService()
    client = _client(ingestion_service, books_dir)

    response = client.post("/api/v1/ingest/pdf", json={})

    assert response.status_code == 200
    assert response.json()["books_dir"] == str(books_dir)
    assert ingestion_service.calls[0]["file_path"] == books_dir / "physics" / "physics bac 2026.pdf"


def test_pdf_ingest_uses_custom_books_dir_from_body(tmp_path: Path) -> None:
    default_books_dir = tmp_path / "data" / "uploads" / "books"
    custom_books_dir = tmp_path / "data" / "custom_books"
    _write_pdf(custom_books_dir / "math" / "math bac part1 2026.pdf")
    ingestion_service = FakeIngestionService()
    client = _client(ingestion_service, default_books_dir)

    response = client.post("/api/v1/ingest/pdf", json={"books_dir": str(custom_books_dir)})

    assert response.status_code == 200
    assert response.json()["books_dir"] == str(custom_books_dir)
    assert ingestion_service.calls[0]["file_path"] == custom_books_dir / "math" / "math bac part1 2026.pdf"


def test_pdf_ingest_finds_pdf_files_recursively(tmp_path: Path) -> None:
    books_dir = tmp_path / "data" / "uploads" / "books"
    _write_pdf(books_dir / "physics" / "physics.pdf")
    _write_pdf(books_dir / "math" / "nested" / "algebra.pdf")
    ingestion_service = FakeIngestionService()
    client = _client(ingestion_service, books_dir)

    response = client.post("/api/v1/ingest/pdf", json={})

    assert response.status_code == 200
    assert response.json()["total_files_found"] == 2
    assert len(ingestion_service.calls) == 2


def test_pdf_ingest_infers_subject_from_parent_folder(tmp_path: Path) -> None:
    books_dir = tmp_path / "data" / "uploads" / "books"
    _write_pdf(books_dir / "biology" / "biology bac 2026.pdf")
    ingestion_service = FakeIngestionService()
    client = _client(ingestion_service, books_dir)

    response = client.post("/api/v1/ingest/pdf", json={})

    assert response.status_code == 200
    assert ingestion_service.calls[0]["metadata"].subject == "biology"
    assert response.json()["results"][0]["subject"] == "biology"


def test_pdf_ingest_uses_grade_language_source_type_and_chunks_from_settings(tmp_path: Path) -> None:
    books_dir = tmp_path / "data" / "uploads" / "books"
    _write_pdf(books_dir / "physics" / "physics.pdf")
    ingestion_service = FakeIngestionService()
    client = _client(ingestion_service, books_dir)

    response = client.post(
        "/api/v1/ingest/pdf",
        json={"chunk_size": 10, "chunk_overlap": 5, "grade": "ignored"},
    )

    assert response.status_code == 200
    call = ingestion_service.calls[0]
    assert call["metadata"].grade == "12"
    assert call["metadata"].language == "arabic"
    assert call["metadata"].source_type == "admin_uploaded_book"
    assert call["chunk_size"] == 900
    assert call["chunk_overlap"] == 120


def test_pdf_ingest_returns_successful_summaries(tmp_path: Path) -> None:
    books_dir = tmp_path / "data" / "uploads" / "books"
    _write_pdf(books_dir / "physics" / "physics bac 2026.pdf")
    client = _client(FakeIngestionService(), books_dir)

    response = client.post("/api/v1/ingest/pdf", json={})

    assert response.status_code == 200
    assert response.json()["results"] == [
        {
            "document_id": "physics_physics_bac_2026",
            "file_name": "physics bac 2026.pdf",
            "source_path": str(books_dir / "physics" / "physics bac 2026.pdf"),
            "subject": "physics",
            "grade": "12",
            "page_count": 2,
            "total_chunks": 3,
            "stored_chunks": 3,
            "empty_pages": [2],
        },
    ]


def test_pdf_ingest_collects_per_file_errors_without_failing_whole_request(tmp_path: Path) -> None:
    books_dir = tmp_path / "data" / "uploads" / "books"
    _write_pdf(books_dir / "physics" / "good.pdf")
    bad_pdf = _write_pdf(books_dir / "math" / "bad.pdf")
    client = _client(FakeIngestionService(failing_names={"bad.pdf"}), books_dir)

    response = client.post("/api/v1/ingest/pdf", json={})

    assert response.status_code == 200
    assert response.json()["successful_files"] == 1
    assert response.json()["failed_files"] == 1
    assert response.json()["errors"] == [
        {
            "file_path": str(bad_pdf),
            "error": "failed to ingest test file",
        },
    ]


def test_pdf_ingest_returns_400_for_missing_directory(tmp_path: Path) -> None:
    books_dir = tmp_path / "data" / "uploads" / "books"
    client = _client(FakeIngestionService(), books_dir)

    response = client.post("/api/v1/ingest/pdf", json={})

    assert response.status_code == 400
    assert response.json() == {"detail": "Books directory does not exist"}


def test_pdf_ingest_returns_400_for_directory_with_no_pdfs(tmp_path: Path) -> None:
    books_dir = tmp_path / "data" / "uploads" / "books"
    books_dir.mkdir(parents=True)
    client = _client(FakeIngestionService(), books_dir)

    response = client.post("/api/v1/ingest/pdf", json={})

    assert response.status_code == 400
    assert response.json() == {"detail": "No PDF files found in books directory"}


def test_pdf_ingest_returns_400_for_unsafe_path(tmp_path: Path) -> None:
    books_dir = tmp_path / "data" / "uploads" / "books"
    books_dir.mkdir(parents=True)
    client = _client(FakeIngestionService(), books_dir)

    response = client.post("/api/v1/ingest/pdf", json={"books_dir": "../secrets"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Unsafe books directory path"}


def test_health_and_chat_routes_still_work(tmp_path: Path) -> None:
    client = _client(FakeIngestionService(), tmp_path / "data" / "uploads" / "books")

    health_response = client.get("/health")
    chat_response = client.post("/api/v1/chat/ask", json={"question": "ما هو قانون أوم؟"})

    assert health_response.status_code == 200
    assert chat_response.status_code == 200
