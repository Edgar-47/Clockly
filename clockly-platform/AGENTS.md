# AGENTS.md

Guidelines for automated changes in `clockly-platform`.

- Keep the backend and web frontend in this repo. Do not create a separate DB
  repo or split into microservices during MVP work.
- Treat `backend/app` as the canonical backend package.
- Keep root `app/__init__.py` as a temporary compatibility shim for imports
  such as `app.main`; do not add business logic there.
- Serve web templates and static files from `frontend/`.
- Put database changes under backend ownership. Today that means
  `backend/app/database/schema.py` plus notes in `backend/migrations`.
- Do not commit `.env`, local databases, uploads, exports, caches or build
  output.
- Update `docs/contracts/api_v1.md` when changing `/api/v1`.
- Prefer small, reversible changes. Avoid broad rewrites unless a test or bug
  requires them.
- Before finishing backend changes, run at least:

```powershell
python -m compileall backend app tests
python -m pytest
```

If PostgreSQL is unavailable, report which tests were skipped or not run.
