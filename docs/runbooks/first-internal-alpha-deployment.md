# Runbook: First Authenticated HTTPS Deployment

This runbook is an operator checklist for an authenticated HTTPS service host. It is not evidence that a
production deployment has happened.

## Preconditions

- Linux host with Docker and Compose v2.
- DNS name and TLS plan selected.
- Protected secret store or host-only secret files prepared.
- PostgreSQL storage and backup destination selected.
- Human maintainer approval for the release commit.
- `deploy/rehearse_internal_alpha_deployment.sh` passed locally or in an equivalent staging
  rehearsal with synthetic disposable values.
- `docs/runbooks/internal-alpha-pilot-readiness.md` pass/no-go gates were reviewed.

## Steps

The complete, verified command procedure is owned by `INSTALL.md`, section 5
("Authenticated pilot Docker deployment"). In summary, the operator must:

Record the Compose project name first: new services use `slaif-asset-reservation`;
existing installations retain their actual project name and database volume. Use
INSTALL's explicit `-p` commands throughout. Do not import the demo on upgrades.

1. Build the reviewed image at the reviewed commit (example tag
   `slaif-asset-reservation:pilot`, plus a commit-addressable tag for rollback).
2. Prepare `deploy/env.production` from `deploy/env.production.example` with real values from a
   protected secret store. Never commit `deploy/env.production`.
3. Store the PostgreSQL password in `deploy/secrets/postgres_password`, matching the
   `DATABASE_URL` password in `deploy/env.production`.
4. Review `compose.production.example.yaml`; do not publish PostgreSQL publicly.
5. Start PostgreSQL, then run migrations and `operational_check` deliberately (see `INSTALL.md`
   section 5, steps 6–8).
6. Configure initial assets and policies, and create the first administrator (see `INSTALL.md`
   section 5, steps 9–10).
7. Start the application and verify `/health/live`, `/health/ready`, `/login/`, `/manage/`, and a
   safe unauthenticated API failure (see `INSTALL.md` section 5, steps 11–16).
8. Configure Caddy or another reverse proxy for HTTPS from `deploy/Caddyfile.example` (it
   forwards to the loopback application port), then verify HTTPS end to end.
9. Once the pilot database is prepared, run `pilot_readiness_check --strict` (see `INSTALL.md`
   section 5, step 17).

## Not Covered

This runbook does not configure OIDC, email, notifications, production monitoring, automated
backups, SmartScheduling migration, execution gateways, or project/resource restrictions.
