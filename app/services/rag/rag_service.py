"""RAG orchestration service."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.rag.prompt_builder import build_arabic_tutor_prompt
from app.services.rag.retriever import retrieve_similar_chunks


@dataclass(frozen=True)
class RagAnswer:
    answer: str
    sources: list[dict[str, object]]
    retrieved_chunks: list[dict[str, object]]


def answer_question_with_rag(
    question: str,
    embedding_service,
    vector_store_client,
    llm_service,
    top_k: int = 5,
    where: dict[str, object] | None = None,
) -> RagAnswer:
    """Answer a question using retrieval, prompt building, and an injected LLM service."""

    if not isinstance(question, str):
        raise TypeError("question must be a string")
    if not question.strip():
        raise ValueError("question must not be empty")

    retrieved_chunks = retrieve_similar_chunks(
        question=question,
        embedding_service=embedding_service,
        vector_store_client=vector_store_client,
        top_k=top_k,
        where=where,
    )
    rag_prompt = build_arabic_tutor_prompt(question, retrieved_chunks)
    answer = llm_service.generate_answer(
        rag_prompt.system_prompt,
        rag_prompt.user_prompt,
    )

    return RagAnswer(
        answer=answer,
        sources=rag_prompt.sources,
        retrieved_chunks=[chunk.to_dict() for chunk in retrieved_chunks],
    )
