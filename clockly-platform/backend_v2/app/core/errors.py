from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ErrorDetail:
    code: str
    message: str
    details: dict[str, Any] | None = None


class AppError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.detail = ErrorDetail(code=self.code, message=message, details=details)


class AuthenticationError(AppError):
    status_code = 401
    code = "unauthorized"


class PermissionDenied(AppError):
    status_code = 403
    code = "forbidden"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"

