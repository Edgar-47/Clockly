# Notas De Migracion

## Estado

La migracion es incremental. El backend canonico vive en `backend/app`, pero el
paquete raiz `app` queda como shim de compatibilidad para que `app.main`,
tests, scripts y Procfile sigan funcionando.

## UI Web

Las plantillas y assets se han copiado a `web/`. Las rutas HTML legacy siguen
activas y llaman servicios backend. No se ha redisenado la UI.

Login, logout y cambio de negocio ya sincronizan tambien la cookie JWT de la
API v1.

## Tablas Canonicas

- `users`: identidad global.
- `businesses`: tenant/negocio.
- `business_users`: membresia, rol y estado por negocio.
- `attendance_sessions`: fuente de verdad de fichajes.
- `plans` y `subscriptions`: limites SaaS.

## Legacy / Deprecated

- `time_entries`: legacy; no debe usarse para nuevas lecturas de fichaje.
- `business_members`: legacy de membresias; se mantiene sincronizada por
  compatibilidad.
- `employees`: tabla legacy/scoped usada para datos auxiliares e internal code;
  la identidad principal esta en `users`.

## Riesgos Pendientes

- Algunos datos historicos pueden tener `business_id` nulo hasta que se complete
  una migracion de backfill en produccion.
- La web aun no es una SPA ni usa API JSON en todos sus formularios; se mantiene
  como shim server-rendered mientras la migracion continua.
- Flutter/Dart no esta instalado en esta maquina, por lo que el scaffold movil
  queda pendiente de `flutter analyze` y `flutter test`.
- Falta implementar refresh tokens o rotacion avanzada de sesion para una app
  movil en produccion.
