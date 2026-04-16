from __future__ import annotations

from typing import Any

from fastapi import status
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


def error_payload(code: str, message: str, details: dict[str, Any] | None = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        }
    }


def api_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_payload(code, message, details),
    )


def invalid_credentials() -> ApiError:
    return ApiError(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="invalid_credentials",
        message="Identificador o contrasena incorrectos.",
    )


def unauthorized(message: str = "Autenticacion requerida.") -> ApiError:
    return ApiError(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="unauthorized",
        message=message,
    )


def forbidden(message: str = "No tienes permisos para realizar esta accion.") -> ApiError:
    return ApiError(
        status_code=status.HTTP_403_FORBIDDEN,
        code="permission_denied",
        message=message,
    )


def not_found(message: str = "Recurso no encontrado.") -> ApiError:
    return ApiError(
        status_code=status.HTTP_404_NOT_FOUND,
        code="not_found",
        message=message,
    )


def validation_error(message: str, details: dict[str, Any] | None = None) -> ApiError:
    return ApiError(
        status_code=status.HTTP_400_BAD_REQUEST,
        code="validation_error",
        message=message,
        details=details,
    )
