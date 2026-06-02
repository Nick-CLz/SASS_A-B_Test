"""Thin, generic CRUD helpers over a SQLModel ``Session``.

Business rules live in entity-specific modules (e.g. ``experiments.py``); these helpers
just persist and fetch.
"""

from __future__ import annotations

import uuid

from sqlmodel import Session, SQLModel, select


def add[T: SQLModel](session: Session, obj: T) -> T:
    """Persist a single object and return it refreshed."""
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def add_all[T: SQLModel](session: Session, objs: list[T]) -> list[T]:
    """Persist many objects in one commit."""
    for obj in objs:
        session.add(obj)
    session.commit()
    for obj in objs:
        session.refresh(obj)
    return objs


def get[T: SQLModel](session: Session, model: type[T], obj_id: uuid.UUID) -> T | None:
    """Fetch one row by primary key, or ``None``."""
    return session.get(model, obj_id)


def list_all[T: SQLModel](session: Session, model: type[T]) -> list[T]:
    """Return all rows of ``model`` (unfiltered — callers scope by tenant)."""
    return list(session.exec(select(model)).all())
