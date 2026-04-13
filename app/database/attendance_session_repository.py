from app.database.connection import get_connection
from app.models.attendance_session import AttendanceSession


class AttendanceSessionRepository:
    _SELECT_COLUMNS = """
        id, user_id, clock_in_time, clock_out_time, is_active, total_seconds, notes
    """

    def create(
        self,
        *,
        user_id: int,
        clock_in_time: str,
        notes: str | None = None,
    ) -> int:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO attendance_sessions
                    (user_id, clock_in_time, is_active, notes)
                VALUES (?, ?, 1, ?)
                """,
                (user_id, clock_in_time, notes),
            )
            return int(cursor.lastrowid)

    def get_by_id(self, session_id: int) -> AttendanceSession | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM attendance_sessions
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
        return AttendanceSession.from_row(row) if row else None

    def get_active_for_user(self, user_id: int) -> AttendanceSession | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM attendance_sessions
                WHERE user_id = ? AND is_active = 1
                ORDER BY clock_in_time DESC, id DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        return AttendanceSession.from_row(row) if row else None

    def get_active_for_users(
        self,
        user_ids: list[int],
    ) -> dict[int, AttendanceSession]:
        if not user_ids:
            return {}

        placeholders = ",".join("?" for _ in user_ids)
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM attendance_sessions
                WHERE is_active = 1
                  AND user_id IN ({placeholders})
                """,
                user_ids,
            ).fetchall()

        return {row["user_id"]: AttendanceSession.from_row(row) for row in rows}

    def get_latest_for_user(self, user_id: int) -> AttendanceSession | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM attendance_sessions
                WHERE user_id = ?
                ORDER BY clock_in_time DESC, id DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        return AttendanceSession.from_row(row) if row else None

    def clock_out(
        self,
        *,
        session_id: int,
        clock_out_time: str,
        total_seconds: int,
        notes: str | None = None,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE attendance_sessions
                SET clock_out_time = ?,
                    is_active = 0,
                    total_seconds = ?,
                    notes = COALESCE(?, notes)
                WHERE id = ? AND is_active = 1
                """,
                (clock_out_time, total_seconds, notes, session_id),
            )

    def list_with_user_names(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        user_id: int | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list = []

        if date_from:
            clauses.append("s.clock_in_time >= ?")
            params.append(date_from + " 00:00:00")

        if date_to:
            clauses.append("s.clock_in_time <= ?")
            params.append(date_to + " 23:59:59")

        if user_id is not None:
            clauses.append("s.user_id = ?")
            params.append(user_id)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        query = f"""
            SELECT
                s.id,
                s.user_id,
                TRIM(COALESCE(u.first_name, '') || ' ' || COALESCE(u.last_name, ''))
                    AS employee_name,
                u.dni,
                s.clock_in_time,
                s.clock_out_time,
                s.is_active,
                s.total_seconds,
                s.notes
            FROM attendance_sessions s
            JOIN users u ON u.id = s.user_id
            {where}
            ORDER BY s.clock_in_time DESC, s.id DESC
        """

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()

        return [dict(row) for row in rows]
