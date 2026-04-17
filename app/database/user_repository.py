from app.database.connection import get_connection
from app.models.user import User


class UserRepository:
    _SELECT = """
        id, email, full_name, google_id, auth_provider, password_hash,
        is_active, active, created_at, updated_at, first_name, last_name, dni,
        role, platform_role
    """

    def get_by_id(self, user_id: int) -> User | None:
        with get_connection() as connection:
            row = connection.execute(
                f"SELECT {self._SELECT} FROM users WHERE id = %s",
                (user_id,),
            ).fetchone()
        return User.from_row(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        clean_email = email.strip().lower()
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT}
                FROM users
                WHERE LOWER(email) = LOWER(%s)
                LIMIT 1
                """,
                (clean_email,),
            ).fetchone()
        return User.from_row(row) if row else None

    def get_by_google_id(self, google_id: str) -> User | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT}
                FROM users
                WHERE google_id = %s
                LIMIT 1
                """,
                (google_id,),
            ).fetchone()
        return User.from_row(row) if row else None

    def create_or_update_google_user(
        self,
        *,
        email: str,
        full_name: str,
        google_id: str,
    ) -> User:
        clean_email = email.strip().lower()
        clean_full_name = " ".join(full_name.strip().split()) or clean_email
        first_name, last_name = _split_name(clean_full_name)

        with get_connection() as connection:
            existing = connection.execute(
                """
                SELECT id, platform_role
                FROM users
                WHERE google_id = %s OR LOWER(email) = LOWER(%s)
                ORDER BY CASE WHEN google_id = %s THEN 0 ELSE 1 END
                LIMIT 1
                """,
                (google_id, clean_email, google_id),
            ).fetchone()

            if existing:
                if existing["platform_role"]:
                    raise ValueError("Usa el acceso interno de Superadmin.")
                user_id = int(existing["id"])
                connection.execute(
                    """
                    UPDATE users
                    SET email = %s,
                        full_name = %s,
                        google_id = %s,
                        auth_provider = 'google',
                        first_name = %s,
                        last_name = %s,
                        dni = CASE
                            WHEN dni IS NULL OR TRIM(dni) = '' THEN %s
                            ELSE dni
                        END,
                        role = 'admin',
                        active = TRUE,
                        is_active = TRUE,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        clean_email,
                        clean_full_name,
                        google_id,
                        first_name,
                        last_name,
                        clean_email,
                        user_id,
                    ),
                )
            else:
                row = connection.execute(
                    """
                    INSERT INTO users (
                        email, full_name, google_id, auth_provider,
                        first_name, last_name, dni, password_hash,
                        role, active, is_active
                    )
                    VALUES (%s, %s, %s, 'google', %s, %s, %s, NULL, 'admin', TRUE, TRUE)
                    RETURNING id
                    """,
                    (
                        clean_email,
                        clean_full_name,
                        google_id,
                        first_name,
                        last_name,
                        clean_email,
                    ),
                ).fetchone()
                user_id = int(row["id"])

            row = connection.execute(
                f"SELECT {self._SELECT} FROM users WHERE id = %s",
                (user_id,),
            ).fetchone()

        if row is None:
            raise RuntimeError("Google user could not be loaded after login.")
        return User.from_row(row)


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.split(maxsplit=1)
    if not parts:
        return "Usuario", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]
