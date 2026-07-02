# Runbook: Internal-Alpha Pilot Readiness

This checklist is a rehearsal gate for a future internal lab pilot. It is not a production
deployment, and it does not authorize real DNS, TLS certificates, production secrets, production
data, or a SmartScheduling cutover.

## Scope

Use this runbook after CI is green on the intended commit and before a human operator attempts an
internal-alpha deployment. The rehearsal uses only synthetic local secrets and disposable database
state.

## Required Pass Gates

- Main CI is green for the reviewed commit.
- `deploy/rehearse_internal_alpha_deployment.sh` completes successfully.
- A fresh migration chain applies to disposable PostgreSQL.
- `operational_check` passes in the rehearsed environment.
- The production-shaped Compose example renders with a temporary ignored `deploy/env.production`.
- Docker image runtime user is `10001:10001`.
- Required static assets and sanitized bootstrap assets are present in the image.
- Sanitized bootstrap asset import dry-run succeeds.
- `/health/live` and `/health/ready` return HTTP 200.
- `/login/` returns HTTP 200.
- Anonymous `/manage/` access redirects safely to authentication.
- Unauthenticated `/api/v1/me/` returns safe HTTP 401 problem details.
- OpenAPI generation validates with `--fail-on-warn`.
- Backup and restore wrapper refusal/dry-run behavior is understood.
- A first staff account creation plan is assigned to a human operator.
- Bootstrap assets have an owner for hardware verification.
- Initial reservation policies will be configured through the staff management UI.
- Local API-token issuance has been tested with fake/local token material only.
- Staff management access, blackout creation/deactivation process, and audit export have been
  rehearsed with synthetic data.
- Rollback and restore posture has been reviewed before any real migration or deployment.

## No-Go Conditions

- Real production secrets are missing, unapproved, or stored in the repository.
- The rehearsal script fails.
- Migrations fail or `operational_check` fails.
- Backup/restore refusal or dry-run behavior is not understood.
- A blocker, high, or medium verification finding remains unresolved.
- Asset or policy ownership is unclear.
- No human operator is assigned for the pilot.
- DNS, TLS, certificates, or production host ownership is unsettled.
- A private SmartScheduling export is required to prove readiness.

## Rehearsal Command

```bash
deploy/rehearse_internal_alpha_deployment.sh
```

The script creates temporary ignored deployment files with synthetic values, uses
`compose.production.example.yaml`, builds the runtime image, starts disposable PostgreSQL and app
services, runs smoke checks, then removes the temporary files and Compose volume.

For a quick Compose-only validation:

```bash
deploy/rehearse_internal_alpha_deployment.sh --config-only
```

## Backup And Restore Drill

The rehearsal script does not perform a destructive restore. Before a real pilot, an operator must
run the backup and restore wrappers against an isolated disposable database and confirm that
passwords are not printed:

```bash
python manage.py backup_database --output /tmp/slaif-alpha-rehearsal.dump
python manage.py restore_database --input /tmp/slaif-alpha-rehearsal.dump
```

Use `--apply` only against an approved disposable target during a restore drill. A backup without a
successful isolated restore drill is not release evidence.

## Explicitly Outside This Gate

- No real production deployment or cutover.
- No production DNS, TLS, certificates, or secret-store integration.
- No real SmartScheduling import or cutover.
- No monitoring stack, backup scheduler, OIDC, email, notifications, execution gateway, API
  throttling implementation, projects, memberships, or resource restrictions.
