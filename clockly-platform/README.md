# ClockLy Platform

ClockLy Platform contiene la aplicacion web server-rendered, la API FastAPI y
la gobernanza de base de datos del producto SaaS. Este repositorio es la fuente
de verdad para autenticacion, tenants/negocios, usuarios, empleados, fichajes,
gastos, analiticas, suscripciones internas y migraciones.

La app movil vive en el repositorio separado `clockly-mobile`. No hay repositorio
separado para la base de datos.

## Stack

| Area | Tecnologia |
| --- | --- |
| Backend/API | Python, FastAPI, Uvicorn |
| Frontend web | Jinja2 templates, CSS/JS estatico |
| Datos | PostgreSQL via `DATABASE_URL` |
| Auth | Sesiones cookie para web, JWT Bearer para API movil |
| Exports | OpenPyXL, ReportLab |
| Tests | Pytest, FastAPI TestClient |

## Estructura

```text
clockly-platform/
  app/                  # Shim temporal para imports app.* desde la raiz
  backend/
    app/                # Backend canonico FastAPI
    migrations/         # Convencion y registro de migraciones DB
    main.py             # Entrada alternativa desde backend/
  backend_v2/           # Backend REST nuevo: FastAPI + SQLAlchemy + Alembic
  frontend/
    templates/          # HTML Jinja2 productivo
    static/             # CSS, JS e imagenes de marca
  docs/                 # Checklist produccion y contratos API
  scripts/              # Scripts locales de desarrollo
  tests/                # Suite backend/web/API
  main.py               # Entrada local compatible
  requirements.txt
  docker-compose.yml    # PostgreSQL local opcional
```

## Desarrollo local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.development.example .env
docker compose up -d postgres
python -m app.database.schema
python main.py --host 127.0.0.1 --port 8000 --reload
```

Tambien puedes usar:

```powershell
.\scripts\start-dev.ps1
```

## Frontend web

El frontend web no es una SPA separada: FastAPI renderiza `frontend/templates`
y sirve `frontend/static` en `/static`.

```powershell
python main.py --host 127.0.0.1 --port 8000 --reload
```

Rutas utiles:

- `http://127.0.0.1:8000/login`
- `http://127.0.0.1:8000/kiosk`
- `http://127.0.0.1:8000/docs` si `CLOCKLY_DOCS_ENABLED=true`

## Backend/API

La API publica para clientes externos y movil esta bajo `/api/v1`.

```powershell
python main.py --host 127.0.0.1 --port 8000 --reload
```

Desde `backend/` tambien funciona:

```powershell
python main.py --host 127.0.0.1 --port 8000 --reload
```

## Backend v2

`backend_v2/` contiene la nueva base separada del frontend: FastAPI REST,
PostgreSQL, SQLAlchemy 2.x, Alembic, Pydantic v2, JWT access/refresh y
aislamiento por `company_id`. Convive con `backend/app` para no romper el
backend web actual durante la migracion.

```powershell
cd backend_v2
copy .env.example .env
python -m alembic upgrade head
python -m app.db.bootstrap --company-name "ClockLy Demo" --email admin@clockly.local --password "Admin12345"
python main.py --host 127.0.0.1 --port 8010 --reload
```

Mas detalle en `backend_v2/README.md`.

## Variables de entorno

Usa `.env.development.example` para local y `.env.production.example` como
plantilla del proveedor de hosting. No subas `.env`.

| Variable | Uso |
| --- | --- |
| `DATABASE_URL` | PostgreSQL principal |
| `TEST_DATABASE_URL` | PostgreSQL aislado para tests; el nombre debe contener `test` |
| `CLOCKLY_ENV` | `development` o `production` |
| `CLOCKLY_SECRET_KEY` | Firma sesiones web y tokens JWT |
| `CLOCKLY_DEFAULT_ADMIN_USERNAME` | Usuario inicial de negocio |
| `CLOCKLY_DEFAULT_ADMIN_PASSWORD` | Password inicial; cambia en produccion |
| `CLOCKLY_ALLOWED_ORIGINS` | Origenes CORS permitidos |
| `CLOCKLY_TRUSTED_HOSTS` | Hostnames validos en produccion |
| `CLOCKLY_SECURE_COOKIES` | Cookies solo HTTPS en produccion |
| `CLOCKLY_DOCS_ENABLED` | Habilita o deshabilita `/docs` |
| `CLOCKLY_UPLOADS_DIR` | Directorio runtime para tickets subidos |
| `FICHAJE_EXPORTS_DIR` | Directorio runtime para exports |

## Migraciones de base de datos

Estado actual: PostgreSQL. Los restos SQLite eran legacy y se han retirado de
la entrega limpia.

El backend gobierna la base de datos desde `backend/app/database/schema.py`.
Ese modulo contiene el schema inicial y migraciones idempotentes que se ejecutan
en el arranque de FastAPI y tambien manualmente:

```powershell
python -m app.database.schema
```

La carpeta `backend/migrations` documenta el estado y la convencion para futuras
migraciones. Para el MVP no se introduce Alembic todavia; seria el siguiente
paso natural cuando haya despliegues multi-entorno con historico de versiones.

## Tests

```powershell
$env:TEST_DATABASE_URL="postgresql://clockly:clockly@localhost:5432/clockly_test"
python -m pytest
python -m compileall backend app tests
```

Si `TEST_DATABASE_URL` no existe, los tests de integracion PostgreSQL se saltan.

## Flujo recomendado

1. Crear una rama corta por cambio.
2. Actualizar backend, frontend o migraciones en el mismo repo cuando afecten al contrato web/API.
3. Mantener `docs/contracts/api_v1.md` alineado si cambia `/api/v1`.
4. Ejecutar tests backend antes de abrir PR.
5. Coordinar cambios de API con `clockly-mobile`.

## Notas de despliegue

- Produccion debe usar PostgreSQL gestionado, backups y `CLOCKLY_ENV=production`.
- `CLOCKLY_SECRET_KEY`, `CLOCKLY_DEFAULT_ADMIN_PASSWORD`, CORS y trusted hosts
  son obligatorios y se validan al arrancar.
- Los uploads y exports son runtime data; no se versionan.
- `docker-compose.yml` es solo para desarrollo local.
- Revisa `docs/PRODUCTION_CHECKLIST.md` antes de exponer trafico real.
