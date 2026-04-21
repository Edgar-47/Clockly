import re
import secrets
import string

from app.database.connection import DatabaseIntegrityError
from app.database.business_user_repository import BusinessUserRepository
from app.database.employee_repository import EmployeeRepository
from app.database.saas_employee_repository import SaaSEmployeeRepository
from app.models.employee import Employee
from app.services.authorization_service import AuthorizationService
from app.services.subscription_service import SubscriptionService
from app.utils.security import hash_password


class EmployeeService:
    VALID_ROLES = {"admin", "manager", "employee"}

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
        self.saas_employee_repository = SaaSEmployeeRepository()
        self.business_user_repository = BusinessUserRepository()
        self.authorization_service = AuthorizationService()
        self.subscription_service = SubscriptionService()

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
        password: str = "",
        role: str = "employee",
        name: str | None = None,
        username: str | None = None,
        internal_code: str | None = None,
        pin_code: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        role_title: str | None = None,
        actor_user_id: int | None = None,
    ) -> int:
        if name and not first_name and not last_name:
            first_name, last_name = self._split_full_name(name)

        clean_first_name = first_name.strip()
        clean_last_name = last_name.strip()
        clean_role = role.strip().lower()
        clean_dni = self._normalize_dni(dni or username or "")
        clean_internal_code = self._normalize_dni(internal_code or clean_dni)
        clean_pin = (pin_code or "").strip() or None
        clean_email = (email or "").strip().lower() or None
        clean_phone = (phone or "").strip() or None
        clean_role_title = (role_title or "").strip() or None
        access_secret = password or clean_pin or ""

        if not clean_first_name:
            raise ValueError("El nombre es obligatorio.")
        if not clean_last_name:
            raise ValueError("El apellido es obligatorio.")
        if not clean_dni:
            raise ValueError("El DNI es obligatorio.")
        if not access_secret:
            raise ValueError("Introduce una contrasena o PIN de acceso.")
        if password and len(password) < 6:
            raise ValueError("La contrasena debe tener al menos 6 caracteres.")
        if clean_pin and len(clean_pin) < 4:
            raise ValueError("El PIN debe tener al menos 4 digitos.")
        if clean_role not in self.VALID_ROLES:
            raise ValueError("Rol no valido.")

        if self.business_id:
            self._enforce_actor_can_manage_role(actor_user_id, clean_role)
            if clean_role == "employee":
                self.subscription_service.assert_can_create_employee(self.business_id)
            else:
                self.subscription_service.assert_can_create_admin(self.business_id)

        duplicate = self.employee_repository.get_by_dni(clean_dni)
        if duplicate:
            raise ValueError("Ya existe un empleado con ese DNI.")

        try:
            password_hash = hash_password(access_secret)
            pin_hash = hash_password(clean_pin) if clean_pin else None
            user_id = self.employee_repository.create(
                first_name=clean_first_name,
                last_name=clean_last_name,
                dni=clean_dni,
                password_hash=password_hash,
                role=clean_role,
                business_id=self.business_id,
            )
            if self.business_id and clean_role == "employee":
                self.saas_employee_repository.create_for_user(
                    business_id=self.business_id,
                    user_id=user_id,
                    internal_code=clean_internal_code,
                    password_hash=password_hash,
                    pin_code=pin_hash,
                    first_name=clean_first_name,
                    last_name=clean_last_name,
                    email=clean_email,
                    phone=clean_phone,
                    role_title=clean_role_title,
                )
            return user_id
        except DatabaseIntegrityError as exc:
            raise ValueError("Ya existe un empleado con ese DNI o codigo interno.") from exc

    def toggle_active(
        self,
        employee_id: int,
        *,
        actor_user_id: int | None = None,
    ) -> bool:
        """
        Flip active/inactive for an employee.
        Returns the new active state (True = active).
        Raises ValueError if deactivating the last active privileged user.
        """
        employee = self.employee_repository.get_by_id(employee_id)
        if not employee:
            raise ValueError("Empleado no encontrado.")
        self._enforce_actor_can_manage_existing_employee(actor_user_id, employee)
        if employee.active and employee.role in {"owner", "admin", "manager"}:
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
        actor_user_id: int | None = None,
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

        self._enforce_actor_can_manage_existing_employee(actor_user_id, employee)
        self._enforce_actor_can_manage_role(actor_user_id, clean_role)

        existing = self.employee_repository.get_by_dni(clean_dni)
        if existing and existing.id != employee_id:
            raise ValueError("Ya existe un empleado con ese DNI.")

        losing_admin_status = employee.role in {"owner", "admin", "manager"} and (
            clean_role == "employee" or not active
        )
        if losing_admin_status:
            if self.employee_repository.count_active_admins() <= 1:
                raise ValueError(
                    "No puedes modificar al único administrador activo del sistema. "
                    "Crea o activa otro administrador primero."
                )

        gaining_admin_status = (
            self.business_id
            and employee.role == "employee"
            and clean_role in {"admin", "manager"}
        )
        if gaining_admin_status:
            self.subscription_service.assert_can_create_admin(self.business_id)

        self.employee_repository.update(
            employee_id,
            first_name=clean_first,
            last_name=clean_last,
            dni=clean_dni,
            role=clean_role,
            active=active,
        )

    def set_password(
        self,
        employee_id: int,
        new_password: str,
        *,
        actor_user_id: int | None = None,
    ) -> None:
        """Set a new password for an employee. Raises ValueError if too short."""
        employee = self.employee_repository.get_by_id(employee_id)
        if not employee:
            raise ValueError("Empleado no encontrado.")
        self._enforce_actor_can_manage_existing_employee(actor_user_id, employee)
        if len(new_password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        self.employee_repository.set_password_hash(employee_id, hash_password(new_password))

    def reset_password(
        self,
        employee_id: int,
        *,
        actor_user_id: int | None = None,
    ) -> str:
        """Generate a random 8-character temporary password, save it, and return the plaintext."""
        alphabet = string.ascii_letters + string.digits
        temp_password = "".join(secrets.choice(alphabet) for _ in range(8))
        self.set_password(employee_id, temp_password, actor_user_id=actor_user_id)
        return temp_password

    def remove_employee_from_business(
        self,
        employee_id: int,
        *,
        actor_user_id: int | None = None,
    ) -> None:
        """Disable one business membership without deleting the global user."""
        if not self.business_id:
            raise ValueError("Selecciona un negocio para eliminar el empleado.")
        employee = self.employee_repository.get_by_id(employee_id)
        if not employee:
            raise ValueError("Empleado no encontrado.")
        self._enforce_actor_can_manage_existing_employee(actor_user_id, employee)
        self.business_user_repository.disable_member(
            business_id=self.business_id,
            user_id=employee_id,
        )

    def _enforce_actor_can_manage_existing_employee(
        self,
        actor_user_id: int | None,
        employee: Employee,
    ) -> None:
        if not self.business_id or actor_user_id is None:
            return
        actor = self.authorization_service.principal_for(
            user_id=actor_user_id,
            business_id=self.business_id,
        )
        if employee.id == actor_user_id and employee.role in {"owner", "admin", "manager"}:
            raise ValueError("No puedes gestionar tu propio rol o acceso administrativo.")
        if employee.role in {"owner", "admin", "manager"} and actor.role != "owner":
            raise ValueError("Solo el propietario puede gestionar administradores o managers.")
        if employee.role == "employee" and actor.role not in {"owner", "admin"}:
            raise ValueError("No tienes permisos para gestionar empleados.")

    def _enforce_actor_can_manage_role(
        self,
        actor_user_id: int | None,
        target_role: str,
    ) -> None:
        if not self.business_id or actor_user_id is None:
            return
        actor = self.authorization_service.principal_for(
            user_id=actor_user_id,
            business_id=self.business_id,
        )
        if not self.authorization_service.can_manage_role(
            actor_role=actor.role,
            target_role=target_role,
        ):
            raise ValueError("No tienes permisos para gestionar usuarios con ese rol.")

    def _normalize_dni(self, value: str) -> str:
        return re.sub(r"\s+", "", value).upper()

    def _split_full_name(self, full_name: str) -> tuple[str, str]:
        parts = full_name.strip().split(maxsplit=1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else ""
        return first_name, last_name
