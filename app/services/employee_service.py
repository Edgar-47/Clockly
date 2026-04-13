import re
import sqlite3

from app.database.employee_repository import EmployeeRepository
from app.models.employee import Employee
from app.utils.security import hash_password


class EmployeeService:
    VALID_ROLES = {"admin", "employee"}

    def __init__(self, employee_repository: EmployeeRepository | None = None) -> None:
        self.employee_repository = employee_repository or EmployeeRepository()

    def list_employees(self) -> list[Employee]:
        return self.employee_repository.list_all()

    def list_clockable_employees(self) -> list[Employee]:
        return self.employee_repository.list_active_clockable()

    def create_employee(
        self,
        *,
        first_name: str = "",
        last_name: str = "",
        dni: str | None = None,
        password: str,
        role: str = "employee",
        name: str | None = None,
        username: str | None = None,
    ) -> int:
        if name and not first_name and not last_name:
            first_name, last_name = self._split_full_name(name)

        clean_first_name = first_name.strip()
        clean_last_name = last_name.strip()
        clean_role = role.strip().lower()
        clean_dni = self._normalize_dni(dni or username or "")

        if not clean_first_name:
            raise ValueError("El nombre es obligatorio.")
        if not clean_last_name:
            raise ValueError("El apellido es obligatorio.")
        if not clean_dni:
            raise ValueError("El DNI es obligatorio.")
        if len(password) < 6:
            raise ValueError("La contrasena debe tener al menos 6 caracteres.")
        if clean_role not in self.VALID_ROLES:
            raise ValueError("Rol no valido.")

        duplicate = self.employee_repository.get_by_dni(clean_dni)
        if duplicate:
            raise ValueError("Ya existe un empleado con ese DNI.")

        try:
            return self.employee_repository.create(
                first_name=clean_first_name,
                last_name=clean_last_name,
                dni=clean_dni,
                password_hash=hash_password(password),
                role=clean_role,
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Ya existe un empleado con ese DNI.") from exc

    def toggle_active(self, employee_id: int) -> bool:
        """
        Flip active/inactive for an employee.
        Returns the new active state (True = active).
        """
        return self.employee_repository.toggle_active(employee_id)

    def _normalize_dni(self, value: str) -> str:
        return re.sub(r"\s+", "", value).upper()

    def _split_full_name(self, full_name: str) -> tuple[str, str]:
        parts = full_name.strip().split(maxsplit=1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else ""
        return first_name, last_name
