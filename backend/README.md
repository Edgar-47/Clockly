# ClockLy Backend

Backend FastAPI de ClockLy. Es la fuente de verdad para autenticacion,
negocios, usuarios, empleados, permisos, fichajes y dashboard.

## Ejecutar

Desde la raiz del repositorio:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

Tambien puedes ejecutar desde `backend/`:

```powershell
python main.py
```

En produccion Railway mantiene compatibilidad con:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Variables principales

- `DATABASE_URL`: PostgreSQL principal.
- `TEST_DATABASE_URL`: PostgreSQL de tests; el nombre debe contener `test`.
- `CLOCKLY_SECRET_KEY`: firma sesiones web y JWT de API.
- `CLOCKLY_SESSION_MAX_AGE`: vida del token/cookie.
- `CLOCKLY_SECURE_COOKIES`: cookies seguras en HTTPS.
- `CLOCKLY_DOCS_ENABLED`: habilita `/docs` y `/redoc`.

## API

La API publica esta bajo `/api/v1`. Flutter debe usar `Authorization: Bearer`.
La web puede compartir la cookie HttpOnly `clockly_access_token` mientras se
mantienen las sesiones HTML legacy.

## Tests

```powershell
$env:TEST_DATABASE_URL="postgresql://clockly:clockly@localhost:5432/clockly_test"
.\.venv\Scripts\python.exe -m pytest
```

Si `TEST_DATABASE_URL` no existe, los tests de integracion PostgreSQL se saltan.
