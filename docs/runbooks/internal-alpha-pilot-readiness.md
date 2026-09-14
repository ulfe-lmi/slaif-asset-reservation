# Runbook: Internal-Alpha Pilot Readiness

This checklist is a rehearsal gate for a future internal lab pilot. It is not a production
deployment, and it does not authorize real DNS, TLS certificates, production secrets, production
data, or a SmartScheduling cutover.

## Scope

Use this runbook after CI is green on the intended commit and before a human operator attempts an
internal-alpha deployment. The rehearsal uses only synthetic local secrets and disposable database
state.

Use `docs/runbooks/internal-alpha-pilot-preparation.md` as the companion planning pack for pilot
asset selection, operator checklists, placeholder-only communication templates, and participant
limitations. This readiness gate remains the pass/fail rehearsal checklist.

## Required Pass Gates

- Main CI is green for the reviewed commit.
- `deploy/rehearse_internal_alpha_deployment.sh` completes successfully.
- A fresh migration chain applies to disposable PostgreSQL.
- `operational_check` passes in the rehearsed environment.
- `pilot_readiness_check --strict` passes against the intended pilot database state after pilot
  assets, staff accounts, users, and policies are configured.
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
- `pilot_readiness_check --strict` fails after the pilot database has been prepared.
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
services, runs smoke checks against the configured `SLAIF_REHEARSAL_PORT`, then removes the
temporary files and Compose volume.

For a quick Compose-only validation:

```bash
deploy/rehearse_internal_alpha_deployment.sh --config-only
```

## Rehearsal Residue And Port Recovery

A rehearsal run that is killed or lost (for example SIGKILL, a crash, or power loss) can leave
its disposable Compose project behind, named `slaif-alpha-rehearsal-<pid>`, including a live app
container that keeps the rehearsal host port (default 18080) bound. The next full rehearsal
refuses to start while such rehearsal-owned residue exists and prints the recovery command; it
never removes residue automatically.

Check what residue exists (read-only; never mutates Docker state):

```bash
deploy/rehearse_internal_alpha_deployment.sh --status
```

Remove only rehearsal-owned projects, scoped by the `slaif-alpha-rehearsal-` project-label
prefix; foreign projects and processes are never touched:

```bash
deploy/rehearse_internal_alpha_deployment.sh --cleanup-owned
```

If the configured `SLAIF_REHEARSAL_PORT` is occupied by a non-rehearsal process, the rehearsal
refuses to start and reports it; choose another `SLAIF_REHEARSAL_PORT`. The script never kills
port occupants automatically.

## Database Readiness Command

After preparing a disposable or intended pilot database, run the read-only readiness status command:

```bash
python manage.py pilot_readiness_check
python manage.py pilot_readiness_check --strict
python manage.py pilot_readiness_check --json
```

The command reports aggregate counts and pass/warn/fail checks for staff users, ordinary pilot
users, active assets, reservable exclusive assets, reservation policies, assets without effective
policy, active blackouts, recent audit events, API-token status counts, expired idempotency rows,
and database migration readiness. It is read-only and must not print token material, private
reservation text, physical locators, cookies, CSRF values, or private SmartScheduling data.

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
