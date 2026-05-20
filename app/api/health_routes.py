"""Health check routes."""

from fastapi import APIRouter, Depends

from app.config import Settings
from app.core.constants import APP_VERSION
from app.dependencies import get_app_settings
from app.services.llm.ollama_client import check_ollama_health
from app.services.vector_store.chroma_client import check_chroma_health

router = APIRouter()


@router.get("/health")
def health_check(settings: Settings = Depends(get_app_settings)) -> dict[str, str]:
    """Return basic service health information."""

    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "version": APP_VERSION,
    }


@router.get("/health/dependencies")
def dependency_health_check(
    settings: Settings = Depends(get_app_settings),
) -> dict[str, object]:
    """Return lightweight dependency reachability status."""

    chroma_status = check_chroma_health(
        host=settings.chroma_host,
        port=settings.chroma_port,
    )
    ollama_status = check_ollama_health(base_url=settings.ollama_base_url)
    dependencies = {
        "chroma": chroma_status,
        "ollama": ollama_status,
    }
    status = (
        "ok"
        if all(dependency["status"] == "ok" for dependency in dependencies.values())
        else "degraded"
    )

    return {
        "status": status,
        "service": settings.app_name,
        "dependencies": dependencies,
    }
