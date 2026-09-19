"""In-process TTL cache of per-workspace experiment specs.

Keeps the assignment hot path off the database. Entries expire after a TTL and are
invalidated explicitly when an experiment's status changes (see services).
"""

from __future__ import annotations

import time
import uuid

from app.assignment.spec import ExperimentSpec

_TTL_SECONDS = 30.0
_cache: dict[uuid.UUID, tuple[float, list[ExperimentSpec]]] = {}


def get_cached(workspace_id: uuid.UUID) -> list[ExperimentSpec] | None:
    entry = _cache.get(workspace_id)
    if entry is None:
        return None
    cached_at, specs = entry
    if time.monotonic() - cached_at > _TTL_SECONDS:
        _cache.pop(workspace_id, None)
        return None
    return specs


def set_cached(workspace_id: uuid.UUID, specs: list[ExperimentSpec]) -> None:
    _cache[workspace_id] = (time.monotonic(), specs)


def invalidate(workspace_id: uuid.UUID) -> None:
    _cache.pop(workspace_id, None)


def clear() -> None:
    _cache.clear()
