# ClockLy Frontend Next

Frontend operativo de ClockLy migrado a Next.js App Router, TypeScript, Tailwind CSS, componentes shadcn/ui, React Hook Form, Zod y TanStack Query.

## Arranque

```bash
npm install
npm run dev
```

Por defecto espera el backend v2 en:

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8010
```

El backend v2 se puede arrancar desde `../backend_v2`:

```bash
python main.py --host 127.0.0.1 --port 8010
```

## Verificacion

```bash
npm run type-check
npx next build --webpack
```

En este workspace dentro de OneDrive, `next build` con Turbopack puede fallar con `EPERM` al renombrar archivos generados. El build con webpack fue validado correctamente.

## Migrado

- Login, logout, estado de sesion y rutas protegidas.
- Dashboard conectado a empleados, fichajes y metricas v2.
- Gestion de empleados: listado, busqueda, alta, edicion y activar/desactivar.
- Sesiones/fichajes: filtros por fecha/estado, tabla, estados vacios y links de export adapter.
- Kiosk tactil: grid de empleados, PIN, entrada/salida y feedback de exito.
- Tickets/incidencias: listado y creacion conectados a `/tickets`.
- Analiticas basicas conectadas a `/metrics/overview`.
- Pantallas preparadas para horarios, gastos, negocios y superadmin con adapters documentados.

## Pendiente de backend v2

- `/exports/*` para Excel/PDF de asistencia.
- `/schedules/*` para horarios y planificado vs real.
- `/expenses/*` para gastos de empleados y aprobacion admin.
- `/businesses/*` para selector y administracion multi-negocio.
- `/superadmin/*`, planes, billing, auditoria e impersonacion.
- Metricas avanzadas: ranking, heatmap, overtime trend y planificado vs real.
