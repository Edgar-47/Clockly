import re
import secrets
import string

from app.database.connection import DatabaseIntegrityError
from app.database.employee_repository import EmployeeRepository
from app.models.employee import Employee
from app.utils.security import hash_password


class EmployeeService:
    VALID_ROLES = {"admin", "employee"}

    def __init__(
        self,
        employee_repository: EmployeeRepository | None = None,
        *,
        business_id: str | None = None,
    ) -> None:
        self.business_id = business_id
        self.employee_repository = employee_repository or EmployeeRepository(
            business_id=business_id
        )

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
                business_id=self.business_id,
            )
        except DatabaseIntegrityError as exc:
            raise ValueError("Ya existe un empleado con ese DNI.") from exc

    def toggle_active(self, employee_id: int) -> bool:
        """
        Flip active/inactive for an employee.
        Returns the new active state (True = active).
        Raises ValueError if deactivating the last active admin.
        """
        employee = self.employee_repository.get_by_id(employee_id)
        if not employee:
            raise ValueError("Empleado no encontrado.")
        if employee.active and employee.role == "admin":
            if self.employee_repository.count_active_admins() <= 1:
                raise ValueError(
                    "No puedes desactivar al único administrador activo del sistema. "
                    "Crea o activa otro administrador primero."
                )
        return self.employee_repository.toggle_active(employee_id)

    def update_employee(
        self,
        employee_id: int,
        *,
        first_name: str,
        last_name: str,
        dni: str,
        role: str,
        active: bool,
    ) -> None:
        """Update employee data. Raises ValueError on validation failure."""
        employee = self.employee_repository.get_by_id(employee_id)
        if not employee:
            raise ValueError("Empleado no encontrado.")

        clean_first = first_name.strip()
        clean_last = last_name.strip()
        clean_dni = self._normalize_dni(dni)
        clean_role = role.strip().lower()

        if not clean_first:
            raise ValueError("El nombre es obligatorio.")
        if not clean_last:
            raise ValueError("El apellido es obligatorio.")
        if not clean_dni:
            raise ValueError("El DNI es obligatorio.")
        if clean_role not in self.VALID_ROLES:
            raise ValueError("Rol no válido.")

        existing = self.employee_repository.get_by_dni(clean_dni)
        if existing and existing.id != employee_id:
            raise ValueError("Ya existe un empleado con ese DNI.")

        # Last-admin guard: block any change that would leave 0 active admins.
        losing_admin_status = employee.role == "admin" and (
            clean_role != "admin" or not active
        )
        if losing_admin_status:
            if self.employee_repository.count_active_admins() <= 1:
                raise ValueError(
                    "No puedes modificar al único administrador activo del sistema. "
                    "Crea o activa otro administrador primero."
                )

        self.employee_repository.update(
            employee_id,
            first_name=clean_first,
            last_name=clean_last,
            dni=clean_dni,
            role=clean_role,
            active=active,
        )

    def set_password(self, employee_id: int, new_password: str) -> None:
        """Set a new password for an employee. Raises ValueError if too short."""
        employee = self.employee_repository.get_by_id(employee_id)
        if not employee:
            raise ValueError("Empleado no encontrado.")
        if len(new_password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        self.employee_repository.set_password_hash(employee_id, hash_password(new_password))

    def reset_password(self, employee_id: int) -> str:
        """Generate a random 8-character temporary password, save it, and return the plaintext."""
        alphabet = string.ascii_letters + string.digits
        temp_password = "".join(secrets.choice(alphabet) for _ in range(8))
        self.set_password(employee_id, temp_password)
        return temp_password

    def _normalize_dni(self, value: str) -> str:
        return re.sub(r"\s+", "", value).upper()

    def _split_full_name(self, full_name: str) -> tuple[str, str]:
        parts = full_name.strip().split(maxsplit=1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else ""
        return first_name, last_name
