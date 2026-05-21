"""PDF text extraction utilities for ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz


class PdfExtractionError(Exception):
    """Base error for PDF extraction failures."""


class PdfFileNotFoundError(PdfExtractionError):
    """Raised when the requested PDF file does not exist."""


class InvalidPdfFileError(PdfExtractionError):
    """Raised when the requested file is not a PDF."""


class PdfProcessingError(PdfExtractionError):
    """Raised when PyMuPDF cannot open or process the PDF."""


@dataclass(frozen=True)
class ExtractedPdfPage:
    page_number: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "text": self.text,
        }


@dataclass(frozen=True)
class ExtractedPdf:
    file_path: str
    file_name: str
    page_count: int
    pages: list[ExtractedPdfPage]

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "page_count": self.page_count,
            "pages": [page.to_dict() for page in self.pages],
        }


def extract_pdf_text(file_path: str | Path) -> ExtractedPdf:
    """Extract text from a PDF page by page."""
    pdf_path = Path(file_path)
    _validate_pdf_path(pdf_path)

    document = None
    try:
        document = fitz.open(pdf_path)
        pages = [
            ExtractedPdfPage(
                page_number=page_index + 1,
                # OCR may be added later for scanned/image-only PDFs.
                text=document.load_page(page_index).get_text("text", sort=True) or "",
            )
            for page_index in range(document.page_count)
        ]

        return ExtractedPdf(
            file_path=str(pdf_path),
            file_name=pdf_path.name,
            page_count=document.page_count,
            pages=pages,
        )
    except PdfExtractionError:
        raise
    except Exception as exc:
        raise PdfProcessingError(f"Could not process PDF file: {pdf_path}") from exc
    finally:
        if document is not None:
            document.close()


def _validate_pdf_path(file_path: Path) -> None:
    if not file_path.exists():
        raise PdfFileNotFoundError(f"PDF file does not exist: {file_path}")

    if not file_path.is_file() or file_path.suffix.lower() != ".pdf":
        raise InvalidPdfFileError(f"File is not a PDF: {file_path}")
