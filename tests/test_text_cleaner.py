import pytest

from app.services.ingestion.text_cleaner import clean_extracted_text


def test_clean_extracted_text_returns_empty_string_for_empty_input() -> None:
    assert clean_extracted_text("") == ""


def test_clean_extracted_text_returns_empty_string_for_whitespace_only_input() -> None:
    assert clean_extracted_text(" \t\r\n  \n") == ""


def test_clean_extracted_text_collapses_repeated_spaces() -> None:
    assert clean_extracted_text("  هذا    نص   عربي  ") == "هذا نص عربي"


def test_clean_extracted_text_reduces_repeated_empty_lines() -> None:
    text = "السطر الأول\n\n\n\nالسطر الثاني"

    assert clean_extracted_text(text) == "السطر الأول\n\nالسطر الثاني"


def test_clean_extracted_text_normalizes_windows_newlines() -> None:
    text = "السطر الأول\r\nالسطر الثاني\rالسطر الثالث"

    assert clean_extracted_text(text) == "السطر الأول\nالسطر الثاني\nالسطر الثالث"


def test_clean_extracted_text_preserves_arabic_letters_and_diacritics() -> None:
    text = "  النَّصّ العَرَبي ـ مهم  "

    assert clean_extracted_text(text) == "النَّصّ العَرَبي ـ مهم"


def test_clean_extracted_text_cleans_simple_arabic_punctuation_spacing() -> None:
    text = "السؤال ؟\n\n\nالجواب .\nمرحبا ، كيف"

    assert clean_extracted_text(text) == "السؤال؟\n\nالجواب.\nمرحبا، كيف"


def test_clean_extracted_text_preserves_numbers_and_equation_like_text() -> None:
    text = "  قانون أوم: V = I * R  و  12 + 3 = 15  "

    assert clean_extracted_text(text) == "قانون أوم: V = I * R و 12 + 3 = 15"


def test_clean_extracted_text_raises_type_error_for_non_string_input() -> None:
    with pytest.raises(TypeError, match="text must be a string"):
        clean_extracted_text(None)  # type: ignore[arg-type]
