"""Chat request and response schemas."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ChatAskRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, gt=0)
    filters: dict[str, Any] | None = None

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be empty")
        return value


class ChatSource(BaseModel):
    chunk_id: str | None = None
    file_name: str | None = None
    page_number: int | None = None
    subject: str | None = None
    grade: str | None = None
    unit: str | None = None
    lesson: str | None = None
    chunk_index: int | None = None
    distance: float | None = None


class RetrievedChunkResponse(BaseModel):
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    distance: float | None = None


class ChatAskResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]]
    retrieved_chunks: list[dict[str, Any]]
