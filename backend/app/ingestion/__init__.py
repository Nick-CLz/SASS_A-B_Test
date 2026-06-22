"""Event ingestion + PII guard — implemented in P06 (no PII may reach storage)."""

from app.ingestion.service import IngestResult, ingest_events

__all__ = ["IngestResult", "ingest_events"]
