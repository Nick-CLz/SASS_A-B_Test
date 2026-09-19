"""Shared schema base."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Response model that can be built from an ORM object via ``model_validate``."""

    model_config = ConfigDict(from_attributes=True)
