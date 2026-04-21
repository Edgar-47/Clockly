# ClockLy Frontend Web

Interfaz web server-rendered con Jinja2 y assets estaticos.

## Estado actual

- Las plantillas viven en `frontend/templates`.
- Los assets viven en `frontend/static`.
- FastAPI monta esta UI desde `backend/app/main.py`.
- Las rutas HTML actuales se mantienen para no romper la app existente.
- Login, logout y cambio de negocio sincronizan la cookie JWT HttpOnly usada
  por la API v1.

## Migracion progresiva

La UI web puede ir pasando gradualmente de formularios HTML directos a llamadas
contra `/api/v1`, manteniendo la misma logica backend.

Prioridad recomendada:

1. Login y `GET /auth/me`.
2. Selector de negocio.
3. Fichaje de empleado.
4. Dashboard.
5. Gestion de empleados.
6. Historial de sesiones y exportaciones.

Durante la transicion, las rutas HTML siguen llamando servicios backend y no
duplican reglas de negocio en el frontend.
