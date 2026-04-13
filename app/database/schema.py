from datetime import datetime

from app.config import DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME
from app.database.connection import get_connection
from app.utils.security import hash_password, verify_password


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    dni TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'employee'
        CHECK (role IN ('admin', 'employee')),
    active INTEGER NOT NULL DEFAULT 1,
    last_business_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS businesses (
    id TEXT PRIMARY KEY,
    owner_user_id INTEGER NOT NULL,
    business_name TEXT NOT NULL,
    business_type TEXT NOT NULL,
    login_code TEXT NOT NULL COLLATE NOCASE,
    slug TEXT NOT NULL,
    business_key TEXT NOT NULL,
    settings_json TEXT NOT NULL DEFAULT '{}',
    last_accessed_at TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_user_id) REFERENCES users(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_businesses_login_code_active
ON businesses(login_code)
WHERE is_active = 1;

CREATE UNIQUE INDEX IF NOT EXISTS idx_businesses_slug
ON businesses(slug);

CREATE UNIQUE INDEX IF NOT EXISTS idx_businesses_business_key
ON businesses(business_key);

CREATE INDEX IF NOT EXISTS idx_businesses_owner
ON businesses(owner_user_id);

CREATE TABLE IF NOT EXISTS business_members (
    business_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    member_role TEXT NOT NULL DEFAULT 'employee'
        CHECK (member_role IN ('owner', 'admin', 'employee')),
    is_default INTEGER NOT NULL DEFAULT 0,
    joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TEXT,
    PRIMARY KEY (business_id, user_id),
    FOREIGN KEY (business_id) REFERENCES businesses(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_business_members_user
ON business_members(user_id, is_default, last_accessed_at);

CREATE INDEX IF NOT EXISTS idx_business_members_business
ON business_members(business_id, member_role);

CREATE TABLE IF NOT EXISTS attendance_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT,
    user_id INTEGER NOT NULL,
    clock_in_time TEXT NOT NULL,
    clock_out_time TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    total_seconds INTEGER,
    notes TEXT,
    exit_note TEXT,
    incident_type TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_by_admin INTEGER NOT NULL DEFAULT 0,
    manual_close_reason TEXT,
    closed_by_user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_sessions_one_active
ON attendance_sessions(user_id)
WHERE is_active = 1;

CREATE INDEX IF NOT EXISTS idx_attendance_sessions_user_clock_in
ON attendance_sessions(user_id, clock_in_time);

CREATE INDEX IF NOT EXISTS idx_attendance_sessions_clock_in
ON attendance_sessions(clock_in_time);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'employee'
        CHECK (role IN ('admin', 'employee')),
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS time_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT,
    employee_id INTEGER NOT NULL,
    entry_type TEXT NOT NULL
        CHECK (entry_type IN ('entrada', 'salida')),
    timestamp TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE INDEX IF NOT EXISTS idx_time_entries_employee_timestamp
ON time_entries(employee_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_time_entries_timestamp
ON time_entries(timestamp);

"""


def initialize_database() -> None:
    with get_connection() as connection:
        _execute_schema(connection)
        _migrate_business_foundation(connection)
        _migrate_legacy_employee_columns(connection)
        _migrate_users_from_legacy_employees(connection)
        _ensure_default_admin(connection)
        _sync_users_to_legacy_employees(connection)
        _migrate_attendance_sessions_from_time_entries(connection)
        _migrate_attendance_sessions_add_context_columns(connection)
        _migrate_attendance_sessions_add_admin_close_columns(connection)


def _execute_schema(connection) -> None:
    """
    Execute schema statements one by one.

    On OneDrive-backed folders, sqlite3.executescript can raise a generic
    disk I/O error even when the individual statements are valid and writable.
    Splitting keeps initialisation reliable for the desktop app and tests.
    """
    for statement in SCHEMA_SQL.split(";"):
        clean_statement = statement.strip()
        if clean_statement:
            connection.execute(clean_statement)


def _table_columns(connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def _migrate_business_foundation(connection) -> None:
    """Add SaaS business context columns to older local databases."""
    user_columns = _table_columns(connection, "users")
    if "last_business_id" not in user_columns:
        connection.execute("ALTER TABLE users ADD COLUMN last_business_id TEXT")

    session_columns = _table_columns(connection, "attendance_sessions")
    if "business_id" not in session_columns:
        connection.execute("ALTER TABLE attendance_sessions ADD COLUMN business_id TEXT")
    connection.execute("DROP INDEX IF EXISTS idx_attendance_sessions_one_active")
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_sessions_one_active
        ON attendance_sessions(COALESCE(business_id, ''), user_id)
        WHERE is_active = 1
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_attendance_sessions_business_clock_in
        ON attendance_sessions(business_id, clock_in_time)
        """
    )

    time_entry_columns = _table_columns(connection, "time_entries")
    if "business_id" not in time_entry_columns:
        connection.execute("ALTER TABLE time_entries ADD COLUMN business_id TEXT")
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_time_entries_business_timestamp
        ON time_entries(business_id, timestamp)
        """
    )


def _migrate_legacy_employee_columns(connection) -> None:
    """
    Keep older databases working after splitting employees.name into
    first_name and last_name.
    """
    columns = _table_columns(connection, "employees")
    had_name_column = "name" in columns

    if "first_name" not in columns:
        connection.execute("ALTER TABLE employees ADD COLUMN first_name TEXT")
    if "last_name" not in columns:
        connection.execute("ALTER TABLE employees ADD COLUMN last_name TEXT")
    if "name" not in columns:
        connection.execute("ALTER TABLE employees ADD COLUMN name TEXT")
    if "created_at" not in columns:
        connection.execute("ALTER TABLE employees ADD COLUMN created_at TEXT")

    if had_name_column:
        connection.execute(
            """
            UPDATE employees
            SET first_name = CASE
                    WHEN first_name IS NOT NULL AND TRIM(first_name) <> ''
                        THEN TRIM(first_name)
                    WHEN INSTR(TRIM(name), ' ') > 0
                        THEN TRIM(SUBSTR(TRIM(name), 1, INSTR(TRIM(name), ' ') - 1))
                    ELSE COALESCE(NULLIF(TRIM(name), ''), username)
                END,
                last_name = CASE
                    WHEN last_name IS NOT NULL AND TRIM(last_name) <> ''
                        THEN TRIM(last_name)
                    WHEN INSTR(TRIM(name), ' ') > 0
                        THEN TRIM(SUBSTR(TRIM(name), INSTR(TRIM(name), ' ') + 1))
                    ELSE ''
                END
            WHERE first_name IS NULL
               OR TRIM(first_name) = ''
               OR last_name IS NULL
            """
        )
    else:
        connection.execute(
            """
            UPDATE employees
            SET first_name = COALESCE(NULLIF(TRIM(first_name), ''), username),
                last_name = COALESCE(last_name, '')
            WHERE first_name IS NULL
               OR TRIM(first_name) = ''
               OR last_name IS NULL
            """
        )

    connection.execute(
        """
        UPDATE employees
        SET name = TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, ''))
        WHERE name IS NULL OR TRIM(name) = ''
        """
    )

    connection.execute(
        """
        UPDATE employees
        SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)
        WHERE created_at IS NULL OR TRIM(created_at) = ''
        """
    )


def _migrate_users_from_legacy_employees(connection) -> None:
    rows = connection.execute(
        """
        SELECT id, first_name, last_name, username, password_hash, role, active, created_at
        FROM employees
        ORDER BY id
        """
    ).fetchall()

    for row in rows:
        first_name = (row["first_name"] or row["username"] or "").strip()
        last_name = (row["last_name"] or "").strip()
        dni = (row["username"] or "").strip()
        if not dni:
            continue

        connection.execute(
            """
            INSERT OR IGNORE INTO users
                (id, first_name, last_name, dni, password_hash, role, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
            """,
            (
                row["id"],
                first_name,
                last_name,
                dni,
                row["password_hash"],
                row["role"],
                row["active"],
                row["created_at"],
            ),
        )


def _ensure_default_admin(connection) -> None:
    admin = connection.execute(
        """
        SELECT id, password_hash
        FROM users
        WHERE LOWER(dni) = LOWER(?) AND role = 'admin'
        LIMIT 1
        """,
        (DEFAULT_ADMIN_USERNAME,),
    ).fetchone()

    if admin:
        stored_hash = admin["password_hash"]
        if verify_password("admin123", stored_hash) and not verify_password(
            DEFAULT_ADMIN_PASSWORD,
            stored_hash,
        ):
            connection.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(DEFAULT_ADMIN_PASSWORD), admin["id"]),
            )
        return

    connection.execute(
        """
        INSERT INTO users
            (first_name, last_name, dni, password_hash, role, active)
        VALUES (?, ?, ?, ?, 'admin', 1)
        """,
        (
            "Admin",
            "Sistema",
            DEFAULT_ADMIN_USERNAME,
            hash_password(DEFAULT_ADMIN_PASSWORD),
        ),
    )


def _sync_users_to_legacy_employees(connection) -> None:
    rows = connection.execute(
        """
        SELECT id, first_name, last_name, dni, password_hash, role, active, created_at
        FROM users
        ORDER BY id
        """
    ).fetchall()

    for row in rows:
        name = f"{row['first_name']} {row['last_name']}".strip()
        connection.execute(
            """
            INSERT OR IGNORE INTO employees
                (id, first_name, last_name, name, username, password_hash, role, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
            """,
            (
                row["id"],
                row["first_name"],
                row["last_name"],
                name,
                row["dni"],
                row["password_hash"],
                row["role"],
                row["active"],
                row["created_at"],
            ),
        )
        connection.execute(
            """
            UPDATE employees
            SET first_name = ?,
                last_name = ?,
                name = ?,
                username = ?,
                password_hash = ?,
                role = ?,
                active = ?,
                created_at = COALESCE(created_at, ?)
            WHERE id = ?
            """,
            (
                row["first_name"],
                row["last_name"],
                name,
                row["dni"],
                row["password_hash"],
                row["role"],
                row["active"],
                row["created_at"],
                row["id"],
            ),
        )


def _migrate_attendance_sessions_from_time_entries(connection) -> None:
    existing = connection.execute(
        "SELECT COUNT(*) FROM attendance_sessions"
    ).fetchone()[0]
    if existing:
        return

    rows = connection.execute(
        """
        SELECT employee_id, entry_type, timestamp, notes
        FROM time_entries
        ORDER BY employee_id, timestamp, id
        """
    ).fetchall()

    active_by_user: dict[int, int] = {}
    active_started_at: dict[int, str] = {}

    for row in rows:
        user_id = row["employee_id"]
        entry_type = row["entry_type"]
        timestamp = row["timestamp"]

        user_exists = connection.execute(
            "SELECT 1 FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not user_exists:
            continue

        if entry_type == "entrada" and user_id not in active_by_user:
            cursor = connection.execute(
                """
                INSERT INTO attendance_sessions
                    (user_id, clock_in_time, is_active, notes)
                VALUES (?, ?, 1, ?)
                """,
                (user_id, timestamp, row["notes"]),
            )
            active_by_user[user_id] = int(cursor.lastrowid)
            active_started_at[user_id] = timestamp
            continue

        if entry_type == "salida" and user_id in active_by_user:
            started_at = active_started_at[user_id]
            total_seconds = _seconds_between(started_at, timestamp)
            connection.execute(
                """
                UPDATE attendance_sessions
                SET clock_out_time = ?,
                    is_active = 0,
                    total_seconds = ?,
                    notes = COALESCE(notes, ?)
                WHERE id = ?
                """,
                (timestamp, total_seconds, row["notes"], active_by_user[user_id]),
            )
            del active_by_user[user_id]
            del active_started_at[user_id]


def _migrate_attendance_sessions_add_admin_close_columns(connection) -> None:
    """Add admin-close audit columns to attendance_sessions if they don't exist yet."""
    columns = _table_columns(connection, "attendance_sessions")
    if "closed_by_admin" not in columns:
        connection.execute(
            "ALTER TABLE attendance_sessions ADD COLUMN closed_by_admin INTEGER NOT NULL DEFAULT 0"
        )
    if "manual_close_reason" not in columns:
        connection.execute(
            "ALTER TABLE attendance_sessions ADD COLUMN manual_close_reason TEXT"
        )
    if "closed_by_user_id" not in columns:
        connection.execute(
            "ALTER TABLE attendance_sessions ADD COLUMN closed_by_user_id INTEGER"
        )


def _migrate_attendance_sessions_add_context_columns(connection) -> None:
    """Add exit context columns to attendance_sessions if they don't exist yet."""
    columns = _table_columns(connection, "attendance_sessions")
    if "exit_note" not in columns:
        connection.execute("ALTER TABLE attendance_sessions ADD COLUMN exit_note TEXT")
    if "incident_type" not in columns:
        connection.execute("ALTER TABLE attendance_sessions ADD COLUMN incident_type TEXT")


def _seconds_between(start: str, end: str) -> int:
    try:
        started = datetime.fromisoformat(start)
        ended = datetime.fromisoformat(end)
    except (TypeError, ValueError):
        return 0
    return max(int((ended - started).total_seconds()), 0)
