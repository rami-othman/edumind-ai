"""Page-based text chunking utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    text: str
    page_number: int
    start_char: int
    end_char: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_index": self.chunk_index,
            "text": self.text,
            "page_number": self.page_number,
            "start_char": self.start_char,
            "end_char": self.end_char,
        }


def split_text_into_chunks(
    text: str,
    page_number: int,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
    start_chunk_index: int = 0,
) -> list[TextChunk]:
    """Split cleaned page text into ordered chunks."""
    _validate_chunking_inputs(text, page_number, chunk_size, chunk_overlap)

    if not text.strip():
        return []

    chunks: list[TextChunk] = []
    text_length = len(text)
    start = 0
    chunk_index = start_chunk_index

    while start < text_length:
        end = _find_chunk_end(text, start, chunk_size)
        chunk_start, chunk_end = _trim_chunk_span(text, start, end)

        if chunk_start < chunk_end:
            chunks.append(
                TextChunk(
                    chunk_index=chunk_index,
                    text=text[chunk_start:chunk_end],
                    page_number=page_number,
                    start_char=chunk_start,
                    end_char=chunk_end,
                )
            )
            chunk_index += 1

        if end >= text_length:
            break

        next_start = end - chunk_overlap
        if next_start <= start:
            next_start = end
        start = next_start

    return chunks


def split_pages_into_chunks(
    pages: list[Any],
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> list[TextChunk]:
    """Split page-like objects or dictionaries into document-ordered chunks."""
    chunks: list[TextChunk] = []

    for page in pages:
        page_text = _read_page_value(page, "text")
        page_number = _read_page_value(page, "page_number")
        page_chunks = split_text_into_chunks(
            page_text,
            page_number=page_number,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            start_chunk_index=len(chunks),
        )
        chunks.extend(page_chunks)

    return chunks


def _validate_chunking_inputs(
    text: str,
    page_number: int,
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if page_number <= 0:
        raise ValueError("page_number must be greater than 0")

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be greater than or equal to 0")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")


def _find_chunk_end(text: str, start: int, chunk_size: int) -> int:
    max_end = min(start + chunk_size, len(text))
    if max_end == len(text):
        return max_end

    search_area = text[start:max_end]
    boundary = _find_best_boundary(search_area)
    if boundary is None:
        return max_end

    return start + boundary


def _find_best_boundary(text: str) -> int | None:
    boundary_candidates = [
        text.rfind("\n\n"),
        text.rfind("\n"),
        max(text.rfind("."), text.rfind("؟"), text.rfind("!")),
        text.rfind(" "),
    ]
    boundary_widths = [2, 1, 1, 1]

    for boundary_index, boundary_width in zip(boundary_candidates, boundary_widths):
        if boundary_index > 0:
            return boundary_index + boundary_width

    return None


def _trim_chunk_span(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1

    while end > start and text[end - 1].isspace():
        end -= 1

    return start, end


def _read_page_value(page: Any, key: str) -> Any:
    if isinstance(page, dict):
        return page[key]

    return getattr(page, key)
