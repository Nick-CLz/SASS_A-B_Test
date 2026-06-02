"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app import __version__

router = APIRouter(tags=["meta"])


class HealthResponse(BaseModel):
    """Response body for the health check."""

    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe — returns ok and the app version."""
    return HealthResponse(status="ok", version=__version__)
