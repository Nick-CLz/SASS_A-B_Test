"""Domain errors that map to typed HTTP responses.

Services raise these; a handler in ``app.main`` renders them as
``{"error": {"code", "message"}}`` (see docs/06-api-and-sdk.md).
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for expected, client-facing errors."""

    status_code: int = 400
    code: str = "bad_request"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404
    code = "not_found"


class ConflictError(DomainError):
    status_code = 409
    code = "conflict"


class InvariantError(DomainError):
    status_code = 422
    code = "invariant_violation"


class InvalidTransitionError(ConflictError):
    code = "invalid_transition"
