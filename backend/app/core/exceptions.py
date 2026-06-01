"""Domain exceptions mapped to HTTP responses in app/api/errors.py."""

from __future__ import annotations


class DomainError(Exception):
    """Base for expected, mappable errors. `code` is the stable API error code."""

    code: str = "error"
    status_code: int = 400

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(DomainError):
    code = "validation_error"
    status_code = 400


class Unauthorized(DomainError):
    code = "unauthorized"
    status_code = 401


class Forbidden(DomainError):
    code = "forbidden"
    status_code = 403


class NotFound(DomainError):
    code = "not_found"
    status_code = 404


class Conflict(DomainError):
    code = "conflict"
    status_code = 409


class RateLimited(DomainError):
    code = "rate_limited"
    status_code = 429


class ProviderError(DomainError):
    code = "provider_error"
    status_code = 502


class NotImplementedYet(DomainError):
    code = "not_implemented"
    status_code = 501
