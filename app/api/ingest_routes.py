"""Admin-oriented content ingestion routes."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings
from app.dependencies import (
    IngestionServiceDependency,
    get_app_settings,
    get_ingestion_service,
)
from app.schemas.ingest_schema import (
    PdfDirectoryIngestError,
    PdfDirectoryIngestItem,
    PdfDirectoryIngestRequest,
    PdfDirectoryIngestResponse,
)
from app.services.ingestion.metadata_builder import DocumentMetadata

router = APIRouter(prefix="/ingest", tags=["ingestion"])

PROJECT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DOCKER_DATA_DIR = Path("/app/data")


@router.post("/pdf", response_model=PdfDirectoryIngestResponse)
def ingest_pdf(
    request: PdfDirectoryIngestRequest | None = None,
    settings: Settings = Depends(get_app_settings),
    ingestion_service: IngestionServiceDependency = Depends(get_ingestion_service),
) -> PdfDirectoryIngestResponse:
    """Ingest all server-local PDFs found under the configured books directory."""

    request = request or PdfDirectoryIngestRequest()
    selected_books_dir = request.books_dir or settings.books_dir
    books_dir = _validate_books_dir(selected_books_dir, settings)
    pdf_files = sorted(books_dir.rglob("*.pdf"))

    if not pdf_files:
        raise HTTPException(
            status_code=400,
            detail="No PDF files found in books directory",
        )

    results: list[PdfDirectoryIngestItem] = []
    errors: list[PdfDirectoryIngestError] = []

    for pdf_file in pdf_files:
        subject = _safe_identifier(pdf_file.parent.name, fallback="subject")
        document_id = _build_document_id(subject, pdf_file)
        document_metadata = DocumentMetadata(
            document_id=document_id,
            file_name=pdf_file.name,
            source_path=str(pdf_file),
            grade=settings.books_grade,
            subject=subject,
            source_type=settings.books_source_type,
            language=settings.books_language,
        )

        try:
            ingestion_result = ingestion_service.ingest_pdf(
                file_path=str(pdf_file),
                document_metadata=document_metadata,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
        except Exception as exc:
            errors.append(
                PdfDirectoryIngestError(file_path=str(pdf_file), error=str(exc)),
            )
            continue

        results.append(
            PdfDirectoryIngestItem(
                document_id=ingestion_result.document_id,
                file_name=ingestion_result.file_name,
                source_path=ingestion_result.source_path,
                subject=subject,
                grade=settings.books_grade,
                page_count=ingestion_result.page_count,
                total_chunks=ingestion_result.total_chunks,
                stored_chunks=ingestion_result.stored_chunks,
                empty_pages=ingestion_result.empty_pages,
            ),
        )

    return PdfDirectoryIngestResponse(
        books_dir=str(books_dir),
        total_files_found=len(pdf_files),
        successful_files=len(results),
        failed_files=len(errors),
        results=results,
        errors=errors,
    )


def _validate_books_dir(raw_books_dir: str, settings: Settings) -> Path:
    if ".." in Path(raw_books_dir).parts:
        raise HTTPException(status_code=400, detail="Unsafe books directory path")

    books_dir = Path(raw_books_dir).expanduser().resolve()
    allowed_roots = _allowed_data_roots(settings)
    if not any(_is_relative_to(books_dir, root) for root in allowed_roots):
        raise HTTPException(status_code=400, detail="Unsafe books directory path")

    if not books_dir.exists() or not books_dir.is_dir():
        raise HTTPException(status_code=400, detail="Books directory does not exist")

    return books_dir


def _allowed_data_roots(settings: Settings) -> list[Path]:
    configured_books_dir = Path(settings.books_dir).expanduser().resolve()
    return [
        PROJECT_DATA_DIR.resolve(),
        DOCKER_DATA_DIR.resolve(),
        _find_data_root(configured_books_dir),
    ]


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False

    return True


def _find_data_root(path: Path) -> Path:
    for candidate in [path, *path.parents]:
        if candidate.name == "data":
            return candidate.resolve()

    return path.parent.resolve()


def _build_document_id(subject: str, pdf_file: Path) -> str:
    safe_stem = _safe_identifier(pdf_file.stem, fallback="")
    if safe_stem:
        return f"{subject}_{safe_stem}"

    digest = hashlib.sha1(str(pdf_file).encode("utf-8")).hexdigest()[:6]
    return f"{subject}_book_{digest}"


def _safe_identifier(value: str, *, fallback: str) -> str:
    normalized = value.lower().strip()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or fallback
