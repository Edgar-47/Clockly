"""
app/database/platform_settings_repository.py

Key-value store for global platform configuration.
"""
from __future__ import annotations

from app.database.connection import get_connection
from app.models.platform_settings import (
    PLATFORM_SETTING_DEFAULTS,
    PLATFORM_SETTING_DESCRIPTIONS,
    PlatformSetting,
)


class PlatformSettingsRepository:

    def get_all(self) -> dict[str, PlatformSetting]:
        """Return all settings as a dict keyed by setting key.
        Merges DB values with defaults so all expected keys are present."""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT key, value, description, updated_at FROM platform_settings"
            ).fetchall()

        db_settings = {r["key"]: PlatformSetting.from_row(r) for r in rows}

        # Ensure all default keys are present
        result: dict[str, PlatformSetting] = {}
        for key, default_value in PLATFORM_SETTING_DEFAULTS.items():
            if key in db_settings:
                result[key] = db_settings[key]
            else:
                result[key] = PlatformSetting(
                    key=key,
                    value=default_value,
                    description=PLATFORM_SETTING_DESCRIPTIONS.get(key),
                    updated_at=None,
                )
        return result

    def get(self, key: str, default: str | None = None) -> str | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM platform_settings WHERE key = %s", (key,)
            ).fetchone()
        if row:
            return row["value"]
        return PLATFORM_SETTING_DEFAULTS.get(key, default)

    def set(self, key: str, value: str, description: str | None = None) -> None:
        desc = description or PLATFORM_SETTING_DESCRIPTIONS.get(key)
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO platform_settings (key, value, description, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    description = COALESCE(EXCLUDED.description, platform_settings.description),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (key, value, desc),
            )

    def set_many(self, settings: dict[str, str]) -> None:
        for key, value in settings.items():
            self.set(key, value)
