"""API key management: create (plaintext returned once), verify, list. Stored hashed."""

from __future__ import annotations

import hashlib
import secrets
import uuid

from sqlmodel import Session, select

from app.models.org import ApiKey
from app.services.repository import add


def _hash(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode()).hexdigest()


def create_api_key(
    session: Session, org_id: uuid.UUID, name: str, scopes: list[str]
) -> tuple[ApiKey, str]:
    """Create a key; return the row and the plaintext secret (shown to the caller once)."""
    plaintext = "mk_" + secrets.token_urlsafe(32)
    key = ApiKey(org_id=org_id, name=name, hashed_key=_hash(plaintext), scopes=scopes)
    add(session, key)
    return key, plaintext


def verify_key(session: Session, plaintext: str) -> ApiKey | None:
    """Return the ApiKey for a plaintext secret, or None."""
    return session.exec(select(ApiKey).where(ApiKey.hashed_key == _hash(plaintext))).first()


def list_api_keys(session: Session, org_id: uuid.UUID) -> list[ApiKey]:
    return list(session.exec(select(ApiKey).where(ApiKey.org_id == org_id)).all())
