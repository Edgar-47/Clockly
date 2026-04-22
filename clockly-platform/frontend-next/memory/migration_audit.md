# Auditoria de migracion frontend

## Funcionalidad detectada en el frontend anterior

- Layout admin con sidebar, topbar, acciones, flashes, responsive drawer y logout.
- Dashboard con uso del plan, empleados activos, fichados, KPIs de horas, top worker, hora pico, empleados en turno y ultimas sesiones.
- Empleados: listado, crear, editar, reset password, activar/desactivar, roles, DNI, horario asignado y estados.
- Fichajes/sesiones: filtros por fechas, empleado, estado e incidencias; export Excel/PDF; cierre administrativo con motivo.
- Kiosk: seleccion/cambio de negocio, login/PIN, grid de empleados, estado fichado, entrada/salida y auto-refresh.
- Portal empleado: mi fichaje y gastos propios.
- Horarios: listado, detalle, crear/editar, dias, descansos, horas netas y empleados asignados.
- Analiticas: periodos, empleado, KPIs, rankings, charts, heatmap, overtime y planificado vs real.
- Gastos: alta, listado, detalle, revision admin, filtros, importes y acciones por estado.
- Negocios: listado, alta, ajustes y cambio de contexto.
- Superadmin: login, dashboard, negocios, usuarios, planes, suscripciones, billing, metricas, ajustes, auditoria e impersonacion.
- Errores 404/500 y estados vacios.

## Estado en Next.js

- Conectado a FastAPI v2: auth, empleados, asistencia, tickets y metricas overview.
- Migrado como UX/adapters pendientes: exports, horarios, gastos, negocios, superadmin y metricas avanzadas.
- Mejoras aplicadas: servicios tipados, bearer auth centralizado, React Query, formularios Zod, componentes por dominio, estados loading/error/empty y rutas protegidas.

## Dependencias de backend

- El backend v2 no tiene todavia endpoints para schedules, expenses, businesses, superadmin ni exports.
- El cierre administrativo de sesiones necesita endpoint especifico o extension de `/attendance/clock-out`.
- Kiosk valida flujo de fichaje pero la verificacion de PIN debe aplicarse en backend para ser segura.
