"""AnalyticsBackend adapter (DuckDB default) — implemented in P06.

Returns sufficient statistics only; never raw rows (see docs/02-architecture.md).
"""

from __future__ import annotations

from app.analytics.store import DuckStore, new_id
from app.core.config import get_settings

_store: DuckStore | None = None


def get_store_singleton() -> DuckStore:
    """Process-wide DuckDB store bound to ``settings.duckdb_path``."""
    global _store
    if _store is None:
        _store = DuckStore(get_settings().duckdb_path)
    return _store


__all__ = ["DuckStore", "get_store_singleton", "new_id"]
