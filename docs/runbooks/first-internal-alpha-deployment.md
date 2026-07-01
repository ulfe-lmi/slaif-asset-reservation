# Runbook: First Internal-Alpha Deployment

This runbook is an operator checklist for a future internal-alpha host. It is not evidence that a
production deployment has happened.

## Preconditions

- Linux host with Docker and Compose v2.
- DNS name and TLS plan selected.
- Protected secret store or host-only secret files prepared.
- PostgreSQL storage and backup destination selected.
- Human maintainer approval for the release commit.

## Steps

1. Build or pull the reviewed image.
2. Copy `deploy/env.production.example` to the ignored host-local file `deploy/env.production` and
   replace every placeholder from a protected secret store. Never commit `deploy/env.production`.
3. Store the PostgreSQL password in `deploy/secrets/postgres_password` or an equivalent protected
   secret mount.
4. Review `compose.production.example.yaml`; do not publish PostgreSQL publicly.
5. Configure Caddy or another reverse proxy for HTTPS. The example `deploy/Caddyfile.example`
   forwards to the loopback application port.
6. Run migrations deliberately:

   ```bash
   docker compose -f compose.production.example.yaml run --rm app python manage.py migrate --noinput
   ```

7. Run operational checks:

   ```bash
   docker compose -f compose.production.example.yaml run --rm app python manage.py operational_check
   ```

8. Start the application and verify `/health/live`, `/health/ready`, `/login/`, `/manage/`, and a
   safe unauthenticated API failure.

## Not Covered

This runbook does not configure OIDC, email, notifications, production monitoring, automated
backups, SmartScheduling migration, execution gateways, or project/resource restrictions.
