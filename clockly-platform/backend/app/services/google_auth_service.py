from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


class GoogleAuthError(ValueError):
    """Raised when Google OAuth cannot validate the user identity."""


@dataclass(frozen=True)
class GoogleIdentity:
    google_id: str
    email: str
    full_name: str


class GoogleAuthService:
    def authorization_url(self, *, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code_for_identity(
        self,
        *,
        code: str,
        redirect_uri: str,
    ) -> GoogleIdentity:
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            raise GoogleAuthError("Google OAuth no esta configurado.")

        async with httpx.AsyncClient(timeout=10.0) as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if token_response.status_code >= 400:
                raise GoogleAuthError("Google no pudo validar el codigo de acceso.")
            token_data = token_response.json()

            id_token = token_data.get("id_token")
            access_token = token_data.get("access_token")
            if not id_token or not access_token:
                raise GoogleAuthError("Google no devolvio una identidad valida.")

            token_info = await self._validate_id_token(client, id_token)
            user_info = await self._load_userinfo(client, access_token)

        google_id = str(token_info.get("sub") or user_info.get("sub") or "").strip()
        email = str(token_info.get("email") or user_info.get("email") or "").strip().lower()
        full_name = str(user_info.get("name") or token_info.get("name") or email).strip()

        if not google_id or not email:
            raise GoogleAuthError("Google no devolvio email o identificador.")
        if str(token_info.get("email_verified", "")).lower() not in {"true", "1"}:
            raise GoogleAuthError("El email de Google no esta verificado.")

        return GoogleIdentity(google_id=google_id, email=email, full_name=full_name)

    async def _validate_id_token(self, client: httpx.AsyncClient, id_token: str) -> dict:
        response = await client.get(GOOGLE_TOKENINFO_URL, params={"id_token": id_token})
        if response.status_code >= 400:
            raise GoogleAuthError("No se pudo validar el token de Google.")
        data = response.json()
        if data.get("aud") != GOOGLE_CLIENT_ID:
            raise GoogleAuthError("El token de Google no pertenece a esta aplicacion.")
        return data

    async def _load_userinfo(self, client: httpx.AsyncClient, access_token: str) -> dict:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code >= 400:
            raise GoogleAuthError("No se pudo cargar el perfil de Google.")
        return response.json()
