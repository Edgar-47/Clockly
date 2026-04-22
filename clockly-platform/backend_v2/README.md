# ClockLy Backend v2

Backend REST separado del frontend, preparado para SaaS multiempresa simple.
Esta version convive con `backend/app` para no romper el backend web legacy.

## Stack

- Python 3.12+
- FastAPI + Uvicorn
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic v2 + pydantic-settings
- JWT access + refresh tokens
- pytest

## Estructura

```text
backend_v2/
  app/
    api/            # routers REST
    core/           # settings, seguridad, errores
    db/             # engine, sesiones, bootstrap
    dependencies/   # auth y tenant context
    models/         # SQLAlchemy ORM
    repositories/   # acceso a datos
    schemas/        # Pydantic v2
    services/       # reglas de negocio
    main.py
  alembic/
    versions/
  alembic.ini
```

## Arranque local

Desde `clockly-platform/backend_v2`:

```powershell
copy .env.example .env
docker compose -f ..\docker-compose.yml up -d postgres
python -m pip install -r ..\requirements.txt
python -m alembic upgrade head
python -m app.db.bootstrap --company-name "ClockLy Demo" --email admin@clockly.local --password "Admin12345"
python main.py --host 127.0.0.1 --port 8010 --reload
```

API:

- `POST /auth/login`
- `POST /auth/refresh`
- `GET /auth/me`
- `GET /employees`
- `POST /employees`
- `GET /attendance/sessions`
- `POST /attendance/clock-in`
- `POST /attendance/clock-out`
- `GET /metrics/overview`
- `GET /tickets`
- `POST /tickets`

## Modelo de datos

`attendance_sessions` es la tabla canonica para fichajes. La tabla tiene
`company_id`, `employee_id`, `clock_in`, `clock_out`, `duration_seconds`,
`status`, `method` y notas. Una restriccion parcial en PostgreSQL impide que
un empleado tenga mas de una sesion abierta por empresa.

El tenant se resuelve desde el JWT: cada usuario pertenece a una empresa y
todas las consultas protegidas filtran por `company_id`.

## Legacy

El backend existente en `backend/app` queda intacto. Sus puntos legacy son:

- migraciones manuales en `backend/app/database/schema.py`;
- repositorios con SQL crudo;
- mezcla de API REST, web Jinja y sesiones cookie;
- nombres historicos `businesses`/`business_id`;
- tablas de compatibilidad como `time_entries`.

La migracion real de datos debe hacerse en una fase posterior mediante scripts
controlados desde `businesses -> companies`, `business_users/users -> users`,
`users/employees -> employees` y `attendance_sessions -> attendance_sessions`.

## Siguiente fase

- Script de migracion de datos legacy con dry-run y conteos por tenant.
- Tests de integracion contra `TEST_DATABASE_URL`.
- Endpoints de empresas, invitaciones y cambio de tenant si un usuario puede
  pertenecer a mas de una empresa.
- Exportacion CSV/XLSX usando `ExportService`.
- Auditoria completa en acciones sensibles.

