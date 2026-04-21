# ClockLy Repository Split Migration Plan

## Executive summary

The original `App_Fichaje` workspace mixed backend, web templates, contracts,
docs, a legacy mobile attempt, a newer Flutter app and local IDE/tooling state.
It has been reorganized into two publishable repo roots:

- `clockly-platform`: FastAPI backend, server-rendered web frontend, database
  migration governance, tests, docs and local development config.
- `clockly-mobile`: Flutter mobile app for Android/iOS consuming `/api/v1`.

There is no separate database repository. PostgreSQL remains governed by the
backend.

## What moved to clockly-platform

- Canonical backend from `backend/app`.
- Web UI from `web/` into `frontend/`.
- API contracts from `contracts/` into `docs/contracts/`.
- Backend tests from `tests/`.
- Root runtime entrypoints: `main.py`, `Procfile`, `requirements.txt`.
- Environment examples and production checklist.
- Local PostgreSQL `docker-compose.yml`.

## What moved to clockly-mobile

- Canonical Flutter app from `mobile_flutter/clockly_flutter_aplication`.
- Existing local Flutter UI changes were preserved.
- Brand SVG assets needed by the app.
- Android/iOS platform folders, tests, analyzer config and lockfile.

## What was removed

- Duplicate legacy root backend copy under `app/`, except the compatibility
  shim `app/__init__.py` in `clockly-platform`.
- Duplicate backend templates/static/assets under `backend/app`.
- Older lightweight Flutter attempt under `mobile_flutter/lib`.
- Generated desktop/web Flutter platforms from the mobile repo.
- IDE/agent state: `.idea`, `.claude`.
- Legacy SQLite smoke script `test_kiosk_flow.py`.
- Runtime outputs such as exports, caches and build artifacts.

## Kept temporarily for compatibility

- `clockly-platform/app/__init__.py` so imports like `app.main` keep working.
- `clockly-platform/main.py` and `Procfile` for existing local/deploy commands.
- Idempotent Python migration runner in `backend/app/database/schema.py`.

## Database state

Current runtime database is PostgreSQL via `DATABASE_URL`. The migration runner
is backend-owned and idempotent. `backend/migrations` documents the baseline and
future migration convention. Alembic is a recommended future step, not required
for the MVP split.

## Known risks

- Some historical docs mention `web/`; updated primary docs now use `frontend/`.
- Flutter was not verified with SDK commands in this environment unless stated
  in the final handoff.
- Android release signing still uses debug signing and must be replaced before
  Play Store distribution.
- Existing backend integration tests require a PostgreSQL test database.
