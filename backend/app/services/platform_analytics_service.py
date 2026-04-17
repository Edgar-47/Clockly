"""
app/services/platform_analytics_service.py

Read-only analytics queries for the superadmin dashboard.
All queries run directly against the DB for performance (no service layer overhead).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.database.connection import get_connection


@dataclass
class GlobalStats:
    # Businesses
    total_businesses: int = 0
    active_businesses: int = 0
    inactive_businesses: int = 0
    suspended_businesses: int = 0
    archived_businesses: int = 0
    businesses_this_month: int = 0

    # Users
    total_users: int = 0
    total_admins: int = 0
    total_employees: int = 0
    users_this_month: int = 0

    # Subscriptions
    subscriptions_active: int = 0
    subscriptions_trialing: int = 0
    subscriptions_canceled: int = 0
    subscriptions_past_due: int = 0
    subscriptions_paused: int = 0

    # Revenue
    mrr: Decimal = field(default_factory=Decimal)
    arr: Decimal = field(default_factory=Decimal)

    # Plans
    plan_distribution: list[dict] = field(default_factory=list)

    # Activity
    total_sessions: int = 0
    active_sessions: int = 0
    total_hours_tracked: float = 0.0

    # Top businesses
    top_businesses_by_employees: list[dict] = field(default_factory=list)
    top_businesses_by_sessions: list[dict] = field(default_factory=list)


class PlatformAnalyticsService:

    def get_global_stats(self) -> GlobalStats:
        stats = GlobalStats()
        with get_connection() as conn:
            self._load_business_stats(conn, stats)
            self._load_user_stats(conn, stats)
            self._load_subscription_stats(conn, stats)
            self._load_revenue_stats(conn, stats)
            self._load_plan_distribution(conn, stats)
            self._load_activity_stats(conn, stats)
            self._load_top_businesses(conn, stats)
        return stats

    def get_monthly_growth(self, *, months: int = 12) -> list[dict]:
        """Returns list of {month, businesses_created, users_created} for the last N months."""
        with get_connection() as conn:
            rows = conn.execute(
                """
                WITH months AS (
                    SELECT generate_series(
                        date_trunc('month', NOW()) - (%s * INTERVAL '1 month'),
                        date_trunc('month', NOW()),
                        INTERVAL '1 month'
                    ) AS month
                ),
                biz AS (
                    SELECT date_trunc('month', created_at) AS month, COUNT(*) AS cnt
                    FROM businesses
                    WHERE created_at >= NOW() - (%s * INTERVAL '1 month')
                    GROUP BY 1
                ),
                usr AS (
                    SELECT date_trunc('month', created_at) AS month, COUNT(*) AS cnt
                    FROM users
                    WHERE created_at >= NOW() - (%s * INTERVAL '1 month')
                    AND role = 'admin'
                    GROUP BY 1
                )
                SELECT
                    to_char(m.month, 'Mon YY') AS label,
                    to_char(m.month, 'YYYY-MM') AS month_key,
                    COALESCE(b.cnt, 0) AS businesses_created,
                    COALESCE(u.cnt, 0) AS users_created
                FROM months m
                LEFT JOIN biz b ON b.month = m.month
                LEFT JOIN usr u ON u.month = m.month
                ORDER BY m.month
                """,
                (months, months, months),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_mrr_trend(self, *, months: int = 12) -> list[dict]:
        """Estimated MRR trend — joins subscriptions on active plans per month."""
        with get_connection() as conn:
            rows = conn.execute(
                """
                WITH months AS (
                    SELECT generate_series(
                        date_trunc('month', NOW()) - (%s * INTERVAL '1 month'),
                        date_trunc('month', NOW()),
                        INTERVAL '1 month'
                    ) AS month
                ),
                snap AS (
                    SELECT
                        date_trunc('month', s.created_at) AS month,
                        SUM(p.price_monthly) AS mrr
                    FROM subscriptions s
                    JOIN plans p ON p.id = s.plan_id
                    WHERE s.status IN ('active', 'trialing')
                    AND p.price_monthly > 0
                    AND s.created_at >= NOW() - (%s * INTERVAL '1 month')
                    GROUP BY 1
                )
                SELECT
                    to_char(m.month, 'Mon YY') AS label,
                    COALESCE(snap.mrr, 0) AS mrr
                FROM months m
                LEFT JOIN snap ON snap.month = m.month
                ORDER BY m.month
                """,
                (months, months),
            ).fetchall()
        return [{"label": r["label"], "mrr": float(r["mrr"])} for r in rows]

    def get_subscription_evolution(self) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM subscriptions
                GROUP BY status
                ORDER BY status
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_usage_metrics(self) -> dict:
        with get_connection() as conn:
            overview = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_sessions,
                    COUNT(*) FILTER (WHERE is_active IS TRUE) AS open_sessions,
                    COUNT(*) FILTER (WHERE is_active IS FALSE) AS closed_sessions,
                    COALESCE(SUM(total_seconds) / 3600.0, 0) AS total_hours,
                    COALESCE(AVG(total_seconds) / 3600.0, 0) AS avg_session_hours
                FROM attendance_sessions
                """
            ).fetchone()
            business_averages = conn.execute(
                """
                SELECT
                    COALESCE(AVG(employee_count), 0) AS avg_employees_per_business,
                    COALESCE(AVG(session_count), 0) AS avg_sessions_per_business
                FROM (
                    SELECT
                        b.id,
                        COUNT(DISTINCT bu.user_id) FILTER (WHERE bu.role = 'employee') AS employee_count,
                        COUNT(DISTINCT a.id) AS session_count
                    FROM businesses b
                    LEFT JOIN business_users bu ON bu.business_id = b.id AND bu.status = 'active'
                    LEFT JOIN attendance_sessions a ON a.business_id = b.id
                    WHERE b.archived_at IS NULL
                    GROUP BY b.id
                ) x
                """
            ).fetchone()
            top_value = conn.execute(
                """
                SELECT b.business_name, b.id, p.price_monthly
                FROM subscriptions s
                JOIN businesses b ON b.id = s.business_id
                JOIN plans p ON p.id = s.plan_id
                WHERE s.status IN ('active', 'trial') AND b.archived_at IS NULL
                ORDER BY p.price_monthly DESC, b.business_name
                LIMIT 10
                """
            ).fetchall()
            days = conn.execute(
                """
                SELECT to_char(clock_in_time::date, 'YYYY-MM-DD') AS day, COUNT(*) AS sessions
                FROM attendance_sessions
                GROUP BY clock_in_time::date
                ORDER BY sessions DESC, day DESC
                LIMIT 10
                """
            ).fetchall()
        return {
            "overview": dict(overview or {}),
            "business_averages": dict(business_averages or {}),
            "top_value": [dict(row) for row in top_value],
            "days": [dict(row) for row in days],
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_business_stats(self, conn, stats: GlobalStats) -> None:
        row = conn.execute(
            """
            SELECT
                COUNT(*)                                         AS total,
                COUNT(*) FILTER (WHERE is_active AND suspended_at IS NULL
                                        AND archived_at IS NULL)  AS active,
                COUNT(*) FILTER (WHERE NOT is_active
                                        AND archived_at IS NULL)  AS inactive,
                COUNT(*) FILTER (WHERE suspended_at IS NOT NULL
                                        AND archived_at IS NULL)  AS suspended,
                COUNT(*) FILTER (WHERE archived_at IS NOT NULL)   AS archived,
                COUNT(*) FILTER (
                    WHERE created_at >= date_trunc('month', NOW())
                )                                                  AS this_month
            FROM businesses
            """
        ).fetchone()
        if row:
            stats.total_businesses = row["total"]
            stats.active_businesses = row["active"]
            stats.inactive_businesses = row["inactive"]
            stats.suspended_businesses = row["suspended"]
            stats.archived_businesses = row["archived"]
            stats.businesses_this_month = row["this_month"]

    def _load_user_stats(self, conn, stats: GlobalStats) -> None:
        row = conn.execute(
            """
            SELECT
                COUNT(*)                                    AS total,
                COUNT(*) FILTER (WHERE role = 'admin')     AS admins,
                COUNT(*) FILTER (WHERE role = 'employee')  AS employees,
                COUNT(*) FILTER (
                    WHERE created_at >= date_trunc('month', NOW())
                )                                           AS this_month
            FROM users
            WHERE active IS TRUE
            """
        ).fetchone()
        if row:
            stats.total_users = row["total"]
            stats.total_admins = row["admins"]
            stats.total_employees = row["employees"]
            stats.users_this_month = row["this_month"]

    def _load_subscription_stats(self, conn, stats: GlobalStats) -> None:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS cnt FROM subscriptions GROUP BY status"
        ).fetchall()
        for row in rows:
            s = row["status"]
            n = row["cnt"]
            if s == "active":
                stats.subscriptions_active = n
            elif s == "trialing":
                stats.subscriptions_trialing = n
            elif s in ("canceled", "cancelled"):
                stats.subscriptions_canceled = n
            elif s == "past_due":
                stats.subscriptions_past_due = n
            elif s == "paused":
                stats.subscriptions_paused = n

    def _load_revenue_stats(self, conn, stats: GlobalStats) -> None:
        row = conn.execute(
            """
            SELECT
                COALESCE(SUM(p.price_monthly), 0) AS mrr,
                COALESCE(SUM(p.price_monthly) * 12, 0) AS arr
            FROM subscriptions s
            JOIN plans p ON p.id = s.plan_id
            WHERE s.status IN ('active', 'trialing')
            AND p.price_monthly > 0
            """
        ).fetchone()
        if row:
            stats.mrr = Decimal(str(row["mrr"]))
            stats.arr = Decimal(str(row["arr"]))

    def _load_plan_distribution(self, conn, stats: GlobalStats) -> None:
        rows = conn.execute(
            """
            SELECT p.name, p.code, COUNT(*) AS cnt
            FROM subscriptions s
            JOIN plans p ON p.id = s.plan_id
            WHERE s.status != 'canceled'
            GROUP BY p.name, p.code
            ORDER BY cnt DESC
            """
        ).fetchall()
        stats.plan_distribution = [
            {"name": r["name"], "code": r["code"], "count": r["cnt"]} for r in rows
        ]

    def _load_activity_stats(self, conn, stats: GlobalStats) -> None:
        row = conn.execute(
            """
            SELECT
                COUNT(*)                              AS total,
                COUNT(*) FILTER (WHERE is_active)     AS active,
                COALESCE(SUM(total_seconds) / 3600.0, 0) AS total_hours
            FROM attendance_sessions
            """
        ).fetchone()
        if row:
            stats.total_sessions = row["total"]
            stats.active_sessions = row["active"]
            stats.total_hours_tracked = round(float(row["total_hours"]), 1)

    def _load_top_businesses(self, conn, stats: GlobalStats) -> None:
        rows = conn.execute(
            """
            SELECT b.business_name, b.id, COUNT(e.id) AS emp_count
            FROM businesses b
            LEFT JOIN employees e ON e.business_id = b.id AND e.is_active IS TRUE
            WHERE b.is_active IS TRUE
            GROUP BY b.id, b.business_name
            ORDER BY emp_count DESC
            LIMIT 5
            """
        ).fetchall()
        stats.top_businesses_by_employees = [
            {"name": r["business_name"], "id": r["id"], "count": r["emp_count"]}
            for r in rows
        ]

        rows = conn.execute(
            """
            SELECT b.business_name, b.id, COUNT(s.id) AS session_count
            FROM businesses b
            LEFT JOIN attendance_sessions s ON s.business_id = b.id
            WHERE b.is_active IS TRUE
            GROUP BY b.id, b.business_name
            ORDER BY session_count DESC
            LIMIT 5
            """
        ).fetchall()
        stats.top_businesses_by_sessions = [
            {"name": r["business_name"], "id": r["id"], "count": r["session_count"]}
            for r in rows
        ]
