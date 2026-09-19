"""Analytics backends: the ``AnalyticsBackend`` interface + DuckDB (default) and SQL connectors.

Returns sufficient statistics only; never raw rows (see docs/02-architecture.md). The active
backend is chosen by settings (``analytics_backend``: ``duckdb`` | ``sql``).
"""

from __future__ import annotations

from app.analytics.base import AnalyticsBackend, EventRow, ExposureRow
from app.analytics.sql_store import SqlStore
from app.analytics.store import DuckStore, new_id
from app.core.config import get_settings

_store: AnalyticsBackend | None = None


def get_store_singleton() -> AnalyticsBackend:
    """Process-wide analytics backend, chosen by ``settings.analytics_backend``."""
    global _store
    if _store is None:
        settings = get_settings()
        if settings.analytics_backend == "sql":
            _store = SqlStore.from_url(settings.analytics_sql_url or settings.database_url)
        else:
            _store = DuckStore(settings.duckdb_path)
    return _store


__all__ = [
    "AnalyticsBackend",
    "DuckStore",
    "EventRow",
    "ExposureRow",
    "SqlStore",
    "get_store_singleton",
    "new_id",
]
