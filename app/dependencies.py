"""Shared FastAPI dependencies."""

from app.config import Settings, get_settings


def get_app_settings() -> Settings:
    """Provide application settings to route handlers."""

    return get_settings()
