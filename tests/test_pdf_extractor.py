from pathlib import Path

import fitz
import pytest

from app.services.ingestion.pdf_extractor import (
    InvalidPdfFileError,
    PdfFileNotFoundError,
    extract_pdf_text,
)


def _create_test_pdf(path: Path, page_texts: list[str]) -> None:
    document = fitz.open()
    try:
        for text in page_texts:
            page = document.new_page()
            page.insert_text((72, 72), text)
        document.save(path)
    finally:
        document.close()


def test_extract_pdf_text_from_generated_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _create_test_pdf(pdf_path, ["First page text", "Second page text"])

    result = extract_pdf_text(pdf_path)

    assert result.file_path == str(pdf_path)
    assert result.file_name == "sample.pdf"
    assert result.page_count == 2
    assert "First page text" in result.pages[0].text
    assert "Second page text" in result.pages[1].text


def test_extract_pdf_text_uses_one_based_page_numbers(tmp_path: Path) -> None:
    pdf_path = tmp_path / "pages.pdf"
    _create_test_pdf(pdf_path, ["Page one", "Page two"])

    result = extract_pdf_text(pdf_path)

    assert [page.page_number for page in result.pages] == [1, 2]


def test_extract_pdf_text_raises_for_missing_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.pdf"

    with pytest.raises(PdfFileNotFoundError):
        extract_pdf_text(missing_path)


def test_extract_pdf_text_raises_for_non_pdf_file(tmp_path: Path) -> None:
    text_path = tmp_path / "notes.txt"
    text_path.write_text("not a pdf", encoding="utf-8")

    with pytest.raises(InvalidPdfFileError):
        extract_pdf_text(text_path)
