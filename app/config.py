"""Environment-based configuration for the AI service."""

from functools import lru_cache

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

    ollama_base_url: str = "http://ollama:11434"
    ollama_llm_model: str = "gemma3:12b"
    ollama_embedding_model: str = "nomic-embed-text"

    upload_dir: str = "/app/data/uploads"
    processed_dir: str = "/app/data/processed"

    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k: int = 5

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
