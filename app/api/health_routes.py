"""Health check routes."""

from fastapi import APIRouter, Depends

from app.config import Settings
from app.core.constants import APP_VERSION
from app.dependencies import get_app_settings

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
