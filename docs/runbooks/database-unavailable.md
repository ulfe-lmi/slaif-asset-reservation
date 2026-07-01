# Runbook: Database Unavailable or Readiness Failure

Symptoms:

- `/health/live` returns 200 but `/health/ready` returns 503;
- `python manage.py operational_check` reports database or migration failure.

Checks:

1. Confirm PostgreSQL process/container health.
2. Confirm network connectivity from the application container to PostgreSQL.
3. Confirm `DATABASE_URL` points to the intended database.
4. Confirm disk space and PostgreSQL connection limits.
5. Run `python manage.py showmigrations --plan` and `python manage.py operational_check`.

Do not expose database hostnames, passwords, or internal exception text in user-facing incidents.
