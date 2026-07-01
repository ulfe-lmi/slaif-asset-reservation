# Runbook: Expired Idempotency Cleanup

Dry-run:

```bash
python manage.py purge_expired_idempotency_records
```

Apply:

```bash
python manage.py purge_expired_idempotency_records --apply
```

The command deletes only records whose `expires_at` is in the past and reports deterministic counts.
It is safe to run repeatedly. Scheduling remains operator responsibility through cron or systemd
timer; no Celery or queue is implemented.
