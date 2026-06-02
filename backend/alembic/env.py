"""Alembic environment.

The target metadata is ``SQLModel.metadata`` (populated by importing ``app.models``),
and the database URL comes from application settings so there is a single source of
truth. A small ``render_item`` hook keeps JSON columns as JSONB on Postgres.
"""

from __future__ import annotations

from logging.config import fileConfig
from typing import Any

import app.models  # noqa: F401  (registers all tables on SQLModel.metadata)
import sqlmodel  # noqa: F401  (referenced by generated migrations as sqlmodel.*)
from alembic import context
from app.core.config import get_settings
from sqlalchemy import JSON, engine_from_config, pool
from sqlmodel import SQLModel

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

db_url = get_settings().database_url
config.set_main_option("sqlalchemy.url", db_url)

target_metadata = SQLModel.metadata


def render_item(type_: str, obj: Any, autogen_context: Any) -> Any:
    """Render JSON columns as JSONB on Postgres (plain JSON elsewhere)."""
    if type_ == "type" and isinstance(obj, JSON):
        autogen_context.imports.add("from sqlalchemy.dialects import postgresql")
        return "sa.JSON().with_variant(postgresql.JSONB(), 'postgresql')"
    return False


def run_migrations_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        render_item=render_item,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            render_item=render_item,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
