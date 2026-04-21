# ClockLy Database Migrations

ClockLy does not use a separate database repository. Database structure is
owned by the backend in this repo.

## Current MVP approach

The active migration runner is `backend/app/database/schema.py`.

It contains:

- `SCHEMA_SQL`: baseline PostgreSQL schema.
- `initialize_database()`: ordered startup runner.
- `_migrate_*` functions: idempotent migrations and backfills.
- seed/bootstrap logic for default plans, subscriptions and first admin.

Run it manually from the `clockly-platform` root:

```powershell
python -m app.database.schema
```

FastAPI also calls it during startup.

## Why no Alembic yet

For the MVP, the existing idempotent runner is faster and safer than introducing
a new migration framework while the schema is still moving quickly. The next
step, when production releases need strict version history, is to introduce
Alembic here in `backend/migrations` and convert the current state into a first
baseline revision.

## Rules

- Never create a separate DB repository.
- Keep schema changes backend-owned and reviewed with API changes.
- New migrations must be idempotent until a versioned migration tool is adopted.
- Never commit local databases, dumps with customer data, or credentials.
