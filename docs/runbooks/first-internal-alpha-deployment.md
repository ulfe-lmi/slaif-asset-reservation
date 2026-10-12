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

Follow [INSTALL's required steps](../../INSTALL.md#installation--required-steps)
in order. The first-install default fetches current `origin/main`, checks it out
detached and records the full SHA. Existing installations retain their project
name and volume and use INSTALL's upgrade section instead.

Database initialization is required. HTTPS proxy configuration and administrator
login verification complete the installation. Readiness, backup/recovery and
routine operations are post-installation responsibilities; use the referenced
runbooks for those procedures.

## Not Covered

This runbook does not configure OIDC, email, notifications, production monitoring, automated
backups, SmartScheduling migration, execution gateways, or project/resource restrictions.
