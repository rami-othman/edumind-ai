"""Ingestion request and response schemas."""

from pydantic import BaseModel


class PdfDirectoryIngestRequest(BaseModel):
    books_dir: str | None = None


class PdfDirectoryIngestItem(BaseModel):
    document_id: str
    file_name: str
    source_path: str
    subject: str
    grade: str
    page_count: int
    total_chunks: int
    stored_chunks: int
    empty_pages: list[int]


class PdfDirectoryIngestError(BaseModel):
    file_path: str
    error: str


class PdfDirectoryIngestResponse(BaseModel):
    books_dir: str
    total_files_found: int
    successful_files: int
    failed_files: int
    results: list[PdfDirectoryIngestItem]
    errors: list[PdfDirectoryIngestError]
