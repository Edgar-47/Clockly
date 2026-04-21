# ClockLy Backend

Backend FastAPI canonico de ClockLy.

## Contenido

- `app/api/routes`: rutas HTML legacy/server-rendered.
- `app/api/v1`: API JSON consumida por Flutter.
- `app/services`: reglas de negocio.
- `app/database`: repositorios, conexion PostgreSQL y runner de migraciones.
- `migrations`: convencion y registro de migraciones para el MVP.

## Ejecutar

Desde la raiz de `clockly-platform`:

```powershell
python main.py --host 127.0.0.1 --port 8000 --reload
```

Desde `backend/`:

```powershell
python main.py --host 127.0.0.1 --port 8000 --reload
```

## Migraciones

```powershell
python -m app.database.schema
```

FastAPI tambien ejecuta `initialize_database()` en startup. Las migraciones son
idempotentes para mantener compatibilidad con el MVP.
