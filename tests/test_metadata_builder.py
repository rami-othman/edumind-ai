import pytest

from app.services.ingestion.chunker import TextChunk
from app.services.ingestion.metadata_builder import (
    ChunkRecord,
    DocumentMetadata,
    build_chunk_id,
    build_chunk_metadata,
    build_chunk_record,
    build_chunk_records,
)


def _document_metadata(**overrides: object) -> DocumentMetadata:
    values = {
        "document_id": "physics_book_2026",
        "file_name": "physics.pdf",
        "source_path": "data/uploads/books/physics.pdf",
        "grade": "12",
        "subject": "physics",
    }
    values.update(overrides)
    return DocumentMetadata(**values)  # type: ignore[arg-type]


def _chunk(**overrides: object) -> TextChunk:
    values = {
        "chunk_index": 0,
        "text": "قانون أوم: V = I * R",
        "page_number": 45,
        "start_char": 100,
        "end_char": 120,
    }
    values.update(overrides)
    return TextChunk(**values)  # type: ignore[arg-type]


def test_build_chunk_id_uses_document_id_and_chunk_index() -> None:
    assert build_chunk_id("physics_book_2026", 0) == "physics_book_2026:chunk:0"


def test_build_chunk_metadata_includes_required_fields() -> None:
    metadata = build_chunk_metadata(_chunk(), _document_metadata())

    assert metadata == {
        "document_id": "physics_book_2026",
        "file_name": "physics.pdf",
        "source_path": "data/uploads/books/physics.pdf",
        "grade": "12",
        "subject": "physics",
        "source_type": "admin_uploaded_content",
        "language": "arabic",
        "page_number": 45,
        "chunk_index": 0,
        "start_char": 100,
        "end_char": 120,
    }


def test_build_chunk_metadata_includes_optional_unit_and_lesson_when_provided() -> None:
    metadata = build_chunk_metadata(
        _chunk(),
        _document_metadata(unit="electricity", lesson="ohms_law"),
    )

    assert metadata["unit"] == "electricity"
    assert metadata["lesson"] == "ohms_law"


def test_build_chunk_metadata_skips_optional_unit_and_lesson_when_none() -> None:
    metadata = build_chunk_metadata(_chunk(), _document_metadata())

    assert "unit" not in metadata
    assert "lesson" not in metadata


def test_build_chunk_metadata_is_flat_and_has_no_nested_dictionaries() -> None:
    metadata = build_chunk_metadata(
        _chunk(),
        _document_metadata(unit="electricity"),
    )

    assert all(not isinstance(value, dict) for value in metadata.values())


def test_build_chunk_record_creates_record_with_id_text_and_metadata() -> None:
    record = build_chunk_record(_chunk(), _document_metadata())

    assert record == ChunkRecord(
        chunk_id="physics_book_2026:chunk:0",
        text="قانون أوم: V = I * R",
        metadata=build_chunk_metadata(_chunk(), _document_metadata()),
    )


def test_build_chunk_records_creates_multiple_records() -> None:
    chunks = [
        _chunk(chunk_index=0, text="النص الأول", start_char=0, end_char=9),
        _chunk(chunk_index=1, text="النص الثاني", start_char=10, end_char=20),
    ]

    records = build_chunk_records(chunks, _document_metadata())

    assert [record.chunk_id for record in records] == [
        "physics_book_2026:chunk:0",
        "physics_book_2026:chunk:1",
    ]
    assert [record.text for record in records] == ["النص الأول", "النص الثاني"]


def test_chunk_ids_are_unique_per_chunk_index() -> None:
    assert build_chunk_id("physics_book_2026", 1) != build_chunk_id(
        "physics_book_2026",
        2,
    )


@pytest.mark.parametrize(
    "field_name",
    ["document_id", "file_name", "source_path", "grade", "subject"],
)
def test_empty_required_document_metadata_raises_value_error(field_name: str) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must not be empty"):
        _document_metadata(**{field_name: " "})


def test_empty_chunk_text_raises_value_error() -> None:
    with pytest.raises(ValueError, match="chunk text must not be empty"):
        build_chunk_record(_chunk(text="   "), _document_metadata())


def test_invalid_chunk_index_raises_value_error() -> None:
    with pytest.raises(ValueError, match="chunk_index must be greater than or equal to 0"):
        build_chunk_record(_chunk(chunk_index=-1), _document_metadata())


def test_invalid_page_number_raises_value_error() -> None:
    with pytest.raises(ValueError, match="page_number must be greater than 0"):
        build_chunk_record(_chunk(page_number=0), _document_metadata())


def test_invalid_character_range_raises_value_error() -> None:
    with pytest.raises(ValueError, match="end_char must be greater than or equal to start_char"):
        build_chunk_record(_chunk(start_char=10, end_char=9), _document_metadata())
