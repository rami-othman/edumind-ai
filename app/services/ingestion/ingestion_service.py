"""In-memory ingestion preview orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services.ingestion.chunker import TextChunk, split_text_into_chunks
from app.services.ingestion.metadata_builder import (
    ChunkRecord,
    DocumentMetadata,
    build_chunk_records,
)
from app.services.ingestion.pdf_extractor import extract_pdf_text
from app.services.ingestion.text_cleaner import clean_extracted_text
from app.services.vector_store.vector_store_service import add_chunk_records


@dataclass(frozen=True)
class IngestionPreviewResult:
    document_id: str
    file_name: str
    source_path: str
    page_count: int
    total_chunks: int
    empty_pages: list[int]
    chunk_records: list[ChunkRecord]


@dataclass(frozen=True)
class IngestionStorageResult:
    document_id: str
    file_name: str
    source_path: str
    page_count: int
    total_chunks: int
    stored_chunks: int
    empty_pages: list[int]


def build_ingestion_preview(
    file_path: str | Path,
    document_metadata: DocumentMetadata,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> IngestionPreviewResult:
    """Build an in-memory ingestion preview without storing or embedding chunks."""
    _validate_chunk_settings(chunk_size, chunk_overlap)

    extracted_pdf = extract_pdf_text(file_path)
    empty_pages: list[int] = []
    chunks: list[TextChunk] = []

    for page in extracted_pdf.pages:
        cleaned_text = clean_extracted_text(page.text)
        if not cleaned_text:
            empty_pages.append(page.page_number)
            continue

        page_chunks = split_text_into_chunks(
            cleaned_text,
            page_number=page.page_number,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            start_chunk_index=len(chunks),
        )
        chunks.extend(page_chunks)

    chunk_records = build_chunk_records(chunks, document_metadata)

    return IngestionPreviewResult(
        document_id=document_metadata.document_id,
        file_name=extracted_pdf.file_name,
        source_path=extracted_pdf.file_path,
        page_count=extracted_pdf.page_count,
        total_chunks=len(chunk_records),
        empty_pages=empty_pages,
        chunk_records=chunk_records,
    )


def ingest_pdf_to_vector_store(
    file_path: str | Path,
    document_metadata: DocumentMetadata,
    embedding_service,
    vector_store_client,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> IngestionStorageResult:
    """Embed an ingestion preview and store chunk records in the vector store."""

    preview = build_ingestion_preview(
        file_path=file_path,
        document_metadata=document_metadata,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if not preview.chunk_records:
        return _build_storage_result(preview, stored_chunks=0)

    chunk_texts = [record.text for record in preview.chunk_records]
    embeddings = embedding_service.embed_texts(chunk_texts)

    if len(embeddings) != len(preview.chunk_records):
        raise ValueError("embeddings count must match chunk records count")

    stored_chunks = add_chunk_records(
        records=preview.chunk_records,
        embeddings=embeddings,
        client=vector_store_client,
    )

    if stored_chunks != len(preview.chunk_records):
        raise ValueError("stored chunks count must match chunk records count")

    return _build_storage_result(preview, stored_chunks=stored_chunks)


def _build_storage_result(
    preview: IngestionPreviewResult,
    stored_chunks: int,
) -> IngestionStorageResult:
    return IngestionStorageResult(
        document_id=preview.document_id,
        file_name=preview.file_name,
        source_path=preview.source_path,
        page_count=preview.page_count,
        total_chunks=preview.total_chunks,
        stored_chunks=stored_chunks,
        empty_pages=preview.empty_pages,
    )


def _validate_chunk_settings(chunk_size: int, chunk_overlap: int) -> None:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be greater than or equal to 0")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
