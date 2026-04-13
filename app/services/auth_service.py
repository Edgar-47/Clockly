from app.database.employee_repository import EmployeeRepository
from app.models.employee import Employee
from app.utils.security import verify_password


class AuthService:
    def __init__(self, employee_repository: EmployeeRepository | None = None) -> None:
        self.employee_repository = employee_repository or EmployeeRepository()

    def login(self, identifier: str, password: str) -> Employee:
        clean_identifier = identifier.strip()
        if not clean_identifier or not password:
            raise ValueError("Introduce identificador y contrasena.")

        employee = self.employee_repository.get_by_identifier(clean_identifier)
        if not employee or not employee.active:
            raise ValueError("Identificador o contrasena incorrectos.")

        if not verify_password(password, employee.password_hash):
            raise ValueError("Identificador o contrasena incorrectos.")

        return employee

    def verify_employee_password(self, employee_id: int, password: str) -> Employee:
        if not password:
            raise ValueError("Introduce la contrasena.")

        employee = self.employee_repository.get_by_id(employee_id)
        if not employee or not employee.active:
            raise ValueError("Empleado no valido o inactivo.")

        if not verify_password(password, employee.password_hash):
            raise ValueError("Contrasena incorrecta.")

        return employee
