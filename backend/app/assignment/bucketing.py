"""Deterministic bucketing.

**Hash construction (the cross-language contract — SDKs must match byte-for-byte):**

    digest = SHA-256( f"{salt}:{unit_id}".encode("utf-8") )
    value  = int.from_bytes(digest[:8], "big")   # first 8 bytes, big-endian uint64
    bucket = value / 2**64                        # in [0, 1)

Independence across experiments comes from a distinct ``salt`` per experiment; within an
experiment we derive independent sub-buckets by composing the salt (e.g. ``"{salt}:variant"``).
"""

from __future__ import annotations

import hashlib

_UINT64 = 2**64


def bucket(salt: str, unit_id: str) -> float:
    """Map ``(salt, unit_id)`` deterministically into ``[0, 1)``."""
    digest = hashlib.sha256(f"{salt}:{unit_id}".encode()).digest()
    value = int.from_bytes(digest[:8], "big")
    return value / _UINT64
