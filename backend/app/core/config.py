"""Application settings, loaded from the environment / ``.env``.

Every field has a safe default so the app (and the test suite) boots without a
``.env`` file. See ``.env.example`` at the repo root for the full list and which
component consumes each variable.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- core / app ----
    app_env: Literal["local", "staging", "production"] = "local"
    app_secret_key: str = "change-me-please"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ---- metadata database (Postgres) ----
    database_url: str = "postgresql+psycopg://mallard:mallard@localhost:5432/mallard"

    # ---- analytics engine (DuckDB) ----
    duckdb_path: str = "./data/analytics.duckdb"

    # ---- Anthropic / Claude (AI agents) ----
    anthropic_api_key: str | None = None
    agent_model_small: str = "claude-haiku-4-5-20251001"
    agent_model_medium: str = "claude-sonnet-4-6"
    agent_model_large: str = "claude-opus-4-8"
    agent_enable_prompt_caching: bool = True

    # ---- CORS (frontend origin) ----
    frontend_origin: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()
