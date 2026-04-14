from app.database.connection import get_connection
from app.core.flow_debug import flow_log
from app.models.attendance_session import AttendanceSession


class AttendanceSessionRepository:
    _SELECT_COLUMNS = """
        id, business_id, user_id, clock_in_time, clock_out_time, is_active,
        total_seconds, notes, exit_note, incident_type,
        closed_by_admin, manual_close_reason, closed_by_user_id
    """

    def __init__(self, business_id: str | None = None) -> None:
        self.business_id = business_id

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
                    (business_id, user_id, clock_in_time, is_active, notes)
                VALUES (?, ?, ?, 1, ?)
                """,
                (self.business_id, user_id, clock_in_time, notes),
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
        clauses = ["user_id = ?", "is_active = 1"]
        params: list = [user_id]
        if self.business_id:
            clauses.append("business_id = ?")
            params.append(self.business_id)

        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM attendance_sessions
                WHERE {" AND ".join(clauses)}
                ORDER BY clock_in_time DESC, id DESC
                LIMIT 1
                """,
                params,
            ).fetchone()
        return AttendanceSession.from_row(row) if row else None

    def get_active_for_users(
        self,
        user_ids: list[int],
    ) -> dict[int, AttendanceSession]:
        if not user_ids:
            return {}

        placeholders = ",".join("?" for _ in user_ids)
        clauses = ["is_active = 1", f"user_id IN ({placeholders})"]
        params: list = list(user_ids)
        if self.business_id:
            clauses.append("business_id = ?")
            params.append(self.business_id)
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM attendance_sessions
                WHERE {" AND ".join(clauses)}
                """,
                params,
            ).fetchall()

        return {row["user_id"]: AttendanceSession.from_row(row) for row in rows}

    def get_latest_for_user(self, user_id: int) -> AttendanceSession | None:
        clauses = ["user_id = ?"]
        params: list = [user_id]
        if self.business_id:
            clauses.append("business_id = ?")
            params.append(self.business_id)

        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM attendance_sessions
                WHERE {" AND ".join(clauses)}
                ORDER BY clock_in_time DESC, id DESC
                LIMIT 1
                """,
                params,
            ).fetchone()
        return AttendanceSession.from_row(row) if row else None

    def clock_out(
        self,
        *,
        session_id: int,
        clock_out_time: str,
        total_seconds: int,
        notes: str | None = None,
        exit_note: str | None = None,
        incident_type: str | None = None,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE attendance_sessions
                SET clock_out_time = ?,
                    is_active = 0,
                    total_seconds = ?,
                    notes = COALESCE(?, notes),
                    exit_note = COALESCE(?, exit_note),
                    incident_type = COALESCE(?, incident_type)
                WHERE id = ? AND is_active = 1
                """,
                (
                    clock_out_time,
                    total_seconds,
                    notes,
                    exit_note,
                    incident_type,
                    session_id,
                ),
            )

    def admin_clock_out(
        self,
        *,
        session_id: int,
        clock_out_time: str,
        total_seconds: int,
        reason: str,
        closed_by_user_id: int,
        exit_note: str | None = None,
        incident_type: str | None = None,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE attendance_sessions
                SET clock_out_time = ?,
                    is_active = 0,
                    total_seconds = ?,
                    closed_by_admin = 1,
                    manual_close_reason = ?,
                    closed_by_user_id = ?,
                    exit_note = COALESCE(?, exit_note),
                    incident_type = COALESCE(?, incident_type)
                WHERE id = ? AND is_active = 1
                """,
                (
                    clock_out_time,
                    total_seconds,
                    reason,
                    closed_by_user_id,
                    exit_note,
                    incident_type,
                    session_id,
                ),
            )

    def list_with_user_names(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        user_id: int | None = None,
        is_active: int | None = None,
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

        if is_active is not None:
            clauses.append("s.is_active = ?")
            params.append(is_active)

        if self.business_id:
            clauses.append("s.business_id = ?")
            params.append(self.business_id)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        query = f"""
            SELECT
                s.id,
                s.business_id,
                s.user_id,
                TRIM(COALESCE(u.first_name, '') || ' ' || COALESCE(u.last_name, ''))
                    AS employee_name,
                u.dni,
                s.clock_in_time,
                s.clock_out_time,
                s.is_active,
                s.total_seconds,
                s.notes,
                s.exit_note,
                s.incident_type,
                s.closed_by_admin,
                s.manual_close_reason,
                s.closed_by_user_id
            FROM attendance_sessions s
            JOIN users u ON u.id = s.user_id
            {where}
            ORDER BY s.clock_in_time DESC, s.id DESC
        """
        flow_log(
            "repository.sessions.query",
            clauses=clauses,
            params=params,
        )

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()

        flow_log("repository.sessions.result", count=len(rows))
        return [dict(row) for row in rows]

    def list_exportable_sessions(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        user_id: int | None = None,
        is_active: int | None = None,
    ) -> list[dict]:
        """
        Return attendance_sessions joined with users for reports/exports.

        This is the canonical export query. The legacy time_entries table is
        intentionally not involved here.
        """
        return self.list_with_user_names(
            date_from=date_from,
            date_to=date_to,
            user_id=user_id,
            is_active=is_active,
        )

    def list_closed_overlapping(
        self,
        *,
        start: str,
        end: str,
        user_ids: list[int] | None = None,
    ) -> list[AttendanceSession]:
        clauses = [
            "is_active = 0",
            "clock_out_time IS NOT NULL",
            "clock_in_time < ?",
            "clock_out_time > ?",
        ]
        params: list = [end, start]

        if user_ids is not None:
            if not user_ids:
                return []
            placeholders = ",".join("?" for _ in user_ids)
            clauses.append(f"user_id IN ({placeholders})")
            params.extend(user_ids)

        if self.business_id:
            clauses.append("business_id = ?")
            params.append(self.business_id)

        query = f"""
            SELECT {self._SELECT_COLUMNS}
            FROM attendance_sessions
            WHERE {" AND ".join(clauses)}
            ORDER BY clock_in_time ASC, id ASC
        """

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()

        return [AttendanceSession.from_row(row) for row in rows]
