"""Shared FastAPI dependencies."""

from app.config import Settings, get_settings
from app.services.embeddings import embedding_service
from app.services.ingestion.ingestion_service import (
    IngestionStorageResult,
    ingest_pdf_to_vector_store,
)
from app.services.ingestion.metadata_builder import DocumentMetadata
from app.services.llm import llm_service
from app.services.rag.rag_service import RagAnswer, answer_question_with_rag
from app.services.vector_store.chroma_client import build_chroma_client


def get_app_settings() -> Settings:
    """Provide application settings to route handlers."""

    return get_settings()


class RagServiceDependency:
    """Thin dependency wrapper around the RAG orchestration function."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def answer_question(
        self,
        question: str,
        top_k: int = 5,
        where: dict[str, object] | None = None,
    ) -> RagAnswer:
        embedding_client = embedding_service.get_embedding_client(self.settings)
        vector_store_client = build_chroma_client(self.settings)
        llm_provider = LLMServiceDependency(self.settings)

        return answer_question_with_rag(
            question=question,
            embedding_service=embedding_client,
            vector_store_client=vector_store_client,
            llm_service=llm_provider,
            top_k=top_k,
            where=where,
        )


class LLMServiceDependency:
    """Adapter exposing the method expected by the RAG service."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_answer(self, system_prompt: str, user_prompt: str) -> str:
        return llm_service.generate_answer(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            settings=self.settings,
        )


class IngestionServiceDependency:
    """Thin dependency wrapper around PDF ingestion-to-vector-store orchestration."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def ingest_pdf(
        self,
        *,
        file_path: str,
        document_metadata: DocumentMetadata,
        chunk_size: int,
        chunk_overlap: int,
    ) -> IngestionStorageResult:
        embedding_client = embedding_service.get_embedding_client(self.settings)
        vector_store_client = build_chroma_client(self.settings)

        return ingest_pdf_to_vector_store(
            file_path=file_path,
            document_metadata=document_metadata,
            embedding_service=embedding_client,
            vector_store_client=vector_store_client,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )


def get_rag_service() -> RagServiceDependency:
    """Provide a RAG service dependency that can be overridden in tests."""

    return RagServiceDependency(get_settings())


def get_ingestion_service() -> IngestionServiceDependency:
    """Provide an ingestion service dependency that can be overridden in tests."""

    return IngestionServiceDependency(get_settings())
