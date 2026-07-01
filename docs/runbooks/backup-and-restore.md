# Runbook: Backup and Restore

SLAIF uses PostgreSQL-native logical backup tools for the initial internal-alpha shape.

## Backup

Dry-run validation:

```bash
python manage.py backup_database --output /backups/slaif-$(date +%Y%m%d).dump
```

Create a backup:

```bash
python manage.py backup_database --output /backups/slaif-$(date +%Y%m%d).dump --apply
```

The command requires `DATABASE_URL`, refuses missing output directories, and does not print the
database password. Operators own retention, encryption, off-host copy, and failure alerts.

## Restore Drill

Never restore over production without a separate human-approved incident plan. Validate first:

```bash
python manage.py restore_database --input /backups/slaif-YYYYMMDD.dump
```

Restore into an isolated database:

```bash
python manage.py restore_database --input /backups/slaif-YYYYMMDD.dump --apply
python manage.py operational_check
```

After restore, compare user, asset, reservation, token, idempotency, blackout, and audit row counts
against the source environment where appropriate.
