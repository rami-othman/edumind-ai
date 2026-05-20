"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.health_routes import router as health_router
from app.config import get_settings
from app.core.constants import APP_VERSION
from app.core.logging_config import setup_logging

settings = get_settings()
setup_logging()

app = FastAPI(title=settings.app_name, version=APP_VERSION)
app.include_router(health_router)


@app.get("/")
def root() -> dict[str, str]:
    """Return a simple service message."""

    return {"message": f"{settings.app_name} is running"}
