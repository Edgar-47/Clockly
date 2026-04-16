# ClockLy Web

Interfaz web server-rendered con Jinja2 y assets estaticos.

## Estado actual

- Las plantillas viven en `web/templates`.
- Los assets viven en `web/static`.
- FastAPI monta esta UI desde `backend/app/main.py`.
- Las rutas HTML actuales se mantienen como capa de compatibilidad para no
  romper la app existente.
- Login, logout y cambio de negocio ya emiten o limpian la cookie JWT HttpOnly
  usada por la API v1.

## Migracion progresiva

La UI web debe ir pasando de formularios HTML directos a servicios/cliente API
contra `/api/v1`, manteniendo la misma estetica y la misma logica backend.

Prioridad recomendada:

1. Login y `GET /auth/me`.
2. Selector de negocio.
3. Fichaje de empleado.
4. Dashboard.
5. Gestion de empleados.
6. Historial de sesiones y exportaciones.

Durante la transicion, las rutas HTML siguen usando servicios backend, no
duplican reglas de negocio en frontend.
