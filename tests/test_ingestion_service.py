from pathlib import Path

import fitz
import pytest

from app.services.ingestion.ingestion_service import build_ingestion_preview
from app.services.ingestion.metadata_builder import DocumentMetadata


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


def test_build_ingestion_preview_returns_generated_pdf_file_name(tmp_path: Path) -> None:
    pdf_path = tmp_path / "physics.pdf"
    _create_test_pdf(pdf_path, ["First page text"])

    result = build_ingestion_preview(pdf_path, _document_metadata(pdf_path))

    assert result.file_name == "physics.pdf"


def test_build_ingestion_preview_returns_page_count(tmp_path: Path) -> None:
    pdf_path = tmp_path / "pages.pdf"
    _create_test_pdf(pdf_path, ["Page one", "Page two"])

    result = build_ingestion_preview(pdf_path, _document_metadata(pdf_path))

    assert result.page_count == 2


def test_build_ingestion_preview_creates_chunk_records(tmp_path: Path) -> None:
    pdf_path = tmp_path / "chunks.pdf"
    _create_test_pdf(pdf_path, ["abcdefghij" * 4])

    result = build_ingestion_preview(
        pdf_path,
        _document_metadata(pdf_path),
        chunk_size=12,
        chunk_overlap=3,
    )

    assert result.total_chunks == len(result.chunk_records)
    assert result.total_chunks > 1


def test_build_ingestion_preview_chunk_metadata_includes_document_fields(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "metadata.pdf"
    _create_test_pdf(pdf_path, ["قانون أوم"])

    result = build_ingestion_preview(pdf_path, _document_metadata(pdf_path))
    metadata = result.chunk_records[0].metadata

    assert metadata["document_id"] == "physics_book_2026"
    assert metadata["file_name"] == "metadata.pdf"
    assert metadata["source_path"] == str(pdf_path)
    assert metadata["grade"] == "12"
    assert metadata["subject"] == "physics"
    assert metadata["unit"] == "electricity"


def test_build_ingestion_preview_preserves_page_numbers_in_chunk_metadata(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "page_numbers.pdf"
    _create_test_pdf(pdf_path, ["First page text", "Second page text"])

    result = build_ingestion_preview(pdf_path, _document_metadata(pdf_path))

    assert [record.metadata["page_number"] for record in result.chunk_records] == [1, 2]


def test_build_ingestion_preview_tracks_empty_pages(tmp_path: Path) -> None:
    pdf_path = tmp_path / "empty_pages.pdf"
    _create_test_pdf(pdf_path, ["First page text", "", "Third page text"])

    result = build_ingestion_preview(pdf_path, _document_metadata(pdf_path))

    assert result.empty_pages == [2]
    assert [record.metadata["page_number"] for record in result.chunk_records] == [1, 3]


def test_build_ingestion_preview_uses_cleaned_text_before_chunking(tmp_path: Path) -> None:
    pdf_path = tmp_path / "cleaning.pdf"
    _create_test_pdf(pdf_path, ["  This    is   cleaned  "])

    result = build_ingestion_preview(pdf_path, _document_metadata(pdf_path))

    assert result.chunk_records[0].text == "This is cleaned"


def test_build_ingestion_preview_rejects_invalid_chunk_settings(tmp_path: Path) -> None:
    pdf_path = tmp_path / "invalid_settings.pdf"
    _create_test_pdf(pdf_path, ["Page text"])
    metadata = _document_metadata(pdf_path)

    with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
        build_ingestion_preview(pdf_path, metadata, chunk_size=0)

    with pytest.raises(ValueError, match="chunk_overlap must be greater than or equal to 0"):
        build_ingestion_preview(pdf_path, metadata, chunk_overlap=-1)

    with pytest.raises(ValueError, match="chunk_overlap must be smaller than chunk_size"):
        build_ingestion_preview(pdf_path, metadata, chunk_size=10, chunk_overlap=10)
