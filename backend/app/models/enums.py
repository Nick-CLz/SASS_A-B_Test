"""Enumerations used across the metadata model (see docs/03-data-model.md).

All are ``str`` enums and are stored as checked VARCHARs (see ``base.enum_type``).
"""

from __future__ import annotations

from enum import StrEnum


class OrgPlan(StrEnum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class MembershipRole(StrEnum):
    owner = "owner"
    admin = "admin"
    editor = "editor"
    analyst = "analyst"
    viewer = "viewer"


class RandomizationUnit(StrEnum):
    user_id = "user_id"
    session_id = "session_id"
    device_id = "device_id"
    account_id = "account_id"


class AnalyticsBackend(StrEnum):
    duckdb = "duckdb"
    bigquery = "bigquery"
    snowflake = "snowflake"
    databricks = "databricks"


class ExperimentStatus(StrEnum):
    draft = "draft"
    review = "review"
    running = "running"
    paused = "paused"
    concluded = "concluded"
    archived = "archived"


class ExperimentDecision(StrEnum):
    ship = "ship"
    no_ship = "no_ship"
    iterate = "iterate"
    inconclusive = "inconclusive"


class MetricType(StrEnum):
    proportion = "proportion"
    mean = "mean"
    ratio = "ratio"
    count = "count"  # type: ignore[assignment]  # shadows str.count (mypy false positive)


class MetricDirection(StrEnum):
    increase_good = "increase_good"
    decrease_good = "decrease_good"


class ExperimentMetricRole(StrEnum):
    primary = "primary"
    secondary = "secondary"
    guardrail = "guardrail"


class AnalysisTrigger(StrEnum):
    scheduled = "scheduled"
    manual = "manual"
    agent = "agent"


class AnalysisStatus(StrEnum):
    pending = "pending"
    running = "running"
    complete = "complete"
    failed = "failed"


class AgentType(StrEnum):
    designer = "designer"
    monitor = "monitor"
    analyst = "analyst"
    readout = "readout"


class AgentRunStatus(StrEnum):
    pending = "pending"
    running = "running"
    complete = "complete"
    failed = "failed"


class AgentStepKind(StrEnum):
    message = "message"
    tool_call = "tool_call"
    tool_result = "tool_result"


class ReadoutAuthor(StrEnum):
    agent = "agent"
    human = "human"


class AuditActorKind(StrEnum):
    user = "user"
    agent = "agent"
    system = "system"
