from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.employee import Employee
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.user_repository import UserRepository
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeService:
    def __init__(self, db: Session, *, company_id: UUID) -> None:
        self.db = db
        self.company_id = company_id
        self.employees = EmployeeRepository(db, company_id=company_id)
        self.users = UserRepository(db)

    def list_employees(self, *, include_inactive: bool = False) -> list[Employee]:
        return self.employees.list(include_inactive=include_inactive)

    def create_employee(self, payload: EmployeeCreate) -> Employee:
        linked_user: User | None = None
        if payload.email and payload.password:
            existing = self.users.get_by_email(payload.email)
            if existing is not None:
                raise ConflictError("A user with this email already exists.")
            linked_user = User(
                company_id=self.company_id,
                email=payload.email,
                full_name=f"{payload.first_name} {payload.last_name}".strip(),
                password_hash=hash_password(payload.password),
                role=UserRole.EMPLOYEE,
            )
            self.users.add(linked_user)

        employee = Employee(
            company_id=self.company_id,
            user_id=linked_user.id if linked_user else None,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            phone=payload.phone,
            dni=payload.dni,
            role_title=payload.role_title,
            pin_hash=hash_password(payload.pin) if payload.pin else None,
            hired_on=payload.hired_on,
            is_active=payload.is_active,
        )
        try:
            self.employees.add(employee)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Employee data conflicts with an existing employee.") from exc
        return employee

    def update_employee(self, employee_id: UUID, payload: EmployeeUpdate) -> Employee:
        employee = self.employees.get(employee_id)
        if employee is None:
            raise NotFoundError("Employee not found.")
        updates = payload.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(employee, key, value)
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee

