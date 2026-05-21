import pytest

from app.services.ingestion.chunker import (
    TextChunk,
    split_pages_into_chunks,
    split_text_into_chunks,
)


def test_split_text_into_chunks_returns_empty_list_for_empty_text() -> None:
    assert split_text_into_chunks("", page_number=1) == []
    assert split_text_into_chunks(" \n\t ", page_number=1) == []


def test_split_text_into_chunks_creates_one_chunk_for_short_text() -> None:
    chunks = split_text_into_chunks("هذا نص قصير", page_number=3, chunk_size=200)

    assert chunks == [
        TextChunk(
            chunk_index=0,
            text="هذا نص قصير",
            page_number=3,
            start_char=0,
            end_char=11,
        )
    ]


def test_split_text_into_chunks_creates_multiple_chunks_for_long_text() -> None:
    text = "abcdefghij" * 5

    chunks = split_text_into_chunks(text, page_number=1, chunk_size=12, chunk_overlap=3)

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 12 for chunk in chunks)


def test_split_text_into_chunks_preserves_page_number() -> None:
    chunks = split_text_into_chunks(
        "abcdefghij" * 3,
        page_number=7,
        chunk_size=10,
        chunk_overlap=2,
    )

    assert {chunk.page_number for chunk in chunks} == {7}


def test_split_text_into_chunks_uses_sequential_chunk_indexes() -> None:
    chunks = split_text_into_chunks(
        "abcdefghij" * 3,
        page_number=1,
        chunk_size=10,
        chunk_overlap=2,
        start_chunk_index=5,
    )

    assert [chunk.chunk_index for chunk in chunks] == list(range(5, 5 + len(chunks)))


def test_split_text_into_chunks_uses_overlap_between_chunks() -> None:
    chunks = split_text_into_chunks(
        "0123456789" * 3,
        page_number=1,
        chunk_size=10,
        chunk_overlap=3,
    )

    assert chunks[1].start_char == chunks[0].end_char - 3
    assert chunks[1].text.startswith(chunks[0].text[-3:])


def test_split_text_into_chunks_rejects_invalid_chunk_size() -> None:
    with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
        split_text_into_chunks("text", page_number=1, chunk_size=0)


def test_split_text_into_chunks_rejects_invalid_chunk_overlap() -> None:
    with pytest.raises(ValueError, match="chunk_overlap must be greater than or equal to 0"):
        split_text_into_chunks("text", page_number=1, chunk_size=10, chunk_overlap=-1)

    with pytest.raises(ValueError, match="chunk_overlap must be smaller than chunk_size"):
        split_text_into_chunks("text", page_number=1, chunk_size=10, chunk_overlap=10)


def test_split_text_into_chunks_rejects_invalid_page_number() -> None:
    with pytest.raises(ValueError, match="page_number must be greater than 0"):
        split_text_into_chunks("text", page_number=0)


def test_split_text_into_chunks_rejects_non_string_text() -> None:
    with pytest.raises(TypeError, match="text must be a string"):
        split_text_into_chunks(None, page_number=1)  # type: ignore[arg-type]


def test_split_text_into_chunks_preserves_arabic_text() -> None:
    text = "هذا نص عربي مهم. يحتوي على أمثلة وأرقام 123."

    chunks = split_text_into_chunks(text, page_number=1, chunk_size=200)

    assert chunks[0].text == text


def test_split_text_into_chunks_prefers_sentence_and_newline_boundaries() -> None:
    text = "الجملة الأولى.\nالجملة الثانية طويلة قليلا.\nالجملة الثالثة."

    chunks = split_text_into_chunks(text, page_number=1, chunk_size=40, chunk_overlap=0)

    assert chunks[0].text == "الجملة الأولى."
    assert chunks[1].text == "الجملة الثانية طويلة قليلا."


def test_split_pages_into_chunks_preserves_document_order_across_pages() -> None:
    pages = [
        {"page_number": 1, "text": "abcdefghij" * 2},
        {"page_number": 2, "text": "نص عربي"},
    ]

    chunks = split_pages_into_chunks(pages, chunk_size=10, chunk_overlap=2)

    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert chunks[0].page_number == 1
    assert chunks[-1].page_number == 2
    assert chunks[-1].text == "نص عربي"
