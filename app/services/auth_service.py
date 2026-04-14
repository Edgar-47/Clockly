from app.core.flow_debug import flow_log, mask_identifier
from app.database.employee_repository import EmployeeRepository
from app.models.employee import Employee
from app.utils.security import verify_password


class AuthService:
    def __init__(self, employee_repository: EmployeeRepository | None = None) -> None:
        self.employee_repository = employee_repository or EmployeeRepository()

    def login(self, identifier: str, password: str) -> Employee:
        clean_identifier = identifier.strip()
        flow_log(
            "service.auth.login.request",
            identifier=mask_identifier(clean_identifier),
            password_present=bool(password),
        )
        if not clean_identifier or not password:
            raise ValueError("Introduce identificador y contrasena.")

        employee = self.employee_repository.get_by_identifier(clean_identifier)
        if not employee or not employee.active:
            flow_log(
                "service.auth.login.rejected",
                identifier=mask_identifier(clean_identifier),
                reason="not_found_or_inactive",
            )
            raise ValueError("Identificador o contrasena incorrectos.")

        if not verify_password(password, employee.password_hash):
            flow_log(
                "service.auth.login.rejected",
                employee_id=employee.id,
                reason="wrong_password",
            )
            raise ValueError("Identificador o contrasena incorrectos.")

        flow_log(
            "service.auth.login.result",
            employee_id=employee.id,
            role=employee.role,
        )
        return employee

    def verify_employee_password(self, employee_id: int, password: str) -> Employee:
        flow_log(
            "service.auth.verify_employee_password.request",
            employee_id=employee_id,
            password_present=bool(password),
        )
        if not password:
            raise ValueError("Introduce la contrasena.")

        employee = self.employee_repository.get_by_id(employee_id)
        if not employee or not employee.active:
            flow_log(
                "service.auth.verify_employee_password.rejected",
                employee_id=employee_id,
                reason="not_found_or_inactive",
            )
            raise ValueError("Empleado no valido o inactivo.")

        if not verify_password(password, employee.password_hash):
            flow_log(
                "service.auth.verify_employee_password.rejected",
                employee_id=employee_id,
                reason="wrong_password",
            )
            raise ValueError("Contrasena incorrecta.")

        flow_log(
            "service.auth.verify_employee_password.result",
            employee_id=employee.id,
            role=employee.role,
        )
        return employee
