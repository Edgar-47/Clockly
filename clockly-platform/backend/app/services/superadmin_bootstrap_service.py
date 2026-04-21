from __future__ import annotations

from dataclasses import dataclass

from app.database.connection import get_connection
from app.models.plan_constants import PlatformRole
from app.utils.security import hash_password


@dataclass(frozen=True)
class SuperadminBootstrapResult:
    user_id: int
    email: str
    created: bool


class SuperadminBootstrapService:
    """Out-of-band provisioning for the internal owner console."""

    def create_or_update_superadmin(
        self,
        *,
        email: str,
        full_name: str,
        password: str,
        force_password_change: bool = False,
    ) -> SuperadminBootstrapResult:
        clean_email = (email or "").strip().lower()
        clean_name = " ".join((full_name or "").split())
        clean_password = password or ""

        if "@" not in clean_email:
            raise ValueError("El email del superadmin no es valido.")
        if len(clean_name) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres.")
        if len(clean_password) < 12:
            raise ValueError("La contrasena debe tener al menos 12 caracteres.")

        first_name, last_name = self._split_name(clean_name)
        password_hash = hash_password(clean_password)

        with get_connection() as conn:
            existing = conn.execute(
                """
                SELECT id
                FROM users
                WHERE LOWER(email) = LOWER(%s)
                   OR LOWER(dni) = LOWER(%s)
                LIMIT 1
                """,
                (clean_email, clean_email),
            ).fetchone()

            if existing:
                user_id = int(existing["id"])
                conn.execute(
                    """
                    UPDATE users
                    SET email = %s,
                        full_name = %s,
                        first_name = %s,
                        last_name = %s,
                        dni = %s,
                        password_hash = %s,
                        role = 'admin',
                        platform_role = %s,
                        active = TRUE,
                        is_active = TRUE,
                        force_password_change = %s,
                        auth_provider = 'password',
                        deactivated_at = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        clean_email,
                        clean_name,
                        first_name,
                        last_name,
                        clean_email,
                        password_hash,
                        PlatformRole.SUPERADMIN.value,
                        force_password_change,
                        user_id,
                    ),
                )
                return SuperadminBootstrapResult(user_id=user_id, email=clean_email, created=False)

            row = conn.execute(
                """
                INSERT INTO users (
                    email, full_name, first_name, last_name, dni, password_hash,
                    role, platform_role, active, is_active, force_password_change,
                    auth_provider
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'admin', %s, TRUE, TRUE, %s, 'password')
                RETURNING id
                """,
                (
                    clean_email,
                    clean_name,
                    first_name,
                    last_name,
                    clean_email,
                    password_hash,
                    PlatformRole.SUPERADMIN.value,
                    force_password_change,
                ),
            ).fetchone()

        return SuperadminBootstrapResult(
            user_id=int(row["id"]),
            email=clean_email,
            created=True,
        )

    def _split_name(self, full_name: str) -> tuple[str, str]:
        first, _, last = full_name.partition(" ")
        return first or "Superadmin", last

