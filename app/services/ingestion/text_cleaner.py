"""Conservative Arabic-safe text cleaning utilities."""

from __future__ import annotations

import re


_REPEATED_SPACES_PATTERN = re.compile(r"[ ]+")
_REPEATED_EMPTY_LINES_PATTERN = re.compile(r"\n{3,}")
_ARABIC_PUNCTUATION_SPACING_PATTERN = re.compile(r"\s+([،؛؟,.])")


def normalize_whitespace(text: str) -> str:
    """Normalize newlines, tabs, and repeated spaces without changing content."""
    _validate_text(text)

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\t", " ")

    lines = [
        _REPEATED_SPACES_PATTERN.sub(" ", line).strip()
        for line in normalized.split("\n")
    ]
    return "\n".join(lines)


def remove_repeated_empty_lines(text: str) -> str:
    """Collapse excessive empty lines to a single blank line."""
    _validate_text(text)

    return _REPEATED_EMPTY_LINES_PATTERN.sub("\n\n", text)


def normalize_arabic_punctuation_spacing(text: str) -> str:
    """Remove extra spaces before simple sentence punctuation."""
    _validate_text(text)

    return _ARABIC_PUNCTUATION_SPACING_PATTERN.sub(r"\1", text)


def clean_extracted_text(text: str) -> str:
    """Clean raw PDF-extracted text conservatively for later chunking."""
    _validate_text(text)

    cleaned = normalize_whitespace(text)
    cleaned = normalize_arabic_punctuation_spacing(cleaned)
    cleaned = remove_repeated_empty_lines(cleaned)
    return cleaned.strip()


def _validate_text(text: str) -> None:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
