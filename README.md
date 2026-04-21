# ClockLy

ClockLy es una aplicación FastAPI para control horario, fichaje en modo kiosco,
gestión de empleados, gastos/tickets, analíticas y administración SaaS básica.
El proyecto queda preparado para producción sin publicar ni desplegar nada.

## Stack

| Área | Tecnología |
|---|---|
| Backend web/API | FastAPI, Jinja2, Uvicorn |
| Datos | PostgreSQL mediante `DATABASE_URL` |
| Seguridad | Cookies firmadas, JWT HS256 para API móvil, PBKDF2-SHA256 |
| Exportación | OpenPyXL, ReportLab |
| Cliente móvil/web | Flutter en `mobile_flutter/clockly_flutter_aplication` |

## Arquitectura actual

```text
App_Fichaje/
  main.py                         # Entrada local compatible
  Procfile                        # Target ASGI: app.main:app
  app/                            # Shim de compatibilidad; carga backend/app primero
  backend/app/                    # Backend canónico
  web/templates/                  # Plantillas HTML productivas
  web/static/                     # CSS/JS productivo
  mobile_flutter/clockly_flutter_aplication/
  contracts/                      # Contratos y notas de API
  tests/                          # Suite PostgreSQL/FastAPI
```

El paquete raíz `app` mantiene compatibilidad con comandos existentes, pero
resuelve los módulos desde `backend/app` primero. El backend canónico es
`backend/app`.

## Desarrollo local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.development.example .env
python main.py --host 127.0.0.1 --port 8000
```

También puedes usar:

```powershell
.\ejecutar_app.ps1
```

## Tests y checks

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall backend app tests
```

`TEST_DATABASE_URL` debe apuntar a una base PostgreSQL cuyo nombre contenga
`test`; la fixture de tests borra y recrea el esquema público.

## Configuración

Usa `.env.development.example` para local y `.env.production.example` como
plantilla para variables del proveedor de hosting. No commits secretos reales.

Variables críticas:

| Variable | Uso |
|---|---|
| `DATABASE_URL` | PostgreSQL principal |
| `TEST_DATABASE_URL` | PostgreSQL aislado para tests |
| `CLOCKLY_ENV` | `development` o `production` |
| `CLOCKLY_SECRET_KEY` | Firma de sesión y tokens |
| `CLOCKLY_DEFAULT_ADMIN_PASSWORD` | Password inicial del admin de negocio |
| `CLOCKLY_SECURE_COOKIES` | Cookies solo HTTPS en producción |
| `CLOCKLY_DOCS_ENABLED` | `/docs` y `/redoc`; debe ser `false` en producción |
| `CLOCKLY_TRUSTED_HOSTS` | Hostnames reales permitidos |
| `CLOCKLY_ALLOWED_ORIGINS` | Orígenes CORS permitidos para la API |
| `CLOCKLY_UPLOADS_DIR` | Directorio privado de tickets subidos |
| `CLOCKLY_PUBLIC_BASE_URL` | URL pública HTTPS cuando exista dominio |

## Primer acceso

En el primer arranque se crea un administrador de negocio inicial si la base
está vacía. En desarrollo usa `admin` / `Admin123`. En producción debes definir
una contraseña fuerte en `CLOCKLY_DEFAULT_ADMIN_PASSWORD`.

El Superadmin interno está separado del login normal. No se siembra
automáticamente:

```powershell
python -m app.cli.superadmin create --email owner@example.com --name "Owner Name"
```

## Producción sin deploy

El comando productivo de referencia es:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Antes de publicar, revisa `docs/PRODUCTION_CHECKLIST.md`. Este repositorio no
incluye secretos reales, dominios conectados ni releases públicas.
