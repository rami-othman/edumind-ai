"""Conservative Arabic text normalization helpers."""

from __future__ import annotations

import re


_ALEF_VARIANTS = str.maketrans(
    {
        "\u0623": "\u0627",
        "\u0625": "\u0627",
        "\u0622": "\u0627",
        "\u0671": "\u0627",
        "\u0649": "\u064a",
    },
)
_REPEATED_SPACES_PATTERN = re.compile(r"[ ]+")
_PUNCTUATION_SPACING_PATTERN = re.compile(r"\s+([\u060c\u061b\u061f,.])")
_TOKEN_PATTERN = re.compile(r"[\u0621-\u064aA-Za-z0-9]+")

_ARABIC_STOPWORDS = {
    "\u0645\u0646",
    "\u0641\u064a",
    "\u0639\u0644\u0649",
    "\u0639\u0646",
    "\u0627\u0644\u0649",
    "\u0645\u0627",
    "\u0645\u0627\u0630\u0627",
    "\u0643\u064a\u0641",
    "\u0647\u0644",
    "\u0647\u0648",
    "\u0647\u064a",
    "\u0627\u0644\u0630\u064a",
    "\u0627\u0644\u062a\u064a",
    "\u0645\u0639",
    "\u0648",
}


def normalize_arabic_text(text: str) -> str:
    """Normalize Arabic text conservatively without removing formulas or numbers."""

    _validate_text(text)

    normalized = text.replace("\u0640", "")
    normalized = normalized.translate(_ALEF_VARIANTS)
    normalized = normalized.replace("\u0627\u0627\u0644", "\u0627\u0644\u0627")
    normalized = _PUNCTUATION_SPACING_PATTERN.sub(r"\1", normalized)
    normalized = _REPEATED_SPACES_PATTERN.sub(" ", normalized)
    return normalized.strip()


def normalize_arabic_for_search(text: str) -> str:
    """Normalize Arabic text for retrieval and keyword matching."""

    return normalize_arabic_text(text).lower()


def extract_search_terms(text: str) -> list[str]:
    """Extract normalized search terms from Arabic or English text."""

    normalized = normalize_arabic_for_search(text)
    terms: list[str] = []

    for match in _TOKEN_PATTERN.finditer(normalized):
        term = match.group(0)
        if len(term) <= 1:
            continue
        if term in _ARABIC_STOPWORDS:
            continue
        terms.append(term)

    return terms


def _validate_text(text: str) -> None:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
