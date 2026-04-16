from app.database.connection import get_connection
from app.models.business_user import BusinessUser


ADMIN_LIKE_ROLES = {"owner", "admin", "manager"}
BUSINESS_ROLES = {"owner", "admin", "manager", "employee", "kiosk_device"}


class BusinessUserRepository:
    def add_or_update(
        self,
        *,
        business_id: str,
        user_id: int,
        role: str,
        status: str = "active",
    ) -> BusinessUser:
        clean_role = role.strip().lower()
        if clean_role not in BUSINESS_ROLES:
            raise ValueError("Rol de negocio no valido.")
        clean_status = status.strip().lower()
        if clean_status not in {"active", "invited", "disabled"}:
            clean_status = "active"

        with get_connection() as connection:
            row = connection.execute(
                """
                INSERT INTO business_users
                    (business_id, user_id, role, status)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (business_id, user_id) DO UPDATE SET
                    role = EXCLUDED.role,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, business_id, user_id, role, status,
                          invited_at, created_at, updated_at
                """,
                (business_id, user_id, clean_role, clean_status),
            ).fetchone()
            self._sync_legacy_member(
                connection,
                business_id=business_id,
                user_id=user_id,
                role=clean_role,
            )
        return BusinessUser.from_row(row)

    def get(self, *, business_id: str, user_id: int) -> BusinessUser | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, business_id, user_id, role, status,
                       invited_at, created_at, updated_at
                FROM business_users
                WHERE business_id = %s
                  AND user_id = %s
                LIMIT 1
                """,
                (business_id, user_id),
            ).fetchone()
        return BusinessUser.from_row(row) if row else None

    def get_active_role(self, *, business_id: str, user_id: int) -> str | None:
        member = self.get(business_id=business_id, user_id=user_id)
        if member and member.status == "active":
            return member.role
        return None

    def user_has_access(self, *, business_id: str, user_id: int) -> bool:
        return self.get_active_role(business_id=business_id, user_id=user_id) is not None

    def count_active_by_roles(self, *, business_id: str, roles: set[str]) -> int:
        if not roles:
            return 0
        placeholders = ", ".join("%s" for _ in roles)
        params: list = [business_id, *sorted(roles)]
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM business_users bu
                JOIN users u ON u.id = bu.user_id
                WHERE bu.business_id = %s
                  AND bu.role IN ({placeholders})
                  AND bu.status = 'active'
                  AND u.active IS TRUE
                """,
                params,
            ).fetchone()
        return int(row["count"]) if row else 0

    def list_for_business(self, business_id: str) -> list[BusinessUser]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, business_id, user_id, role, status,
                       invited_at, created_at, updated_at
                FROM business_users
                WHERE business_id = %s
                ORDER BY
                    CASE role
                        WHEN 'owner' THEN 0
                        WHEN 'admin' THEN 1
                        WHEN 'manager' THEN 2
                        WHEN 'employee' THEN 3
                        ELSE 4
                    END,
                    created_at
                """,
                (business_id,),
            ).fetchall()
        return [BusinessUser.from_row(row) for row in rows]

    def _sync_legacy_member(self, connection, *, business_id: str, user_id: int, role: str) -> None:
        legacy_role = role if role in {"owner", "admin", "employee"} else "admin"
        connection.execute(
            """
            INSERT INTO business_members
                (business_id, user_id, member_role)
            VALUES (%s, %s, %s)
            ON CONFLICT (business_id, user_id) DO UPDATE SET
                member_role = EXCLUDED.member_role
            """,
            (business_id, user_id, legacy_role),
        )
