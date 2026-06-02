"""Versioned (/v1) API router aggregation.

As later prompts add routers (experiments P03, results P09, agents P12-P14),
include them here.
"""

from fastapi import APIRouter

from app.api.v1 import health

api_router = APIRouter(prefix="/v1")
api_router.include_router(health.router)

__all__ = ["api_router"]
