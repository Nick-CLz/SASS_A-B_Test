"""Mallard backend application package.

See ``docs/02-architecture.md`` for the component layout. Subpackages:

- ``core``       — settings, logging (P01)
- ``api``        — REST routers under /v1 (P01, P03, P09, agents)
- ``models``     — SQLModel metadata tables (P02)
- ``services``   — domain logic (P03, P09)
- ``assignment`` — pure deterministic bucketing (P04)
- ``ingestion``  — event intake + PII guard (P06)
- ``analytics``  — AnalyticsBackend adapter, DuckDB (P06)
- ``stats``      — pure statistics engine (P07, P08)
- ``agents``     — Claude agents + tools + evals (P11-P14)
"""

__version__ = "0.1.0"
