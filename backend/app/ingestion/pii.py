"""Ingestion PII guard — no PII may reach the analytics store.

Privacy-first by construction (docs/01-product-vision.md): the unit id must be
pseudonymous and event/exposure properties must not carry PII. Rejected items are
reported with a reason (never silently dropped). Mirrors the SDK-side guard.
"""

from __future__ import annotations

import re
from typing import Any

_PII_KEYS = {
    "email",
    "e_mail",
    "mail",
    "phone",
    "phone_number",
    "ssn",
    "password",
    "name",
    "first_name",
    "last_name",
    "full_name",
    "address",
    "ip",
    "ip_address",
    "credit_card",
    "card_number",
}
_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def pii_reason(unit_id: str, properties: dict[str, Any]) -> str | None:
    """Return a rejection reason if PII is detected, else ``None``."""
    if not unit_id:
        return "unit_id must be a non-empty pseudonymous identifier"
    if _EMAIL_RE.search(unit_id):
        return "unit_id looks like an email; use a pseudonymous id"
    for key, value in properties.items():
        if key.lower() in _PII_KEYS:
            return f"property '{key}' looks like PII and must not be sent"
        if isinstance(value, str) and _EMAIL_RE.search(value):
            return f"property '{key}' value looks like an email"
    return None
