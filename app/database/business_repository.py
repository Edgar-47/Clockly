from app.database.connection import get_connection
from app.models.business import Business


class BusinessRepository:
    _SELECT_COLUMNS = """
        id, owner_user_id, business_name, business_type, login_code, slug,
        business_key, settings_json, last_accessed_at, is_active,
        created_at, updated_at
    """
    _QUALIFIED_SELECT_COLUMNS = """
        b.id, b.owner_user_id, b.business_name, b.business_type, b.login_code,
        b.slug, b.business_key, b.settings_json, b.last_accessed_at,
        b.is_active, b.created_at, b.updated_at
    """

    def create(
        self,
        *,
        business_id: str,
        owner_user_id: int,
        business_name: str,
        business_type: str,
        login_code: str,
        slug: str,
        business_key: str,
        settings_json: str = "{}",
        mark_default: bool = True,
        include_legacy_records: bool = False,
    ) -> Business:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO businesses
                    (
                        id, owner_user_id, business_name, business_type,
                        login_code, slug, business_key, settings_json
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    business_id,
                    owner_user_id,
                    business_name,
                    business_type,
                    login_code,
                    slug,
                    business_key,
                    settings_json,
                ),
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO business_members
                    (business_id, user_id, member_role, is_default)
                VALUES (?, ?, 'owner', ?)
                """,
                (business_id, owner_user_id, int(mark_default)),
            )
            connection.execute(
                "UPDATE users SET last_business_id = ? WHERE id = ?",
                (business_id, owner_user_id),
            )

            if include_legacy_records:
                self._attach_legacy_records(connection, business_id)

            row = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM businesses
                WHERE id = ?
                """,
                (business_id,),
            ).fetchone()

        if row is None:
            raise RuntimeError("No se pudo crear el negocio.")
        return Business.from_row(row)

    def add_member(
        self,
        *,
        business_id: str,
        user_id: int,
        member_role: str,
        is_default: bool = False,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO business_members
                    (business_id, user_id, member_role, is_default)
                VALUES (?, ?, ?, ?)
                """,
                (business_id, user_id, member_role, int(is_default)),
            )

    def count_all(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) FROM businesses").fetchone()
        return int(row[0]) if row else 0

    def count_for_user(self, user_id: int) -> int:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*)
                FROM businesses b
                JOIN business_members bm ON bm.business_id = b.id
                WHERE bm.user_id = ?
                  AND b.is_active = 1
                """,
                (user_id,),
            ).fetchone()
        return int(row[0]) if row else 0

    def get_by_id(self, business_id: str) -> Business | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM businesses
                WHERE id = ?
                """,
                (business_id,),
            ).fetchone()
        return Business.from_row(row) if row else None

    def get_by_login_code(self, login_code: str) -> Business | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM businesses
                WHERE LOWER(login_code) = LOWER(?)
                  AND is_active = 1
                LIMIT 1
                """,
                (login_code,),
            ).fetchone()
        return Business.from_row(row) if row else None

    def list_for_user(self, user_id: int) -> list[Business]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {self._QUALIFIED_SELECT_COLUMNS}
                FROM businesses b
                JOIN business_members bm ON bm.business_id = b.id
                WHERE bm.user_id = ?
                  AND b.is_active = 1
                ORDER BY
                    CASE WHEN b.id = (
                        SELECT last_business_id FROM users WHERE id = ?
                    ) THEN 0 ELSE 1 END,
                    bm.is_default DESC,
                    COALESCE(bm.last_accessed_at, b.last_accessed_at, b.created_at) DESC,
                    b.business_name COLLATE NOCASE
                """,
                (user_id, user_id),
            ).fetchall()
        return [Business.from_row(row) for row in rows]

    def mark_accessed(self, *, business_id: str, user_id: int, accessed_at: str) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE businesses
                SET last_accessed_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (accessed_at, business_id),
            )
            connection.execute(
                """
                UPDATE business_members
                SET last_accessed_at = ?
                WHERE business_id = ? AND user_id = ?
                """,
                (accessed_at, business_id, user_id),
            )
            connection.execute(
                "UPDATE users SET last_business_id = ? WHERE id = ?",
                (business_id, user_id),
            )

    def user_has_access(self, *, business_id: str, user_id: int) -> bool:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM business_members bm
                JOIN businesses b ON b.id = bm.business_id
                WHERE bm.business_id = ?
                  AND bm.user_id = ?
                  AND b.is_active = 1
                LIMIT 1
                """,
                (business_id, user_id),
            ).fetchone()
        return row is not None

    def _attach_legacy_records(self, connection, business_id: str) -> None:
        rows = connection.execute("SELECT id, role FROM users").fetchall()
        for row in rows:
            member_role = "admin" if row["role"] == "admin" else "employee"
            connection.execute(
                """
                INSERT OR IGNORE INTO business_members
                    (business_id, user_id, member_role, is_default)
                VALUES (?, ?, ?, 1)
                """,
                (business_id, row["id"], member_role),
            )

        connection.execute(
            """
            UPDATE attendance_sessions
            SET business_id = ?
            WHERE business_id IS NULL
            """,
            (business_id,),
        )
        connection.execute(
            """
            UPDATE time_entries
            SET business_id = ?
            WHERE business_id IS NULL
            """,
            (business_id,),
        )
