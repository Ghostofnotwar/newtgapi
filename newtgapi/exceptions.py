"""Exceptions for newtgapi."""

from __future__ import annotations


class NewTgApiError(Exception):
    """Base exception."""


class ValidationError(NewTgApiError, ValueError):
    """Raised when a parameter fails local validation."""


class TelegramAPIError(NewTgApiError):
    """Raised when the Bot API returns ``ok: false`` or an HTTP error."""

    def __init__(
        self,
        message: str,
        *,
        error_code: int | None = None,
        description: str | None = None,
        parameters: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.description = description or message
        self.parameters = parameters or {}

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"TelegramAPIError({self.error_code!r}, {self.description!r})"


class NetworkError(NewTgApiError):
    """Raised on transport-level failures (DNS, timeout, connection reset)."""


class UnauthorizedError(TelegramAPIError):
    """401 — invalid token."""


class ForbiddenError(TelegramAPIError):
    """403 — bot was blocked / not enough rights."""


class NotFoundError(TelegramAPIError):
    """404 — method / resource not found (e.g. unknown unique gift name)."""


class TooManyRequestsError(TelegramAPIError):
    """429 — rate limited. ``retry_after`` mirrors ``parameters.retry_after``."""

    @property
    def retry_after(self) -> int | None:
        value = self.parameters.get("retry_after")
        return int(value) if value is not None else None
