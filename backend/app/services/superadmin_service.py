"""
app/services/superadmin_service.py

Business logic for superadmin operations: business management, subscription control,
internal user management.  All mutating methods write to audit_logs via AuditService.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.database.connection import get_connection
from app.database.plan_repository import PlanRepository
from app.database.subscription_repository import SubscriptionRepository
from app.models.plan_constants import PLATFORM_ADMIN_ROLES, BusinessRole, PlatformRole
from app.utils.security import hash_password


# ---------------------------------------------------------------------------
# Typed results
# ---------------------------------------------------------------------------

@dataclass
class BusinessRow:
    id: str
    business_name: str
    business_type: str
    primary_email: str | None
    phone: str | None
    is_active: bool
    created_at: str | None
    last_accessed_at: str | None
    suspended_at: str | None
    suspended_reason: str | None
    archived_at: str | None
    owner_email: str | None
    plan_code: str
    plan_name: str
    subscription_status: str
    employee_count: int
    admin_count: int
    session_count: int

    @property
    def status_label(self) -> str:
        if self.archived_at:
            return "archived"
        if self.suspended_at:
            return "suspended"
        if self.subscription_status in ("trial", "trialing"):
            return "trial"
        if not self.is_active:
            return "inactive"
        return "active"

    @property
    def status_css(self) -> str:
        m = {
            "active": "badge--success",
            "inactive": "badge--muted",
            "suspended": "badge--warning",
            "trial": "badge--blue",
            "archived": "badge--danger",
        }
        return m.get(self.status_label, "badge--muted")


@dataclass
class SubscriptionRow:
    id: int
    business_id: str
    business_name: str
    plan_id: int
    plan_name: str
    plan_code: str
    status: str
    billing_cycle: str
    current_period_start: str | None
    current_period_end: str | None
    renewal_date: str | None
    trial_ends_at: str | None
    cancel_at: str | None
    cancelled_at: str | None
    paused_at: str | None
    payment_status: str
    notes: str | None
    price_monthly: Decimal
    created_at: str | None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class SuperadminService:

    # ── Businesses ──────────────────────────────────────────────────────────

    def list_businesses(
        self,
        *,
        search: str | None = None,
        status_filter: str | None = None,
        plan_filter: str | None = None,
        page: int = 1,
        per_page: int = 30,
    ) -> tuple[list[BusinessRow], int]:
        conditions = ["1=1"]
        params: list = []

        if search:
            conditions.append(
                "(b.business_name ILIKE %s OR u.email ILIKE %s OR b.primary_email ILIKE %s OR b.id ILIKE %s OR p.code ILIKE %s)"
            )
            like = f"%{search}%"
            params.extend([like, like, like, like, like])

        if status_filter == "active":
            conditions.append("b.is_active IS TRUE AND b.suspended_at IS NULL AND b.archived_at IS NULL")
        elif status_filter == "suspended":
            conditions.append("b.suspended_at IS NOT NULL AND b.archived_at IS NULL")
        elif status_filter == "trial":
            conditions.append("s.status IN ('trial', 'trialing')")
        elif status_filter == "inactive":
            conditions.append("b.is_active IS FALSE AND b.archived_at IS NULL")
        elif status_filter == "archived":
            conditions.append("b.archived_at IS NOT NULL")
        elif status_filter == "cancelled":
            conditions.append("s.status IN ('cancelled', 'canceled')")
        else:
            conditions.append("b.archived_at IS NULL")

        if plan_filter:
            conditions.append("p.code = %s")
            params.append(plan_filter)

        where = "WHERE " + " AND ".join(conditions)
        offset = (page - 1) * per_page

        with get_connection() as conn:
            count_row = conn.execute(
                f"""
                SELECT COUNT(*) AS n
                FROM businesses b
                LEFT JOIN users u ON u.id = b.owner_user_id
                LEFT JOIN subscriptions s ON s.business_id = b.id
                LEFT JOIN plans p ON p.id = s.plan_id
                {where}
                """,
                params,
            ).fetchone()
            total = count_row["n"] if count_row else 0

            params_page = params + [per_page, offset]
            rows = conn.execute(
                f"""
                SELECT
                    b.id, b.business_name, b.business_type, b.primary_email, b.phone,
                    b.is_active, b.created_at, b.last_accessed_at,
                    b.suspended_at, b.suspended_reason, b.archived_at,
                    u.email AS owner_email,
                    COALESCE(p.code, 'free') AS plan_code,
                    COALESCE(p.name, 'Free') AS plan_name,
                    COALESCE(s.status, 'active') AS subscription_status,
                    (
                        SELECT COUNT(*)
                        FROM business_users bu
                        JOIN users eu ON eu.id = bu.user_id
                        WHERE bu.business_id = b.id
                          AND bu.role = 'employee'
                          AND bu.status = 'active'
                          AND eu.active IS TRUE
                    ) AS employee_count,
                    (
                        SELECT COUNT(*)
                        FROM business_users bu
                        JOIN users au ON au.id = bu.user_id
                        WHERE bu.business_id = b.id
                          AND bu.role IN ('owner', 'admin')
                          AND bu.status = 'active'
                          AND au.active IS TRUE
                    ) AS admin_count,
                    (
                        SELECT COUNT(*) FROM attendance_sessions a
                        WHERE a.business_id = b.id
                    ) AS session_count
                FROM businesses b
                LEFT JOIN users u ON u.id = b.owner_user_id
                LEFT JOIN subscriptions s ON s.business_id = b.id
                LEFT JOIN plans p ON p.id = s.plan_id
                {where}
                ORDER BY b.created_at DESC
                LIMIT %s OFFSET %s
                """,
                params_page,
            ).fetchall()

        result = [
            BusinessRow(
                id=str(r["id"]),
                business_name=r["business_name"],
                business_type=r["business_type"],
                primary_email=r.get("primary_email"),
                phone=r.get("phone"),
                is_active=bool(r["is_active"]),
                created_at=str(r["created_at"]) if r["created_at"] else None,
                last_accessed_at=str(r["last_accessed_at"]) if r["last_accessed_at"] else None,
                suspended_at=str(r["suspended_at"]) if r["suspended_at"] else None,
                suspended_reason=r.get("suspended_reason"),
                archived_at=str(r["archived_at"]) if r["archived_at"] else None,
                owner_email=r.get("owner_email"),
                plan_code=r["plan_code"],
                plan_name=r["plan_name"],
                subscription_status=r["subscription_status"],
                employee_count=r["employee_count"],
                admin_count=r["admin_count"],
                session_count=r["session_count"],
            )
            for r in rows
        ]
        return result, total

    def get_business_detail(self, business_id: str) -> dict | None:
        with get_connection() as conn:
            biz = conn.execute(
                """
                SELECT
                    b.*,
                    u.email AS owner_email, u.full_name AS owner_name,
                    p.name AS plan_name, p.code AS plan_code,
                    p.price_monthly, p.max_employees,
                    s.status AS subscription_status, s.id AS sub_id,
                    s.billing_cycle, s.trial_ends_at, s.payment_status,
                    s.current_period_start, s.current_period_end,
                    s.notes AS sub_notes, s.created_at AS sub_created_at
                FROM businesses b
                LEFT JOIN users u ON u.id = b.owner_user_id
                LEFT JOIN subscriptions s ON s.business_id = b.id
                LEFT JOIN plans p ON p.id = s.plan_id
                WHERE b.id = %s
                """,
                (business_id,),
            ).fetchone()
            if not biz:
                return None

            emp_count = conn.execute(
                """
                SELECT COUNT(*) AS n
                FROM business_users bu
                JOIN users u ON u.id = bu.user_id
                WHERE bu.business_id = %s
                  AND bu.role = 'employee'
                  AND bu.status = 'active'
                  AND u.active IS TRUE
                """,
                (business_id,),
            ).fetchone()["n"]

            admin_count = conn.execute(
                """
                SELECT COUNT(*) AS n FROM business_users
                WHERE business_id = %s AND role IN ('owner','admin') AND status = 'active'
                """,
                (business_id,),
            ).fetchone()["n"]

            session_count = conn.execute(
                "SELECT COUNT(*) AS n FROM attendance_sessions WHERE business_id = %s",
                (business_id,),
            ).fetchone()["n"]

            recent_sessions = conn.execute(
                """
                SELECT a.id, u.full_name AS employee_name,
                       a.clock_in_time, a.clock_out_time, a.is_active
                FROM attendance_sessions a
                LEFT JOIN users u ON u.id = a.user_id
                WHERE a.business_id = %s
                ORDER BY a.clock_in_time DESC
                LIMIT 5
                """,
                (business_id,),
            ).fetchall()

            members = conn.execute(
                """
                SELECT bu.role, bu.status, u.id, u.full_name, u.email, u.dni, u.active
                FROM business_users bu
                JOIN users u ON u.id = bu.user_id
                WHERE bu.business_id = %s
                ORDER BY
                    CASE bu.role
                        WHEN 'owner' THEN 0
                        WHEN 'admin' THEN 1
                        WHEN 'manager' THEN 2
                        ELSE 3
                    END,
                    u.full_name
                LIMIT 80
                """,
                (business_id,),
            ).fetchall()

            audit_logs = conn.execute(
                """
                SELECT al.*, u.full_name AS actor_name
                FROM audit_logs al
                LEFT JOIN users u ON u.id = al.actor_user_id
                WHERE al.business_id = %s
                ORDER BY al.created_at DESC
                LIMIT 15
                """,
                (business_id,),
            ).fetchall()

        return {
            "business": dict(biz),
            "employee_count": emp_count,
            "admin_count": admin_count,
            "session_count": session_count,
            "recent_sessions": [dict(r) for r in recent_sessions],
            "members": [dict(r) for r in members],
            "audit_logs": [dict(r) for r in audit_logs],
        }

    def suspend_business(self, business_id: str, reason: str, actor_user_id: int) -> None:
        if not reason.strip():
            raise ValueError("Indica un motivo interno para suspender el negocio.")
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE businesses
                SET suspended_at = CURRENT_TIMESTAMP,
                    suspended_reason = %s,
                    is_active = FALSE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (reason, business_id),
            )

    def update_business(
        self,
        *,
        business_id: str,
        business_name: str,
        primary_email: str | None,
        phone: str | None,
        business_type: str,
        timezone: str,
        country: str | None,
    ) -> dict:
        clean_name = " ".join((business_name or "").split())
        if len(clean_name) < 2:
            raise ValueError("El nombre del negocio debe tener al menos 2 caracteres.")
        with get_connection() as conn:
            before = conn.execute("SELECT * FROM businesses WHERE id = %s", (business_id,)).fetchone()
            if not before:
                raise ValueError("Negocio no encontrado.")
            conn.execute(
                """
                UPDATE businesses
                SET name = %s,
                    business_name = %s,
                    primary_email = NULLIF(%s, ''),
                    phone = NULLIF(%s, ''),
                    business_type = %s,
                    timezone = %s,
                    country = NULLIF(%s, ''),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    clean_name,
                    clean_name,
                    (primary_email or "").strip(),
                    (phone or "").strip(),
                    (business_type or "otro").strip() or "otro",
                    (timezone or "Europe/Madrid").strip() or "Europe/Madrid",
                    (country or "").strip(),
                    business_id,
                ),
            )
            after = conn.execute("SELECT * FROM businesses WHERE id = %s", (business_id,)).fetchone()
        return {"old": dict(before), "new": dict(after)}

    def unsuspend_business(self, business_id: str, actor_user_id: int) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE businesses
                SET suspended_at = NULL,
                    suspended_reason = NULL,
                    is_active = TRUE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (business_id,),
            )

    def archive_business(self, business_id: str, actor_user_id: int) -> None:
        """Soft-delete: sets archived_at, marks inactive. Preserves all data."""
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE businesses
                SET archived_at = CURRENT_TIMESTAMP,
                    is_active = FALSE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (business_id,),
            )

    def change_plan(self, business_id: str, plan_code: str, actor_user_id: int) -> None:
        plan = PlanRepository().get_by_code(plan_code)
        if not plan:
            raise ValueError(f"Plan '{plan_code}' no encontrado.")
        SubscriptionRepository().update_plan(
            business_id=business_id,
            plan_id=plan.id,
            status="active",
        )
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE subscriptions
                SET price = %s,
                    currency = 'EUR',
                    payment_status = CASE WHEN %s = 0 THEN 'none' ELSE 'pending' END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE business_id = %s
                """,
                (plan.price_monthly, plan.price_monthly, business_id),
            )

    # ── Subscriptions ───────────────────────────────────────────────────────

    def list_subscriptions(
        self,
        *,
        status_filter: str | None = None,
        plan_filter: str | None = None,
        page: int = 1,
        per_page: int = 30,
    ) -> tuple[list[SubscriptionRow], int]:
        conditions = ["1=1"]
        params: list = []

        if status_filter:
            if status_filter == "cancelled":
                conditions.append("s.status IN ('cancelled', 'canceled')")
            elif status_filter == "trial":
                conditions.append("s.status IN ('trial', 'trialing')")
            else:
                conditions.append("s.status = %s")
                params.append(status_filter)
        if plan_filter:
            conditions.append("p.code = %s")
            params.append(plan_filter)

        where = "WHERE " + " AND ".join(conditions)
        offset = (page - 1) * per_page

        with get_connection() as conn:
            count_row = conn.execute(
                f"""
                SELECT COUNT(*) AS n FROM subscriptions s
                JOIN plans p ON p.id = s.plan_id
                JOIN businesses b ON b.id = s.business_id
                {where}
                """,
                params,
            ).fetchone()
            total = count_row["n"] if count_row else 0

            rows = conn.execute(
                f"""
                SELECT
                    s.id, s.business_id, b.business_name,
                    s.plan_id, p.name AS plan_name, p.code AS plan_code,
                    s.status,
                    COALESCE(s.billing_cycle, 'monthly') AS billing_cycle,
                    s.current_period_start, s.current_period_end, s.renewal_date,
                    s.trial_ends_at, s.cancel_at, s.cancelled_at, s.paused_at,
                    COALESCE(s.payment_status, 'none') AS payment_status,
                    s.notes, p.price_monthly, s.created_at
                FROM subscriptions s
                JOIN plans p ON p.id = s.plan_id
                JOIN businesses b ON b.id = s.business_id
                {where}
                ORDER BY s.created_at DESC
                LIMIT %s OFFSET %s
                """,
                params + [per_page, offset],
            ).fetchall()

        result = [
            SubscriptionRow(
                id=r["id"],
                business_id=str(r["business_id"]),
                business_name=r["business_name"],
                plan_id=r["plan_id"],
                plan_name=r["plan_name"],
                plan_code=r["plan_code"],
                status=r["status"],
                billing_cycle=r["billing_cycle"],
                current_period_start=str(r["current_period_start"]) if r["current_period_start"] else None,
                current_period_end=str(r["current_period_end"]) if r["current_period_end"] else None,
                renewal_date=str(r["renewal_date"]) if r["renewal_date"] else None,
                trial_ends_at=str(r["trial_ends_at"]) if r["trial_ends_at"] else None,
                cancel_at=str(r["cancel_at"]) if r["cancel_at"] else None,
                cancelled_at=str(r["cancelled_at"]) if r["cancelled_at"] else None,
                paused_at=str(r["paused_at"]) if r["paused_at"] else None,
                payment_status=r["payment_status"],
                notes=r.get("notes"),
                price_monthly=Decimal(str(r["price_monthly"])),
                created_at=str(r["created_at"]) if r["created_at"] else None,
            )
            for r in rows
        ]
        return result, total

    def change_subscription_status(
        self, subscription_id: int, new_status: str, notes: str | None = None
    ) -> None:
        if new_status == "trialing":
            new_status = "trial"
        if new_status == "canceled":
            new_status = "cancelled"
        valid = {"trial", "active", "past_due", "cancelled", "incomplete", "paused", "suspended", "expired"}
        if new_status not in valid:
            raise ValueError(f"Estado '{new_status}' no válido.")
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE subscriptions
                SET status = %s,
                    notes = COALESCE(NULLIF(%s, ''), notes),
                    cancelled_at = CASE WHEN %s = 'cancelled' THEN CURRENT_TIMESTAMP ELSE cancelled_at END,
                    paused_at = CASE WHEN %s = 'paused' THEN CURRENT_TIMESTAMP ELSE paused_at END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (new_status, notes or "", new_status, new_status, subscription_id),
            )

    # ── Internal users ──────────────────────────────────────────────────────

    def extend_trial(self, *, subscription_id: int, trial_ends_at: str, notes: str | None = None) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE subscriptions
                SET status = 'trial',
                    trial_ends_at = %s,
                    notes = COALESCE(NULLIF(%s, ''), notes),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (trial_ends_at, notes or "", subscription_id),
            )

    def list_plans(self) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM plans ORDER BY price_monthly, id").fetchall()
        return [dict(r) for r in rows]

    def list_payment_records(self, *, search: str | None = None) -> list[dict]:
        params: list = []
        where = ""
        if search:
            like = f"%{search.strip()}%"
            where = "WHERE b.business_name ILIKE %s OR pr.business_id ILIKE %s"
            params.extend([like, like])
        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT pr.*, b.business_name, p.name AS plan_name
                FROM payment_records pr
                JOIN businesses b ON b.id = pr.business_id
                LEFT JOIN subscriptions s ON s.id = pr.subscription_id
                LEFT JOIN plans p ON p.id = s.plan_id
                {where}
                ORDER BY pr.created_at DESC
                LIMIT 200
                """,
                params,
            ).fetchall()
        return [dict(r) for r in rows]

    def list_users(
        self,
        *,
        search: str | None = None,
        role_filter: str | None = None,
        platform_filter: str | None = None,
        status_filter: str | None = None,
        page: int = 1,
        per_page: int = 40,
    ) -> tuple[list[dict], int]:
        conditions = ["1=1"]
        params: list = []

        if search:
            like = f"%{search.strip()}%"
            conditions.append(
                """
                (
                    u.full_name ILIKE %s OR u.email ILIKE %s OR u.dni ILIKE %s
                    OR b.business_name ILIKE %s
                )
                """
            )
            params.extend([like, like, like, like])
        if role_filter in {"admin", "employee"}:
            conditions.append("u.role = %s")
            params.append(role_filter)
        if platform_filter == "internal":
            conditions.append("u.platform_role IS NOT NULL")
        elif platform_filter == "tenant":
            conditions.append("u.platform_role IS NULL")
        if status_filter == "active":
            conditions.append("u.active IS TRUE")
        elif status_filter == "inactive":
            conditions.append("u.active IS FALSE")

        where = "WHERE " + " AND ".join(conditions)
        offset = (page - 1) * per_page

        with get_connection() as conn:
            total = conn.execute(
                f"""
                SELECT COUNT(DISTINCT u.id) AS n
                FROM users u
                LEFT JOIN business_users bu ON bu.user_id = u.id
                LEFT JOIN businesses b ON b.id = bu.business_id
                {where}
                """,
                params,
            ).fetchone()["n"]
            rows = conn.execute(
                f"""
                SELECT
                    u.id, u.full_name, u.email, u.dni, u.role, u.platform_role,
                    u.active, u.force_password_change, u.last_login_at, u.created_at,
                    COUNT(DISTINCT bu.business_id) AS business_count,
                    STRING_AGG(
                        DISTINCT b.business_name || ' (' || bu.role || ')',
                        ', '
                    ) FILTER (WHERE b.id IS NOT NULL) AS memberships
                FROM users u
                LEFT JOIN business_users bu ON bu.user_id = u.id
                LEFT JOIN businesses b ON b.id = bu.business_id
                {where}
                GROUP BY u.id
                ORDER BY u.active DESC, u.created_at DESC
                LIMIT %s OFFSET %s
                """,
                params + [per_page, offset],
            ).fetchall()
        return [dict(r) for r in rows], int(total)

    def set_user_active(self, *, user_id: int, active: bool) -> None:
        with get_connection() as conn:
            if not active:
                self._ensure_not_last_superadmin(conn, user_id)
            conn.execute(
                """
                UPDATE users
                SET active = %s,
                    is_active = %s,
                    deactivated_at = CASE WHEN %s IS FALSE THEN CURRENT_TIMESTAMP ELSE NULL END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (active, active, active, user_id),
            )

    def set_business_user_role(self, *, business_id: str, user_id: int, role: str) -> None:
        clean_role = self._normalize_business_role(role)
        with get_connection() as conn:
            exists = conn.execute(
                """
                SELECT role
                FROM business_users
                WHERE business_id = %s AND user_id = %s
                """,
                (business_id, user_id),
            ).fetchone()
            if not exists:
                raise ValueError("El usuario no pertenece a este negocio.")
            if exists["role"] == BusinessRole.OWNER.value and clean_role != BusinessRole.OWNER.value:
                owner_count = conn.execute(
                    """
                    SELECT COUNT(*) AS n
                    FROM business_users
                    WHERE business_id = %s AND role = 'owner' AND status = 'active'
                    """,
                    (business_id,),
                ).fetchone()["n"]
                if owner_count <= 1:
                    raise ValueError("No puedes quitar el ultimo owner del negocio.")

            conn.execute(
                """
                UPDATE business_users
                SET role = %s,
                    status = 'active',
                    updated_at = CURRENT_TIMESTAMP
                WHERE business_id = %s AND user_id = %s
                """,
                (clean_role, business_id, user_id),
            )
            legacy_role = clean_role if clean_role in {"owner", "admin", "employee"} else "admin"
            conn.execute(
                """
                UPDATE business_members
                SET member_role = %s
                WHERE business_id = %s AND user_id = %s
                """,
                (legacy_role, business_id, user_id),
            )
            self._sync_user_global_role_from_memberships(conn, user_id)

    def list_internal_users(self) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, full_name, email, dni, role, platform_role,
                       active, force_password_change, last_login_at, created_at, updated_at
                FROM users
                WHERE platform_role IN ('superadmin', 'internal_admin')
                ORDER BY platform_role, full_name
                """
            ).fetchall()
        return [dict(r) for r in rows]

    def list_all_admin_users(self, *, search: str | None = None) -> list[dict]:
        conditions = ["role = 'admin'"]
        params: list = []
        if search:
            conditions.append(
                "(LOWER(full_name) LIKE LOWER(%s) OR LOWER(email) LIKE LOWER(%s) OR LOWER(dni) LIKE LOWER(%s))"
            )
            like = f"%{search}%"
            params.extend([like, like, like])
        where = "WHERE " + " AND ".join(conditions)
        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT id, full_name, email, dni, role, platform_role,
                       active, created_at
                FROM users {where}
                ORDER BY full_name
                LIMIT 200
                """,
                params,
            ).fetchall()
        return [dict(r) for r in rows]

    def set_platform_role(
        self, user_id: int, platform_role: str | None, actor_user_id: int
    ) -> None:
        clean = self._normalize_platform_role(platform_role) if platform_role else None
        with get_connection() as conn:
            current = conn.execute(
                "SELECT platform_role FROM users WHERE id = %s",
                (user_id,),
            ).fetchone()
            if not current:
                raise ValueError("Usuario no encontrado.")
            if current["platform_role"] == PlatformRole.SUPERADMIN.value and clean != PlatformRole.SUPERADMIN.value:
                self._ensure_not_last_superadmin(conn, user_id)
            conn.execute(
                "UPDATE users SET platform_role = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (clean, user_id),
            )

    def create_internal_user(
        self,
        *,
        full_name: str,
        email: str,
        password: str,
        platform_role: str,
    ) -> dict:
        clean_role = self._normalize_platform_role(platform_role)
        clean_name = " ".join((full_name or "").split())
        clean_email = (email or "").strip().lower()
        if len(clean_name) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres.")
        if "@" not in clean_email:
            raise ValueError("Introduce un email valido.")
        if len(password or "") < 12:
            raise ValueError("La contrasena debe tener al menos 12 caracteres.")
        first, _, last = clean_name.partition(" ")
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM users WHERE LOWER(email) = LOWER(%s) OR LOWER(dni) = LOWER(%s)",
                (clean_email, clean_email),
            ).fetchone()
            if existing:
                raise ValueError("Ya existe un usuario con ese email.")
            row = conn.execute(
                """
                INSERT INTO users (
                    email, full_name, first_name, last_name, dni, password_hash,
                    role, platform_role, active, is_active, force_password_change, auth_provider
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'admin', %s, TRUE, TRUE, TRUE, 'password')
                RETURNING id, full_name, email, dni, role, platform_role, active, created_at
                """,
                (clean_email, clean_name, first, last, clean_email, hash_password(password), clean_role),
            ).fetchone()
        return dict(row)

    def set_internal_user_active(self, *, user_id: int, active: bool) -> None:
        with get_connection() as conn:
            if not active:
                self._ensure_not_last_superadmin(conn, user_id)
            conn.execute(
                """
                UPDATE users
                SET active = %s,
                    is_active = %s,
                    deactivated_at = CASE WHEN %s IS FALSE THEN CURRENT_TIMESTAMP ELSE NULL END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND platform_role IN ('superadmin', 'internal_admin')
                """,
                (active, active, active, user_id),
            )

    def reset_internal_password(self, *, user_id: int, new_password: str, force_change: bool = True) -> None:
        if len(new_password or "") < 8:
            raise ValueError("La nueva contrasena debe tener al menos 8 caracteres.")
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE users
                SET password_hash = %s,
                    force_password_change = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND platform_role IN ('superadmin', 'internal_admin')
                """,
                (hash_password(new_password), force_change, user_id),
            )

    def _normalize_platform_role(self, value: str | PlatformRole | None) -> str:
        clean = str(value or "").strip().lower()
        if clean not in PLATFORM_ADMIN_ROLES:
            raise ValueError("Rol interno no valido.")
        return PlatformRole(clean).value

    def _normalize_business_role(self, value: str | BusinessRole | None) -> str:
        clean = str(value or "").strip().lower()
        allowed = {
            BusinessRole.OWNER.value,
            BusinessRole.COMPANY_ADMIN.value,
            BusinessRole.MANAGER.value,
            BusinessRole.EMPLOYEE.value,
        }
        if clean not in allowed:
            raise ValueError("Rol de negocio no valido.")
        return clean

    def _ensure_not_last_superadmin(self, conn, user_id: int) -> None:
        row = conn.execute(
            """
            SELECT platform_role, active
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        ).fetchone()
        if not row or row["platform_role"] != PlatformRole.SUPERADMIN.value or not row["active"]:
            return
        count = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM users
            WHERE platform_role = 'superadmin' AND active IS TRUE
            """
        ).fetchone()["n"]
        if count <= 1:
            raise ValueError("No puedes desactivar o degradar el ultimo superadmin activo.")

    def _sync_user_global_role_from_memberships(self, conn, user_id: int) -> None:
        row = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM business_users
            WHERE user_id = %s
              AND status = 'active'
              AND role IN ('owner', 'admin', 'manager')
            """,
            (user_id,),
        ).fetchone()
        global_role = "admin" if row and row["n"] else "employee"
        conn.execute(
            """
            UPDATE users
            SET role = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (global_role, user_id),
        )
