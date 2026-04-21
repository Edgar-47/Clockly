# ClockLy — Production Deployment Checklist

Complete every item before serving real traffic. Items marked **CRITICAL** will
cause the app to refuse to start (enforced by `validate_runtime_config()`).

---

## 1. Variables de entorno (servidor / plataforma)

Copia `.env.production.example` como punto de partida. **Nunca** subas `.env`
al repositorio.

| Variable | Estado | Notas |
|---|---|---|
| `DATABASE_URL` | **CRITICAL** | PostgreSQL en producción, usuario dedicado con permisos mínimos |
| `CLOCKLY_ENV=production` | **CRITICAL** | Activa todas las validaciones de producción |
| `CLOCKLY_SECRET_KEY` | **CRITICAL** | Mínimo 64 bytes aleatorios: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `CLOCKLY_DEFAULT_ADMIN_PASSWORD` | **CRITICAL** | No puede ser `Admin123`. Usa una contraseña fuerte y única |
| `CLOCKLY_DEFAULT_ADMIN_USERNAME` | Recomendado | Cambia el username por defecto `admin` |
| `CLOCKLY_SECURE_COOKIES=true` | **CRITICAL** | Obligatorio para HTTPS |
| `CLOCKLY_DOCS_ENABLED=false` | **CRITICAL** | `/docs` y `/redoc` deben estar desactivados |
| `CLOCKLY_ALLOWED_ORIGINS` | **CRITICAL** | Solo tu dominio: `https://tudominio.com`. Sin `*` |
| `CLOCKLY_TRUSTED_HOSTS` | **CRITICAL** | Solo tu hostname: `tudominio.com`. Sin `*` |
| `CLOCKLY_PUBLIC_BASE_URL` | **CRITICAL** | `https://tudominio.com` (con HTTPS) |
| `CLOCKLY_SESSION_MAX_AGE` | Recomendado | 28800 (8 h). Ajusta según política de seguridad |
| `CLOCKLY_UPLOADS_DIR` | Recomendado | Ruta absoluta fuera del repositorio, con backups |
| `CLOCKLY_MAX_UPLOAD_MB` | Opcional | 5 MB por defecto |
| `FICHAJE_EXPORTS_DIR` | Opcional | Ruta absoluta para exports Excel/PDF |
| `DEFAULT_ROUTE` | Opcional | `/kiosk` o `/login` |

### Google OAuth (si se usa)
| Variable | Notas |
|---|---|
| `GOOGLE_CLIENT_ID` | Desde Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | Desde Google Cloud Console |
| `GOOGLE_REDIRECT_URI` | Debe ser `https://tudominio.com/auth/google/callback` |

---

## 2. Dominio y TLS

- [ ] Dominio apuntando al servidor (A / CNAME DNS configurado)
- [ ] Certificado TLS válido instalado (Let's Encrypt o similar)
- [ ] Redirección HTTP → HTTPS activa en el proxy inverso (nginx / Caddy)
- [ ] HSTS preload considerado para dominios establecidos
- [ ] `CLOCKLY_PUBLIC_BASE_URL` usa `https://`

---

## 3. Base de datos

- [ ] PostgreSQL en producción (no SQLite)
- [ ] Usuario dedicado con solo los permisos necesarios (`SELECT`, `INSERT`, `UPDATE`, `DELETE`)
- [ ] Backups automáticos configurados (diarios mínimo, probar restauración)
- [ ] Conexión cifrada (SSL mode `require` en `DATABASE_URL`)
- [ ] `DATABASE_URL` no contiene credenciales de dev (`clockly:clockly`)

---

## 4. Servidor de aplicación

- [ ] Uvicorn detrás de un proxy inverso (nginx, Caddy, etc.)
- [ ] Workers suficientes para carga esperada (`--workers 2` mínimo):
  ```bash
  uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
  ```
- [ ] Proxy inverso escucha en 0.0.0.0:443 y hace forward a 127.0.0.1:8000
- [ ] Proceso supervisado (systemd, Docker restart policy, etc.)
- [ ] Logs de acceso y errores capturados y rotados

---

## 5. Seguridad de archivos (uploads)

- [ ] `CLOCKLY_UPLOADS_DIR` apunta a un directorio **fuera del document root** del servidor web
- [ ] Los uploads **no** están montados como estáticos públicos
- [ ] Los archivos solo son accesibles a través de `/expenses/attachment/{id}/{id}` (requiere sesión)
- [ ] El directorio de uploads está incluido en la estrategia de backups

---

## 6. Primer arranque y superadmin

- [ ] Base de datos vacía o migrada correctamente
- [ ] Superadmin interno creado antes de exponer la app:
  ```bash
  python -m app.cli.superadmin create --email owner@example.com --name "Owner"
  ```
- [ ] El admin de negocio inicial usa la contraseña definida en `CLOCKLY_DEFAULT_ADMIN_PASSWORD`
- [ ] Se cambia la contraseña del admin en el primer acceso

---

## 7. Cliente movil Flutter

- [ ] Build movil con `CLOCKLY_API_BASE_URL` apuntando al dominio real en HTTPS:
  ```bash
  flutter build apk --release \
    --dart-define=CLOCKLY_API_BASE_URL=https://tudominio.com/api/v1
  ```
- [ ] iOS build firmado con el equipo correcto
- [ ] Android release signing reemplaza la firma debug
- [ ] El paquete/app id final no usa `com.example`

---

## 8. Monitorización y alertas

- [ ] Health check endpoint accesible por el balanceador / monitor externo
- [ ] Alertas configuradas en errores 5xx (Sentry, BetterStack, Datadog, etc.)
- [ ] Monitorización de intentos de login fallidos (brute-force detection)
- [ ] Logs de acciones de admin auditables y retenidos

---

## 9. Revisión de dependencias y seguridad

- [ ] `pip list --outdated` ejecutado; parches de seguridad aplicados
- [ ] `flutter pub outdated` ejecutado
- [ ] No hay secretos en el historial git:
  ```bash
  git log --all --oneline -S "password" -- "*.py"
  git log --all --oneline -S "SECRET_KEY"
  ```
- [ ] `.env` en `.gitignore` y **no rastreado** por git:
  ```bash
  git ls-files .env  # debe devolver vacío
  ```

---

## 10. Verificación final antes de go-live

```bash
# El servidor aborta si falta alguna variable crítica:
CLOCKLY_ENV=production uvicorn app.main:app --host 127.0.0.1 --port 8001

# Sin errores de compilación:
python -m compileall backend app

# Suite de tests verde:
python -m pytest
```

Lista de comprobación manual:
- [ ] La app arranca sin errores con `CLOCKLY_ENV=production`
- [ ] `/login` responde 200
- [ ] `/api/v1/auth/login` devuelve 422 con payload inválido (validación Pydantic activa)
- [ ] `/docs` devuelve 404 (documentación desactivada en producción)
- [ ] Cabeceras de seguridad presentes en las respuestas:
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `Content-Security-Policy: frame-ancestors 'none'`
- [ ] Los archivos de uploads no son accesibles directamente vía URL
- [ ] El reset de contraseña de empleado incluye `Cache-Control: no-store`

---

*Última revisión: 2026-04-20*
