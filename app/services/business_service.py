from __future__ import annotations

import json
import re
import secrets
import unicodedata
import uuid
from datetime import datetime

from app.database.connection import DatabaseIntegrityError
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

    def ensure_legacy_business_for_user(self, user_id: int) -> Business | None:
        """
        Create a default workspace for older single-business databases.

        Fresh installs still go through onboarding. This only runs when legacy
        employees or attendance records already exist without business_id.
        """
        if self.business_repository.count_for_user(user_id) > 0:
            return self.choose_default_business(user_id)
        if self.business_repository.count_all() > 0:
            return None
        if not self.business_repository.has_unscoped_legacy_data():
            return None

        return self.create_business(
            owner_user_id=user_id,
            business_name="Negocio principal",
            business_type="otro",
            login_code="CLOCKLY",
        )

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
        raw_login_code = (login_code or "").strip()
        clean_login_code = self._normalize_login_code(raw_login_code)
        login_code_generated = False

        if not clean_name:
            raise ValueError("El nombre del negocio es obligatorio.")
        if len(clean_name) < 2:
            raise ValueError("El nombre del negocio debe tener al menos 2 caracteres.")
        if raw_login_code and not clean_login_code:
            raise ValueError(
                "El codigo de inicio solo puede contener letras, numeros, guiones y guiones bajos."
            )
        if not clean_login_code:
            clean_login_code = self._generate_unique_login_code(clean_name)
            login_code_generated = True
        if len(clean_login_code) < 3:
            raise ValueError("El codigo de inicio de sesion debe tener al menos 3 caracteres.")

        if self.business_repository.get_by_login_code(clean_login_code):
            raise ValueError("Ya existe un negocio activo con ese codigo de inicio.")

        include_legacy_records = self.business_repository.count_all() == 0
        settings_json = json.dumps(
            {"onboarding_version": 1},
            ensure_ascii=True,
            separators=(",", ":"),
        )

        business: Business | None = None
        for attempt in range(5):
            business_id = str(uuid.uuid4())
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
                break
            except DatabaseIntegrityError as exc:
                if login_code_generated and attempt < 4:
                    clean_login_code = self._generate_unique_login_code(clean_name)
                    continue
                raise ValueError("Ya existe un negocio con ese codigo o identificador.") from exc
        if business is None:
            raise RuntimeError("No se pudo crear el negocio.")

        return self.activate_business_for_user(
            user_id=owner_user_id,
            business_id=business.id,
        )

    def update_business(
        self,
        *,
        requester_user_id: int,
        business_id: str,
        business_name: str,
        business_type: str,
        login_code: str,
        settings_json: str | dict | None = None,
    ) -> Business:
        if not self.business_repository.user_has_access(
            business_id=business_id,
            user_id=requester_user_id,
        ):
            raise ValueError("No tienes acceso a este negocio.")

        current = self.business_repository.get_by_id(business_id)
        if current is None:
            raise ValueError("Negocio no encontrado.")

        clean_name = self._clean_business_name(business_name)
        clean_type = self._normalize_business_type(business_type)
        clean_login_code = self._normalize_login_code(login_code)
        clean_settings = self._normalize_settings_json(
            settings_json,
            fallback=current.settings_json,
        )

        if not clean_name:
            raise ValueError("El nombre del negocio es obligatorio.")
        if len(clean_name) < 2:
            raise ValueError("El nombre del negocio debe tener al menos 2 caracteres.")
        if not clean_login_code:
            raise ValueError("El codigo de inicio de sesion es obligatorio.")
        if len(clean_login_code) < 3:
            raise ValueError("El codigo de inicio de sesion debe tener al menos 3 caracteres.")

        duplicate = self.business_repository.get_by_login_code(clean_login_code)
        if duplicate and duplicate.id != business_id:
            raise ValueError("Ya existe un negocio activo con ese codigo de inicio.")

        try:
            return self.business_repository.update(
                business_id=business_id,
                business_name=clean_name,
                business_type=clean_type,
                login_code=clean_login_code,
                settings_json=clean_settings,
            )
        except DatabaseIntegrityError as exc:
            raise ValueError("Ya existe un negocio con ese codigo o identificador.") from exc

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

    def _generate_unique_login_code(self, business_name: str) -> str:
        prefix = re.sub(r"[^A-Z0-9]", "", self._ascii_key(business_name).upper())
        prefix = (prefix[:6] or "BIZ").strip("-_")
        for _ in range(20):
            candidate = f"{prefix}-{secrets.token_hex(3).upper()}"
            if not self.business_repository.get_by_login_code(candidate):
                return candidate
        raise ValueError("No se pudo generar un codigo de inicio unico.")

    def _normalize_settings_json(
        self,
        value: str | dict | None,
        *,
        fallback: str = "{}",
    ) -> str:
        if value is None:
            value = fallback
        if isinstance(value, dict):
            parsed = value
        else:
            text = value.strip() or "{}"
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError("La configuracion del negocio debe ser JSON valido.") from exc
        if not isinstance(parsed, dict):
            raise ValueError("La configuracion del negocio debe ser un objeto JSON.")
        return json.dumps(parsed, ensure_ascii=True, separators=(",", ":"))

    def _now(self) -> str:
        return datetime.now().replace(microsecond=0).isoformat(sep=" ")

    def _ascii_key(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.strip().lower())
        return normalized.encode("ascii", "ignore").decode("ascii")
