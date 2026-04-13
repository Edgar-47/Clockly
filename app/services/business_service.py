from __future__ import annotations

import json
import re
import secrets
import sqlite3
import unicodedata
import uuid
from datetime import datetime

from app.database.business_repository import BusinessRepository
from app.database.employee_repository import EmployeeRepository
from app.models.business import Business


class BusinessService:
    BUSINESS_TYPES = {
        "cafeteria": "Cafeteria",
        "restaurante": "Restaurante",
        "bar": "Bar",
        "tienda": "Tienda",
        "taller": "Taller",
        "peluqueria": "Peluqueria",
        "clinica": "Clinica",
        "gimnasio": "Gimnasio",
        "oficina": "Oficina",
        "otro": "Otro",
    }

    def __init__(
        self,
        business_repository: BusinessRepository | None = None,
        employee_repository: EmployeeRepository | None = None,
    ) -> None:
        self.business_repository = business_repository or BusinessRepository()
        self.employee_repository = employee_repository or EmployeeRepository()

    def requires_onboarding(self, user_id: int) -> bool:
        return self.business_repository.count_for_user(user_id) == 0

    def count_for_user(self, user_id: int) -> int:
        return self.business_repository.count_for_user(user_id)

    def list_businesses_for_user(self, user_id: int) -> list[Business]:
        return self.business_repository.list_for_user(user_id)

    def choose_default_business(self, user_id: int) -> Business | None:
        businesses = self.list_businesses_for_user(user_id)
        return businesses[0] if businesses else None

    def activate_business_for_user(self, *, user_id: int, business_id: str) -> Business:
        if not self.business_repository.user_has_access(
            business_id=business_id,
            user_id=user_id,
        ):
            raise ValueError("No tienes acceso a este negocio.")

        accessed_at = self._now()
        self.business_repository.mark_accessed(
            business_id=business_id,
            user_id=user_id,
            accessed_at=accessed_at,
        )
        business = self.business_repository.get_by_id(business_id)
        if business is None:
            raise ValueError("Negocio no encontrado.")
        return business

    def create_business(
        self,
        *,
        owner_user_id: int,
        business_name: str,
        business_type: str,
        login_code: str,
    ) -> Business:
        owner = self.employee_repository.get_by_id(owner_user_id)
        if not owner or not owner.active:
            raise ValueError("Usuario propietario no valido.")
        if owner.role != "admin":
            raise ValueError("Solo un administrador puede crear negocios.")

        clean_name = self._clean_business_name(business_name)
        clean_type = self._normalize_business_type(business_type)
        clean_login_code = self._normalize_login_code(login_code)

        if not clean_name:
            raise ValueError("El nombre del negocio es obligatorio.")
        if len(clean_name) < 2:
            raise ValueError("El nombre del negocio debe tener al menos 2 caracteres.")
        if not clean_login_code:
            raise ValueError("El codigo de inicio de sesion es obligatorio.")
        if len(clean_login_code) < 3:
            raise ValueError("El codigo de inicio de sesion debe tener al menos 3 caracteres.")

        if self.business_repository.get_by_login_code(clean_login_code):
            raise ValueError("Ya existe un negocio activo con ese codigo de inicio.")

        business_id = str(uuid.uuid4())
        include_legacy_records = self.business_repository.count_all() == 0
        settings_json = json.dumps(
            {"onboarding_version": 1},
            ensure_ascii=True,
            separators=(",", ":"),
        )

        try:
            business = self.business_repository.create(
                business_id=business_id,
                owner_user_id=owner_user_id,
                business_name=clean_name,
                business_type=clean_type,
                login_code=clean_login_code,
                slug=self._build_slug(clean_name, business_id),
                business_key=self._generate_business_key(),
                settings_json=settings_json,
                mark_default=True,
                include_legacy_records=include_legacy_records,
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Ya existe un negocio con ese codigo o identificador.") from exc

        return self.activate_business_for_user(
            user_id=owner_user_id,
            business_id=business.id,
        )

    def _clean_business_name(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _normalize_business_type(self, value: str) -> str:
        clean = self._ascii_key(value)
        clean = re.sub(r"\s+", "_", clean)
        if clean not in self.BUSINESS_TYPES:
            raise ValueError("Selecciona un tipo de negocio valido.")
        return clean

    def _normalize_login_code(self, value: str) -> str:
        clean = re.sub(r"\s+", "-", value.strip().upper())
        clean = re.sub(r"[^A-Z0-9_-]", "", clean)
        return clean[:32]

    def _build_slug(self, business_name: str, business_id: str) -> str:
        base = self._ascii_key(business_name)
        base = re.sub(r"[^a-z0-9]+", "-", base)
        base = base.strip("-") or "negocio"
        return f"{base[:42].strip('-')}-{business_id[:8]}"

    def _generate_business_key(self) -> str:
        return f"BUS-{secrets.token_hex(4).upper()}"

    def _now(self) -> str:
        return datetime.now().replace(microsecond=0).isoformat(sep=" ")

    def _ascii_key(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.strip().lower())
        return normalized.encode("ascii", "ignore").decode("ascii")
