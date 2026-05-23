from pathlib import Path

import fitz
import pytest

from app.services.ingestion.ingestion_service import ingest_pdf_to_vector_store
from app.services.ingestion.metadata_builder import ChunkRecord, DocumentMetadata


class FakeEmbeddingService:
    def __init__(self, embeddings: list[list[float]]) -> None:
        self.embeddings = embeddings
        self.received_texts: list[str] | None = None
        self.called = False

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.called = True
        self.received_texts = texts
        return self.embeddings


class FakeCollection:
    def __init__(self) -> None:
        self.add_call: dict[str, object] | None = None

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


class FakeVectorStoreClient:
    def __init__(self) -> None:
        self.collection = FakeCollection()
        self.called = False

    def get_or_create_collection(self) -> FakeCollection:
        self.called = True
        return self.collection


def _create_test_pdf(path: Path, page_texts: list[str]) -> None:
    document = fitz.open()
    try:
        for text in page_texts:
            page = document.new_page()
            if text:
                page.insert_text((72, 72), text)
        document.save(path)
    finally:
        document.close()


def _document_metadata(pdf_path: Path) -> DocumentMetadata:
    return DocumentMetadata(
        document_id="physics_book_2026",
        file_name=pdf_path.name,
        source_path=str(pdf_path),
        grade="12",
        subject="physics",
        unit="electricity",
    )


def test_ingest_pdf_to_vector_store_stores_generated_pdf_chunks(tmp_path: Path) -> None:
    pdf_path = tmp_path / "physics.pdf"
    _create_test_pdf(pdf_path, ["First page text", "Second page text"])
    embedding_service = FakeEmbeddingService([[0.1, 0.2], [0.3, 0.4]])
    vector_store_client = FakeVectorStoreClient()

    result = ingest_pdf_to_vector_store(
        pdf_path,
        _document_metadata(pdf_path),
        embedding_service,
        vector_store_client,
    )

    assert result.document_id == "physics_book_2026"
    assert result.file_name == "physics.pdf"
    assert result.source_path == str(pdf_path)
    assert result.page_count == 2
    assert result.total_chunks == 2
    assert result.stored_chunks == 2
    assert result.empty_pages == []


def test_ingest_pdf_to_vector_store_sends_chunk_texts_to_embedding_service(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "texts.pdf"
    _create_test_pdf(pdf_path, ["  First    page text  ", "Second page text"])
    embedding_service = FakeEmbeddingService([[0.1], [0.2]])

    ingest_pdf_to_vector_store(
        pdf_path,
        _document_metadata(pdf_path),
        embedding_service,
        FakeVectorStoreClient(),
    )

    assert embedding_service.received_texts == ["First page text", "Second page text"]


def test_ingest_pdf_to_vector_store_sends_records_and_embeddings_to_vector_store(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "store.pdf"
    _create_test_pdf(pdf_path, ["First page text", "Second page text"])
    embeddings = [[0.1, 0.2], [0.3, 0.4]]
    vector_store_client = FakeVectorStoreClient()

    ingest_pdf_to_vector_store(
        pdf_path,
        _document_metadata(pdf_path),
        FakeEmbeddingService(embeddings),
        vector_store_client,
    )

    add_call = vector_store_client.collection.add_call
    assert add_call is not None
    assert add_call["ids"] == [
        "physics_book_2026:chunk:0",
        "physics_book_2026:chunk:1",
    ]
    assert add_call["documents"] == ["First page text", "Second page text"]
    assert add_call["embeddings"] == embeddings
    assert [
        metadata["page_number"]
        for metadata in add_call["metadatas"]  # type: ignore[index]
    ] == [1, 2]


def test_ingest_pdf_to_vector_store_zero_chunks_skips_embedding_and_storage(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "empty.pdf"
    _create_test_pdf(pdf_path, [""])
    embedding_service = FakeEmbeddingService([])
    vector_store_client = FakeVectorStoreClient()

    result = ingest_pdf_to_vector_store(
        pdf_path,
        _document_metadata(pdf_path),
        embedding_service,
        vector_store_client,
    )

    assert result.total_chunks == 0
    assert result.stored_chunks == 0
    assert result.empty_pages == [1]
    assert embedding_service.called is False
    assert vector_store_client.called is False
    assert vector_store_client.collection.add_call is None


def test_ingest_pdf_to_vector_store_rejects_mismatched_embedding_count(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "mismatched_embeddings.pdf"
    _create_test_pdf(pdf_path, ["First page text", "Second page text"])

    with pytest.raises(ValueError, match="embeddings count must match chunk records count"):
        ingest_pdf_to_vector_store(
            pdf_path,
            _document_metadata(pdf_path),
            FakeEmbeddingService([[0.1]]),
            FakeVectorStoreClient(),
        )


def test_ingest_pdf_to_vector_store_rejects_mismatched_stored_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = tmp_path / "mismatched_stored.pdf"
    _create_test_pdf(pdf_path, ["First page text", "Second page text"])

    def fake_add_chunk_records(
        records: list[ChunkRecord],
        embeddings: list[list[float]],
        client: FakeVectorStoreClient,
    ) -> int:
        return len(records) - 1

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.add_chunk_records",
        fake_add_chunk_records,
    )

    with pytest.raises(ValueError, match="stored chunks count must match chunk records count"):
        ingest_pdf_to_vector_store(
            pdf_path,
            _document_metadata(pdf_path),
            FakeEmbeddingService([[0.1], [0.2]]),
            FakeVectorStoreClient(),
        )
