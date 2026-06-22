"""FastAPI application entrypoint.

Run locally with::

    uvicorn app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.v1 import api_router
from app.core import configure_logging, get_settings
from app.core.errors import DomainError


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Render expected domain errors as typed JSON (see docs/06-api-and-sdk.md)."""
    assert isinstance(exc, DomainError)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Mallard API",
        version=__version__,
        summary="AI-native, privacy-first A/B testing platform.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(DomainError, domain_error_handler)
    app.include_router(api_router)
    return app


app = create_app()
