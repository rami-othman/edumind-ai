import pytest

from app.services.ingestion.text_cleaner import clean_extracted_text


def test_clean_extracted_text_returns_empty_string_for_empty_input() -> None:
    assert clean_extracted_text("") == ""


def test_clean_extracted_text_returns_empty_string_for_whitespace_only_input() -> None:
    assert clean_extracted_text(" \t\r\n  \n") == ""


def test_clean_extracted_text_collapses_repeated_spaces() -> None:
    assert clean_extracted_text("  \u0647\u0630\u0627    \u0646\u0635   \u0639\u0631\u0628\u064a  ") == "\u0647\u0630\u0627 \u0646\u0635 \u0639\u0631\u0628\u064a"


def test_clean_extracted_text_reduces_repeated_empty_lines() -> None:
    text = "\u0627\u0644\u0633\u0637\u0631 \u0627\u0644\u0623\u0648\u0644\n\n\n\n\u0627\u0644\u0633\u0637\u0631 \u0627\u0644\u062b\u0627\u0646\u064a"

    assert clean_extracted_text(text) == "\u0627\u0644\u0633\u0637\u0631 \u0627\u0644\u0627\u0648\u0644\n\n\u0627\u0644\u0633\u0637\u0631 \u0627\u0644\u062b\u0627\u0646\u064a"


def test_clean_extracted_text_normalizes_windows_newlines() -> None:
    text = "\u0627\u0644\u0633\u0637\u0631 \u0627\u0644\u0623\u0648\u0644\r\n\u0627\u0644\u0633\u0637\u0631 \u0627\u0644\u062b\u0627\u0646\u064a\r\u0627\u0644\u0633\u0637\u0631 \u0627\u0644\u062b\u0627\u0644\u062b"

    assert clean_extracted_text(text) == "\u0627\u0644\u0633\u0637\u0631 \u0627\u0644\u0627\u0648\u0644\n\u0627\u0644\u0633\u0637\u0631 \u0627\u0644\u062b\u0627\u0646\u064a\n\u0627\u0644\u0633\u0637\u0631 \u0627\u0644\u062b\u0627\u0644\u062b"


def test_clean_extracted_text_preserves_arabic_letters_and_diacritics() -> None:
    text = "  \u0627\u0644\u0646\u064e\u0651\u0635\u0651 \u0627\u0644\u0639\u064e\u0631\u064e\u0628\u064a \u0640 \u0645\u0647\u0645  "

    assert clean_extracted_text(text) == "\u0627\u0644\u0646\u064e\u0651\u0635\u0651 \u0627\u0644\u0639\u064e\u0631\u064e\u0628\u064a \u0645\u0647\u0645"


def test_clean_extracted_text_cleans_simple_arabic_punctuation_spacing() -> None:
    text = "\u0627\u0644\u0633\u0624\u0627\u0644 \u061f\n\n\n\u0627\u0644\u062c\u0648\u0627\u0628 .\n\u0645\u0631\u062d\u0628\u0627 \u060c \u0643\u064a\u0641"

    assert clean_extracted_text(text) == "\u0627\u0644\u0633\u0624\u0627\u0644\u061f\n\n\u0627\u0644\u062c\u0648\u0627\u0628.\n\u0645\u0631\u062d\u0628\u0627\u060c \u0643\u064a\u0641"


def test_clean_extracted_text_preserves_numbers_and_equation_like_text() -> None:
    text = "  \u0642\u0627\u0646\u0648\u0646 \u0623\u0648\u0645: V = I * R  \u0648  12 + 3 = 15  "

    assert clean_extracted_text(text) == "\u0642\u0627\u0646\u0648\u0646 \u0627\u0648\u0645: V = I * R \u0648 12 + 3 = 15"


def test_clean_extracted_text_applies_arabic_normalization() -> None:
    text = (
        "\u0623\u0647\u0645\u064a\u0629  \u0627\u0627\u0644\u0646\u0642\u0633\u0627\u0645"
        "  \u0627\u0644\u0645\u0646\u0635\u0641"
    )

    assert clean_extracted_text(text) == (
        "\u0627\u0647\u0645\u064a\u0629 \u0627\u0644\u0627\u0646\u0642\u0633\u0627\u0645 "
        "\u0627\u0644\u0645\u0646\u0635\u0641"
    )


def test_clean_extracted_text_raises_type_error_for_non_string_input() -> None:
    with pytest.raises(TypeError, match="text must be a string"):
        clean_extracted_text(None)  # type: ignore[arg-type]
