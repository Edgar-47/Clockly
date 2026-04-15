"""
app/database/employee_profile_repository.py

CRUD access for employee_profiles.
Uses an UPSERT (INSERT … ON CONFLICT DO UPDATE) so callers never need to know
whether a row already exists.
"""
from __future__ import annotations

from app.database.connection import get_connection
from app.models.employee_profile import EmployeeProfile


class EmployeeProfileRepository:

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_user_id(self, user_id: int) -> EmployeeProfile | None:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT user_id, hire_date, contract_type, department,
                       job_title, phone, personal_email,
                       emergency_contact_name, emergency_contact_phone,
                       social_security_number, notes,
                       created_at, updated_at
                FROM   employee_profiles
                WHERE  user_id = %s
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return EmployeeProfile.from_row(dict(row))

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def upsert(
        self,
        user_id: int,
        *,
        hire_date: str | None = None,
        contract_type: str | None = None,
        department: str | None = None,
        job_title: str | None = None,
        phone: str | None = None,
        personal_email: str | None = None,
        emergency_contact_name: str | None = None,
        emergency_contact_phone: str | None = None,
        social_security_number: str | None = None,
        notes: str | None = None,
    ) -> EmployeeProfile:
        """
        Insert or update the profile row for *user_id*.
        Returns the saved EmployeeProfile.
        """
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO employee_profiles (
                    user_id, hire_date, contract_type, department,
                    job_title, phone, personal_email,
                    emergency_contact_name, emergency_contact_phone,
                    social_security_number, notes,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    hire_date               = EXCLUDED.hire_date,
                    contract_type           = EXCLUDED.contract_type,
                    department              = EXCLUDED.department,
                    job_title               = EXCLUDED.job_title,
                    phone                   = EXCLUDED.phone,
                    personal_email          = EXCLUDED.personal_email,
                    emergency_contact_name  = EXCLUDED.emergency_contact_name,
                    emergency_contact_phone = EXCLUDED.emergency_contact_phone,
                    social_security_number  = EXCLUDED.social_security_number,
                    notes                   = EXCLUDED.notes,
                    updated_at              = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    hire_date or None,
                    contract_type or None,
                    department or None,
                    job_title or None,
                    phone or None,
                    personal_email or None,
                    emergency_contact_name or None,
                    emergency_contact_phone or None,
                    social_security_number or None,
                    notes or None,
                ),
            )
            conn.commit()

        saved = self.get_by_user_id(user_id)
        if saved is None:
            # Should never happen right after upsert, but guard defensively
            return EmployeeProfile.empty(user_id)
        return saved
