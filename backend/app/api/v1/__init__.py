"""Versioned (/v1) API router aggregation."""

from fastapi import APIRouter

from app.api.v1 import analysis, assign, events, experiments, health, layers, metrics

api_router = APIRouter(prefix="/v1")
api_router.include_router(health.router)
api_router.include_router(assign.router)
api_router.include_router(events.router)
api_router.include_router(experiments.router)
api_router.include_router(analysis.router)
api_router.include_router(metrics.router)
api_router.include_router(layers.router)

__all__ = ["api_router"]
