---
name: ClockLy Next.js frontend
description: Estado del nuevo frontend Next.js creado en frontend-next/
type: project
---

Nuevo frontend Next.js creado en `frontend-next/`. Build pasa limpio.

**Why:** Migración de Jinja2/server-rendered a Next.js 15 App Router con TypeScript, Tailwind, TanStack Query.

**How to apply:** Saber que el frontend-next/ es el activo; frontend/ es legacy y no se toca.

Stack: Next.js 16 (latest patched), TypeScript, Tailwind 3, shadcn-style components sin CLI, TanStack Query v5, Zustand (solo kiosk), React Hook Form + Zod, Sonner para toasts.

API: todos los servicios apuntan a `/api/v1/*` (proxy en next.config.ts → backend FastAPI en NEXT_PUBLIC_API_URL).

Endpoints conectados: `/auth/login`, `/auth/logout`, `/auth/me`, `/employees`, `/attendance`, `/attendance/clock-in`, `/attendance/clock-out`, `/attendance/history`, `/dashboard/summary`.

Endpoints mock/placeholder: `/auth/forgot-password` (botón desactivado), `/exports` (botón disabled en sessions table).

Rutas placeholder: `/schedules`, `/analytics`, `/settings` — muestran "Próximamente".
