# 0001 Current PostgreSQL State

This is the baseline migration record for the repository split.

The executable source of truth is currently:

```text
backend/app/database/schema.py
```

It creates and migrates these main areas:

- identity and tenant tables: `users`, `businesses`, `business_users`
- attendance: `attendance_sessions`, legacy-compatible `time_entries`
- planning: `work_schedules`, `schedule_days`, `employee_schedules`
- SaaS billing metadata: `plans`, `subscriptions`, `payment_records`
- expenses: `expenses`, `expense_attachments`
- audit and platform settings: `audit_logs`, `platform_settings`

This file exists so future migration tooling has an explicit baseline anchor.
