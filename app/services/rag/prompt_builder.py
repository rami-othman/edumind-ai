"""Build source-grounded Arabic tutor prompts for future RAG generation."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.rag.retriever import RetrievedChunk

FALLBACK_ANSWER = "لا أملك معلومات كافية من المحتوى المتوفر للإجابة بدقة."
NO_CONTEXT_MESSAGE = "لا يوجد سياق مسترجع ذو صلة."

SYSTEM_PROMPT = f"""أنت مدرس عربي لمساعدة الطلاب السوريين.
استخدم السياق المقدم فقط للإجابة عن سؤال الطالب.
لا تخترع معلومات، ولا تضف ادعاءات غير موجودة في السياق.
إذا لم تكن الإجابة موجودة في السياق، قل بالضبط:
{FALLBACK_ANSWER}
اشرح خطوة بخطوة عندما يكون ذلك مفيدا.
استخدم أمثلة بسيطة فقط إذا كانت مدعومة بالسياق.
اذكر المصادر المتاحة في نهاية الإجابة.
لا تذكر صفحات أو مصادر غير موجودة في السياق."""


@dataclass(frozen=True)
class RagPrompt:
    system_prompt: str
    user_prompt: str
    context: str
    sources: list[dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        """Return a serializable prompt payload."""

        return {
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "context": self.context,
            "sources": self.sources,
        }


def build_arabic_tutor_prompt(
    question: str,
    retrieved_chunks: list[RetrievedChunk],
) -> RagPrompt:
    """Build an Arabic source-grounded tutor prompt from retrieved chunks."""

    if not isinstance(question, str):
        raise TypeError("question must be a string")
    if not question.strip():
        raise ValueError("question must not be empty")
    if not isinstance(retrieved_chunks, list):
        raise TypeError("retrieved_chunks must be a list")

    context = _format_context(retrieved_chunks)
    sources = [_build_source(chunk) for chunk in retrieved_chunks]
    user_prompt = _build_user_prompt(question, context)

    return RagPrompt(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        context=context,
        sources=sources,
    )


def _build_user_prompt(question: str, context: str) -> str:
    return f"""سؤال الطالب:
{question}

السياق المسترجع:
{context}

تعليمات الإجابة:
- أجب باللغة العربية الواضحة.
- استخدم السياق المسترجع فقط.
- لا تخترع معلومات أو تفاصيل غير مذكورة في السياق.
- إذا لم تكن الإجابة متوفرة في السياق، قل بالضبط: {FALLBACK_ANSWER}
- اشرح خطوة بخطوة عندما يكون ذلك مفيدا.
- استخدم أمثلة بسيطة فقط إذا كانت مدعومة بالسياق.
- اذكر المصادر في النهاية باستخدام البيانات المتاحة.
- لا تذكر صفحات أو مصادر غير موجودة في السياق."""


def _format_context(retrieved_chunks: list[RetrievedChunk]) -> str:
    if not retrieved_chunks:
        return NO_CONTEXT_MESSAGE

    return "\n\n".join(
        _format_chunk(index=index, chunk=chunk)
        for index, chunk in enumerate(retrieved_chunks, start=1)
    )


def _format_chunk(index: int, chunk: RetrievedChunk) -> str:
    lines = [f"[Source {index}]"]

    metadata_labels = {
        "file_name": "File",
        "page_number": "Page",
        "subject": "Subject",
        "grade": "Grade",
        "unit": "Unit",
        "lesson": "Lesson",
        "chunk_index": "Chunk Index",
    }

    for key, label in metadata_labels.items():
        if key in chunk.metadata:
            lines.append(f"{label}: {chunk.metadata[key]}")

    lines.extend(
        [
            f"Chunk ID: {chunk.chunk_id}",
            "Content:",
            chunk.text,
        ],
    )

    return "\n".join(lines)


def _build_source(chunk: RetrievedChunk) -> dict[str, object]:
    source: dict[str, object] = {
        "chunk_id": chunk.chunk_id,
        "distance": chunk.distance,
    }

    for key, value in chunk.metadata.items():
        if _is_simple_source_value(value):
            source[key] = value

    return source


def _is_simple_source_value(value: object) -> bool:
    return isinstance(value, str | int | float | bool) or value is None
