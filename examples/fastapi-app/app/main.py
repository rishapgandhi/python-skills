"""Application factory — single entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.api.v1.router import v1_router
from app.core.config import settings
from app.core.exceptions import AppError, app_exception_handler
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown lifecycle."""
    configure_logging(log_level=settings.log_level, json_output=not settings.debug)
    yield


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        lifespan=lifespan,
    )
    app.add_exception_handler(AppError, app_exception_handler)
    app.include_router(v1_router, prefix="/api/v1")
    return app


app = create_app()
