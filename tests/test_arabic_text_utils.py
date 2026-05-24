from app.utils.arabic_text_utils import (
    extract_search_terms,
    normalize_arabic_for_search,
    normalize_arabic_text,
)


def test_normalize_arabic_text_fixes_common_alef_lam_pdf_artifact() -> None:
    assert "\u0627\u0644\u0627\u0646\u0642\u0633\u0627\u0645" in normalize_arabic_text(
        "\u0627\u0627\u0644\u0646\u0642\u0633\u0627\u0645",
    )


def test_normalize_arabic_text_normalizes_alef_variants() -> None:
    assert normalize_arabic_text("\u0623\u0625\u0622\u0671") == "\u0627\u0627\u0627\u0627"


def test_normalize_arabic_text_removes_tatweel() -> None:
    assert normalize_arabic_text("\u0627\u0644\u0646\u0640\u0645\u0648") == "\u0627\u0644\u0646\u0645\u0648"


def test_normalize_arabic_text_preserves_math_symbols_and_numbers() -> None:
    text = "\u0642\u0627\u0646\u0648\u0646: V = I * R \u0648 12 + 3 = 15"

    assert normalize_arabic_text(text) == text


def test_normalize_arabic_for_search_lowercases_english_text() -> None:
    assert normalize_arabic_for_search("Cell DNA") == "cell dna"


def test_extract_search_terms_removes_common_stopwords() -> None:
    terms = extract_search_terms(
        "\u0645\u0627 \u0647\u0648 \u0627\u0644\u0627\u0646\u0642\u0633\u0627\u0645 "
        "\u0627\u0644\u062e\u064a\u0637\u064a \u0641\u064a \u0627\u0644\u062e\u0644\u064a\u0629",
    )

    assert "\u0645\u0627" not in terms
    assert "\u0647\u0648" not in terms
    assert "\u0641\u064a" not in terms
    assert "\u0627\u0644\u0627\u0646\u0642\u0633\u0627\u0645" in terms
    assert "\u0627\u0644\u062e\u064a\u0637\u064a" in terms
    assert "\u0627\u0644\u062e\u0644\u064a\u0629" in terms


def test_extract_search_terms_removes_arabic_question_mark_from_terms() -> None:
    terms = extract_search_terms("\u0645\u0631\u0627\u062d\u0644 \u0627\u0644\u0646\u0645\u0648\u061f")

    assert "\u0627\u0644\u0646\u0645\u0648" in terms
    assert "\u0627\u0644\u0646\u0645\u0648\u061f" not in terms
