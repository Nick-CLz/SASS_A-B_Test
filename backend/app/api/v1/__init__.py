"""Versioned (/v1) API router aggregation."""

from fastapi import APIRouter

from app.api.v1 import experiments, health, layers, metrics

api_router = APIRouter(prefix="/v1")
api_router.include_router(health.router)
api_router.include_router(experiments.router)
api_router.include_router(metrics.router)
api_router.include_router(layers.router)

__all__ = ["api_router"]
