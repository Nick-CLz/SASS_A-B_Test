"""Deterministic bucketing — byte-for-byte identical to the server.

See ``backend/app/assignment/bucketing.py`` and ``sdks/fixtures/bucketing.json``.
"""

from __future__ import annotations

import hashlib

_UINT64 = 2**64


def bucket(salt: str, unit_id: str) -> float:
    """Map ``(salt, unit_id)`` deterministically into ``[0, 1)``."""
    digest = hashlib.sha256(f"{salt}:{unit_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / _UINT64
