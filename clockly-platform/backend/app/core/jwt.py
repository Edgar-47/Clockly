from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from app.config import SECRET_KEY, SESSION_MAX_AGE


class TokenError(ValueError):
    """Raised when an API access token is missing, invalid, or expired."""


def create_access_token(
    *,
    user_id: int,
    role: str,
    active_business_id: str | None = None,
    expires_in: int | None = None,
) -> str:
    issued_at = int(time.time())
    ttl = int(expires_in or SESSION_MAX_AGE)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "active_business_id": active_business_id,
        "iat": issued_at,
        "exp": issued_at + ttl,
        "typ": "access",
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = ".".join(
        [
            _b64_json(header),
            _b64_json(payload),
        ]
    )
    signature = _sign(signing_input)
    return f"{signing_input}.{signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature = token.split(".", 2)
    except ValueError as exc:
        raise TokenError("Token mal formado.") from exc

    signing_input = f"{header_part}.{payload_part}"
    expected_signature = _sign(signing_input)
    if not hmac.compare_digest(signature, expected_signature):
        raise TokenError("Firma de token no valida.")

    header = _decode_json(header_part)
    if header.get("alg") != "HS256":
        raise TokenError("Algoritmo de token no permitido.")

    payload = _decode_json(payload_part)
    if payload.get("typ") != "access":
        raise TokenError("Tipo de token no permitido.")
    if int(payload.get("exp") or 0) < int(time.time()):
        raise TokenError("Token expirado.")
    if not payload.get("sub"):
        raise TokenError("Token sin sujeto.")
    return payload


def _sign(value: str) -> str:
    digest = hmac.new(
        SECRET_KEY.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64_bytes(digest)


def _b64_json(value: dict[str, Any]) -> str:
    data = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return _b64_bytes(data)


def _b64_bytes(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode_json(value: str) -> dict[str, Any]:
    try:
        padded = value + "=" * (-len(value) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        parsed = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise TokenError("Token no decodificable.") from exc
    if not isinstance(parsed, dict):
        raise TokenError("Payload de token no valido.")
    return parsed
