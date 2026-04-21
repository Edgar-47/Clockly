"""
app/database/audit_log_repository.py

Read/write access to the audit_logs table.
"""
from __future__ import annotations

import json

from app.database.connection import get_connection
from app.models.audit_log import AuditLog


class AuditLogRepository:

    def create(
        self,
        *,
        actor_user_id: int | None,
        actor_email: str | None,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        business_id: str | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (
                    actor_user_id, actor_email, action,
                    resource_type, resource_id, business_id,
                    old_value, new_value, metadata, ip_address
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    actor_user_id,
                    actor_email,
                    action,
                    resource_type,
                    str(resource_id) if resource_id is not None else None,
                    business_id,
                    json.dumps(old_value) if old_value is not None else None,
                    json.dumps(new_value) if new_value is not None else None,
                    json.dumps(metadata) if metadata is not None else None,
                    ip_address,
                ),
            )

    def list_recent(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        action_filter: str | None = None,
        resource_type: str | None = None,
        business_id: str | None = None,
    ) -> list[AuditLog]:
        conditions = []
        params: list = []

        if action_filter:
            conditions.append("al.action ILIKE %s")
            params.append(f"%{action_filter}%")
        if resource_type:
            conditions.append("al.resource_type = %s")
            params.append(resource_type)
        if business_id:
            conditions.append("al.business_id = %s")
            params.append(business_id)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        params.extend([limit, offset])
        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT
                    al.*,
                    u.full_name AS actor_name,
                    b.business_name
                FROM audit_logs al
                LEFT JOIN users u ON u.id = al.actor_user_id
                LEFT JOIN businesses b ON b.id = al.business_id
                {where}
                ORDER BY al.created_at DESC
                LIMIT %s OFFSET %s
                """,
                params,
            ).fetchall()
        return [AuditLog.from_row(r) for r in rows]

    def count(
        self,
        *,
        action_filter: str | None = None,
        resource_type: str | None = None,
        business_id: str | None = None,
    ) -> int:
        conditions = []
        params: list = []

        if action_filter:
            conditions.append("action ILIKE %s")
            params.append(f"%{action_filter}%")
        if resource_type:
            conditions.append("resource_type = %s")
            params.append(resource_type)
        if business_id:
            conditions.append("business_id = %s")
            params.append(business_id)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        with get_connection() as conn:
            row = conn.execute(
                f"SELECT COUNT(*) AS n FROM audit_logs {where}", params
            ).fetchone()
        return row["n"] if row else 0
