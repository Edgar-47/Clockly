from __future__ import annotations

from app.core.flow_debug import flow_log, mask_identifier
from app.database.employee_repository import EmployeeRepository
from app.models.employee import Employee
from app.models.plan_constants import PlatformRole
from app.utils.security import verify_password


class SuperadminAuthService:
    """Authentication for the isolated internal owner console."""

    def __init__(self, employee_repository: EmployeeRepository | None = None) -> None:
        self.employee_repository = employee_repository or EmployeeRepository()

    def login(self, identifier: str, password: str) -> Employee:
        clean_identifier = identifier.strip()
        if not clean_identifier or not password:
            raise ValueError("Introduce email/identificador y contrasena.")

        user = self.employee_repository.get_by_identifier(clean_identifier)
        if (
            not user
            or not user.active
            or user.platform_role != PlatformRole.SUPERADMIN.value
            or not verify_password(password, user.password_hash)
        ):
            flow_log(
                "service.superadmin.login.rejected",
                identifier=mask_identifier(clean_identifier),
            )
            raise ValueError("Credenciales internas incorrectas.")

        self.employee_repository.mark_login_success(user.id)
        flow_log("service.superadmin.login.success", user_id=user.id)
        return user

