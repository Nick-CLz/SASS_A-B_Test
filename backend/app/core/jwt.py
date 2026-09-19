"""Minimal HS256 JWT verification (stdlib only) for SSO bearer tokens.

Enough to accept signed tokens from an identity provider in the demo without a third-party
dependency. Production should use a vetted library with JWKS / RS256 (roadmap). Verifies the
signature in constant time and the ``exp`` claim; raises ``UnauthorizedError`` on any failure.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from app.core.errors import UnauthorizedError


def _b64url_decode(segment: str) -> bytes:
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def encode_hs256(claims: dict[str, Any], secret: str) -> str:
    """Mint an HS256 JWT (used by tests and a simple token issuer)."""
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64url_encode(json.dumps(claims, separators=(",", ":")).encode())
    signing_input = f"{header}.{body}".encode()
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header}.{body}.{_b64url_encode(signature)}"


def decode_hs256(token: str, secret: str, *, audience: str | None = None) -> dict[str, Any]:
    """Verify an HS256 JWT and return its claims, or raise ``UnauthorizedError``."""
    try:
        header_b64, body_b64, sig_b64 = token.split(".")
    except ValueError as exc:
        raise UnauthorizedError("malformed bearer token") from exc

    signing_input = f"{header_b64}.{body_b64}".encode()
    expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
        raise UnauthorizedError("bad token signature")

    try:
        claims: dict[str, Any] = json.loads(_b64url_decode(body_b64))
    except ValueError as exc:
        raise UnauthorizedError("malformed token payload") from exc

    exp = claims.get("exp")
    if exp is not None and time.time() > float(exp):
        raise UnauthorizedError("token expired")
    if audience is not None and claims.get("aud") != audience:
        raise UnauthorizedError("token audience mismatch")
    return claims
