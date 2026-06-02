"""Tenant + identity tables: organization, user, workspace, membership, API key, audit."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from app.models.base import Base, enum_type, json_type
from app.models.enums import (
    AnalyticsBackend,
    AuditActorKind,
    MembershipRole,
    OrgPlan,
    RandomizationUnit,
)


class Organization(Base, table=True):
    __tablename__ = "organization"

    name: str
    slug: str = Field(unique=True, index=True)
    plan: OrgPlan = Field(default=OrgPlan.free, sa_type=enum_type(OrgPlan))
    settings: dict[str, Any] = Field(default_factory=dict, sa_type=json_type())


class User(Base, table=True):
    __tablename__ = "user"

    # NB: email is used for auth only and must never enter the event stream.
    email: str = Field(unique=True, index=True)
    name: str = ""
    is_active: bool = True


class Workspace(Base, table=True):
    __tablename__ = "workspace"
    __table_args__ = (UniqueConstraint("org_id", "slug", name="uq_workspace_org_slug"),)

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    name: str
    slug: str
    default_randomization_unit: RandomizationUnit = Field(
        default=RandomizationUnit.user_id, sa_type=enum_type(RandomizationUnit)
    )
    analytics_backend: AnalyticsBackend = Field(
        default=AnalyticsBackend.duckdb, sa_type=enum_type(AnalyticsBackend)
    )
    # Privacy allow-list: event names + typed properties permitted in this workspace.
    event_schema: dict[str, Any] = Field(default_factory=dict, sa_type=json_type())


class Membership(Base, table=True):
    __tablename__ = "membership"
    __table_args__ = (UniqueConstraint("org_id", "user_id", name="uq_membership_org_user"),)

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    role: MembershipRole = Field(default=MembershipRole.viewer, sa_type=enum_type(MembershipRole))


class ApiKey(Base, table=True):
    __tablename__ = "api_key"

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    name: str
    hashed_key: str = Field(unique=True, index=True)
    scopes: list[str] = Field(default_factory=list, sa_type=json_type())
    last_used_at: datetime | None = None


class AuditLog(Base, table=True):
    __tablename__ = "audit_log"

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    actor_kind: AuditActorKind = Field(sa_type=enum_type(AuditActorKind))
    actor_id: str | None = None
    action: str
    target_type: str
    target_id: uuid.UUID | None = None
    before: dict[str, Any] | None = Field(default=None, sa_type=json_type())
    after: dict[str, Any] | None = Field(default=None, sa_type=json_type())
