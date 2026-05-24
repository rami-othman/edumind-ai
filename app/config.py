"""Environment-based configuration for the AI service."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "EduMind AI Service"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8001

    chroma_host: str = "chroma"
    chroma_port: int = 8000
    chroma_collection_name: str = "edumind_content"
    chroma_distance_function: str = "cosine"

    ollama_base_url: str = "http://ollama:11434"
    ollama_llm_base_url: str | None = "https://ollama.com"
    ollama_embedding_base_url: str | None = "http://ollama:11434"
    ollama_api_key: str | None = None
    ollama_llm_model: str = "deepseek-v4-pro:cloud"
    ollama_embedding_model: str = "nomic-embed-text"

    llm_provider: str = "ollama"
    embedding_provider: str = "ollama"
    embedding_dimension: int | None = None
    google_embedding_model: str = "gemini-embedding-2"
    google_embedding_dimension: int = 768

    upload_dir: str = "/app/data/uploads"
    processed_dir: str = "/app/data/processed"
    books_dir: str = "/app/data/uploads/books"
    books_grade: str = "12"
    books_language: str = "arabic"
    books_source_type: str = "admin_uploaded_book"

    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k: int = 5

    @field_validator("embedding_dimension", mode="before")
    @classmethod
    def parse_optional_embedding_dimension(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @field_validator(
        "ollama_llm_base_url",
        "ollama_embedding_base_url",
        "ollama_api_key",
        mode="before",
    )
    @classmethod
    def parse_optional_text(cls, value: object) -> object:
        if value == "":
            return None
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
