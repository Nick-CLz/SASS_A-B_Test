"""The metadata model registers all tables and key invariants hold at import time."""

from __future__ import annotations

import app.models  # noqa: F401  (registers tables)
from app.models import Organization, Variant
from sqlmodel import SQLModel

EXPECTED_TABLE_COUNT = 17


def test_all_tables_registered() -> None:
    assert len(SQLModel.metadata.tables) == EXPECTED_TABLE_COUNT


def test_table_names() -> None:
    assert Organization.__tablename__ == "organization"
    assert Variant.__tablename__ == "variant"
    assert "experiment_metric" in SQLModel.metadata.tables
