"""Build flat chunk metadata records for future vector storage."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.ingestion.chunker import TextChunk

MetadataValue = str | int | float | bool


@dataclass(frozen=True)
class DocumentMetadata:
    document_id: str
    file_name: str
    source_path: str
    grade: str
    subject: str
    unit: str | None = None
    lesson: str | None = None
    source_type: str = "admin_uploaded_content"
    language: str = "arabic"

    def __post_init__(self) -> None:
        _validate_required_text(self.document_id, "document_id")
        _validate_required_text(self.file_name, "file_name")
        _validate_required_text(self.source_path, "source_path")
        _validate_required_text(self.grade, "grade")
        _validate_required_text(self.subject, "subject")


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    text: str
    metadata: dict[str, MetadataValue]


def build_chunk_id(document_id: str, chunk_index: int) -> str:
    """Build a stable chunk identifier from the document ID and chunk index."""
    _validate_required_text(document_id, "document_id")
    if chunk_index < 0:
        raise ValueError("chunk_index must be greater than or equal to 0")

    return f"{document_id}:chunk:{chunk_index}"


def build_chunk_metadata(
    chunk: TextChunk,
    document_metadata: DocumentMetadata,
) -> dict[str, MetadataValue]:
    """Build flat, Chroma-compatible metadata for a text chunk."""
    _validate_chunk(chunk)

    metadata: dict[str, MetadataValue] = {
        "document_id": document_metadata.document_id,
        "file_name": document_metadata.file_name,
        "source_path": document_metadata.source_path,
        "grade": document_metadata.grade,
        "subject": document_metadata.subject,
        "source_type": document_metadata.source_type,
        "language": document_metadata.language,
        "page_number": chunk.page_number,
        "chunk_index": chunk.chunk_index,
        "start_char": chunk.start_char,
        "end_char": chunk.end_char,
    }

    if document_metadata.unit is not None:
        metadata["unit"] = document_metadata.unit

    if document_metadata.lesson is not None:
        metadata["lesson"] = document_metadata.lesson

    return metadata


def build_chunk_record(
    chunk: TextChunk,
    document_metadata: DocumentMetadata,
) -> ChunkRecord:
    """Build a chunk record ready for future embedding and vector storage."""
    _validate_chunk(chunk)

    return ChunkRecord(
        chunk_id=build_chunk_id(document_metadata.document_id, chunk.chunk_index),
        text=chunk.text,
        metadata=build_chunk_metadata(chunk, document_metadata),
    )


def build_chunk_records(
    chunks: list[TextChunk],
    document_metadata: DocumentMetadata,
) -> list[ChunkRecord]:
    """Build chunk records in the same order as the provided chunks."""
    return [build_chunk_record(chunk, document_metadata) for chunk in chunks]


def _validate_required_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _validate_chunk(chunk: TextChunk) -> None:
    if not chunk.text.strip():
        raise ValueError("chunk text must not be empty")

    if chunk.chunk_index < 0:
        raise ValueError("chunk_index must be greater than or equal to 0")

    if chunk.page_number <= 0:
        raise ValueError("page_number must be greater than 0")

    if chunk.end_char < chunk.start_char:
        raise ValueError("end_char must be greater than or equal to start_char")
