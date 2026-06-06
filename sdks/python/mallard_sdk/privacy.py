"""Client-side PII guard.

Mallard is privacy-first: the unit id must be pseudonymous and event/attribute
properties must not carry PII. This is a best-effort client check; the server enforces
the workspace allow-list authoritatively (see docs/01-product-vision.md).
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


class PIIError(ValueError):
    """Raised when a value looks like personally identifiable information."""


def assert_pseudonymous_unit(unit_id: str) -> None:
    if not unit_id:
        raise PIIError("unit_id must be a non-empty pseudonymous identifier")
    if _EMAIL_RE.search(unit_id):
        raise PIIError("unit_id looks like an email; use a pseudonymous id")


def assert_no_pii(properties: dict[str, Any]) -> None:
    for key, value in properties.items():
        if key.lower() in _PII_KEYS:
            raise PIIError(f"property {key!r} looks like PII and must not be sent")
        if isinstance(value, str) and _EMAIL_RE.search(value):
            raise PIIError(f"property {key!r} value looks like an email")
