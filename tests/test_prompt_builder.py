import pytest

from app.services.rag.prompt_builder import RagPrompt, build_arabic_tutor_prompt
from app.services.rag.retriever import RetrievedChunk


def _retrieved_chunk(**overrides: object) -> RetrievedChunk:
    values = {
        "chunk_id": "physics_book_2026:chunk:12",
        "text": "قانون أوم يربط بين التوتر والتيار والمقاومة.",
        "metadata": {
            "file_name": "physics.pdf",
            "page_number": 45,
            "subject": "physics",
            "grade": "12",
            "unit": "electricity",
            "lesson": "ohms_law",
            "chunk_index": 12,
        },
        "distance": 0.123,
    }
    values.update(overrides)
    return RetrievedChunk(**values)  # type: ignore[arg-type]


def test_build_arabic_tutor_prompt_returns_prompt_for_question_and_chunks() -> None:
    prompt = build_arabic_tutor_prompt("ما هو قانون أوم؟", [_retrieved_chunk()])

    assert isinstance(prompt, RagPrompt)
    assert prompt.context.startswith("[Source 1]")
    assert "قانون أوم يربط بين التوتر والتيار والمقاومة." in prompt.context
    assert prompt.sources == [
        {
            "chunk_id": "physics_book_2026:chunk:12",
            "distance": 0.123,
            "file_name": "physics.pdf",
            "page_number": 45,
            "subject": "physics",
            "grade": "12",
            "unit": "electricity",
            "lesson": "ohms_law",
            "chunk_index": 12,
        },
    ]


def test_system_prompt_contains_arabic_tutor_and_source_grounding_rules() -> None:
    prompt = build_arabic_tutor_prompt("ما هو قانون أوم؟", [_retrieved_chunk()])

    assert "مدرس عربي" in prompt.system_prompt
    assert "استخدم السياق المقدم فقط" in prompt.system_prompt
    assert "لا تخترع معلومات" in prompt.system_prompt
    assert "لا أملك معلومات كافية من المحتوى المتوفر للإجابة بدقة." in prompt.system_prompt


def test_user_prompt_contains_original_question_and_answer_rules() -> None:
    question = "  ما هو قانون أوم؟  "
    prompt = build_arabic_tutor_prompt(question, [_retrieved_chunk()])

    assert question in prompt.user_prompt
    assert "اذكر المصادر في النهاية" in prompt.user_prompt
    assert "لا تذكر صفحات أو مصادر غير موجودة" in prompt.user_prompt


def test_context_includes_available_source_metadata() -> None:
    prompt = build_arabic_tutor_prompt("ما هو قانون أوم؟", [_retrieved_chunk()])

    assert "File: physics.pdf" in prompt.context
    assert "Page: 45" in prompt.context
    assert "Subject: physics" in prompt.context
    assert "Grade: 12" in prompt.context
    assert "Unit: electricity" in prompt.context
    assert "Lesson: ohms_law" in prompt.context
    assert "Chunk Index: 12" in prompt.context
    assert "Chunk ID: physics_book_2026:chunk:12" in prompt.context


def test_missing_metadata_does_not_crash() -> None:
    prompt = build_arabic_tutor_prompt(
        "ما هو قانون أوم؟",
        [_retrieved_chunk(metadata={}, distance=None)],
    )

    assert "Chunk ID: physics_book_2026:chunk:12" in prompt.context
    assert "Content:" in prompt.context
    assert prompt.sources == [
        {
            "chunk_id": "physics_book_2026:chunk:12",
            "distance": None,
        },
    ]


def test_empty_retrieved_chunks_produces_no_context_fallback_prompt() -> None:
    prompt = build_arabic_tutor_prompt("ما هو قانون أوم؟", [])

    assert "ما هو قانون أوم؟" in prompt.user_prompt
    assert "لا يوجد سياق مسترجع ذو صلة." in prompt.context
    assert "لا أملك معلومات كافية من المحتوى المتوفر للإجابة بدقة." in prompt.user_prompt
    assert prompt.sources == []


def test_rag_prompt_to_dict_returns_serializable_dictionary() -> None:
    prompt = build_arabic_tutor_prompt("ما هو قانون أوم؟", [_retrieved_chunk()])

    assert prompt.to_dict() == {
        "system_prompt": prompt.system_prompt,
        "user_prompt": prompt.user_prompt,
        "context": prompt.context,
        "sources": prompt.sources,
    }


def test_empty_question_raises_value_error() -> None:
    with pytest.raises(ValueError, match="question must not be empty"):
        build_arabic_tutor_prompt("   ", [])


def test_non_string_question_raises_type_error() -> None:
    with pytest.raises(TypeError, match="question must be a string"):
        build_arabic_tutor_prompt(None, [])  # type: ignore[arg-type]


def test_non_list_retrieved_chunks_raises_type_error() -> None:
    with pytest.raises(TypeError, match="retrieved_chunks must be a list"):
        build_arabic_tutor_prompt("ما هو قانون أوم؟", None)  # type: ignore[arg-type]
