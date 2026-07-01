# Runbook: Migration and Rollback

## Before Migration

- Confirm the target release commit and reviewed migrations.
- Take a PostgreSQL backup and verify the artifact exists.
- Run `python manage.py migrate --plan`.
- Confirm `btree_gist` is available for the migration role.

## Migration

```bash
python manage.py migrate --noinput
python manage.py operational_check
```

Application workers must not run migrations implicitly at startup.

## Rollback Posture

Rollback is restore-and-redeploy for internal alpha. The repository does not yet claim
zero-downtime expand/contract migration support. If a migration fails after partial database
changes, stop, preserve logs, restore into an isolated database first, and get human approval before
touching production data.
