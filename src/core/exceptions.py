"""Domain exceptions; map to HTTP via handlers (avoid HTTPException in services)."""

from typing import ClassVar


class AppError(Exception):
    """Base class with optional machine-readable code."""

    default_code = "APP_ERROR"

    http_status: ClassVar[int] = 500

    def __init__(self, message: str, *, code: str | None = None) -> None:
        self.message = message

        self.code = code or self.default_code

        super().__init__(message)


class NotFoundError(AppError):
    default_code = "NOT_FOUND"

    http_status: ClassVar[int] = 404


class ConflictError(AppError):
    default_code = "CONFLICT"

    http_status: ClassVar[int] = 409


class GoneError(AppError):
    default_code = "GONE"

    http_status: ClassVar[int] = 410


class ForbiddenError(AppError):
    default_code = "FORBIDDEN"

    http_status: ClassVar[int] = 403


class UnauthorizedError(AppError):
    default_code = "UNAUTHORIZED"

    http_status: ClassVar[int] = 401


class ValidationError(AppError):
    """Business or request validation failure (contract: 400 + VALIDATION_ERROR)."""

    default_code = "VALIDATION_ERROR"

    http_status: ClassVar[int] = 400

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: list[object] | None = None,
        issues: list[object] | None = None,
    ) -> None:
        super().__init__(message, code=code)

        self.details = details if details is not None else []

        self.issues = issues if issues is not None else []


class UnprocessableEntityError(AppError):
    """Semantic / state conflict (e.g. business rule); HTTP 422."""

    default_code = "UNPROCESSABLE_ENTITY"

    http_status: ClassVar[int] = 422
