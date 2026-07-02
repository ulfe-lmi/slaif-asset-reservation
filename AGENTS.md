# AGENTS.md

## Mission

This repository implements **SLAIF Asset Reservation**, an authenticated reservation authority for shared laboratory assets. The initial domain is compute infrastructure: machines, GPUs, and related reservable devices. Human users and authenticated software agents must use the same scheduling rules and the same reservation records.

Preserve this promise:

> A reservation accepted by the system is authoritative, auditable, policy-compliant, and conflict-free for the reserved asset and time range.

## Current product stage

The project has completed alpha verification and is now in the internal-alpha deployment rehearsal
and pilot-readiness gate. The rehearsal uses synthetic disposable resources only. The system remains
not production-ready and has not been deployed.
Read these documents before changing behavior:

- `docs/discovery-brief.md`
- `docs/architecture.md`
- `docs/domain-model.md`
- `docs/api-contract.md`
- `docs/security-model.md`
- `docs/testing-strategy.md`
- relevant ADRs under `docs/decisions/`
- the GitHub issue or work order assigned to the current PR

The live repository and accepted ADRs are authoritative. If the work order disagrees with current `main`, report the discrepancy before making an architectural assumption.

## Product boundaries

### In scope for the first release

- authenticated human users;
- scoped API-token access for agents;
- hierarchical inventory of machines and reservable child assets;
- exclusive time-range reservations;
- availability discovery;
- reservation creation, cancellation, and early release;
- policies such as horizon, duration, concurrency, and group access;
- append-only audit events;
- administrator workflows;
- PostgreSQL-backed conflict enforcement;
- deployment on a Linux server behind HTTPS.

### Explicit non-goals unless a work order says otherwise

- starting jobs, SSH sessions, containers, or GPU processes;
- replacing Slurm, Kubernetes, or other workload schedulers;
- controlling machine power state;
- billing or payment processing;
- a general multi-tenant SaaS product;
- a heavy single-page application;
- Redis, Celery, message brokers, or microservices in the initial architecture;
- importing private legacy client data without an approved migration plan;
- reproducing SmartScheduling's salon concepts such as staff, services, or phone-first clients.

## Accepted technical baseline

- Python 3.13.
- Django 5.2 LTS.
- Django REST Framework 3.16.
- PostgreSQL 17 or a later explicitly approved supported major version.
- `uv` for environment and dependency locking; commit `uv.lock`.
- Server-rendered Django templates, progressively enhanced where useful; HTMX may be added by an approved UI work order.
- OpenAPI generated from the implemented API; do not maintain a contradictory hand-written schema.
- Docker Compose for repeatable development and small-server deployment, unless an ADR replaces it.

Do not substitute Flask, FastAPI, a JavaScript SPA, SQLite production storage, or a microservice architecture without an accepted ADR.

## Expected code organization

Once the application scaffold exists, prefer this shape unless an accepted ADR changes it:

```text
src/slaif_reservation/
  config/          Django settings, URLs, ASGI/WSGI
  accounts/        custom user model, memberships, API tokens
  assets/          machines, assets, tags, availability rules
  reservations/    policies, reservations, conflict logic
  audit/           append-only audit events
  api/             versioned REST API and OpenAPI integration
  web/             shared human-facing views, forms, and templates
```

Keep scheduling and policy logic out of views and serializers. Put business operations in explicit service functions or domain modules that both the web UI and API call.

## Non-negotiable domain invariants

1. **One reservation engine.** Human UI, admin workflows, and agent API must call the same domain operations. Do not implement parallel scheduling logic.
2. **Opaque stable IDs.** Use UUIDs for public objects. Never infer a machine, GPU index, or capability from a legacy identifier suffix or display name.
3. **Time semantics.** Store aware timestamps in UTC. Render in the user's selected timezone, defaulting to `Europe/Ljubljana`. Reservation intervals are half-open: `[start_at, end_at)`, so adjacent reservations may touch but not overlap.
4. **Database-enforced exclusivity.** For exclusive assets, active blocking reservations must be protected by a PostgreSQL exclusion constraint or an equivalent accepted database invariant. Application-only overlap checks are insufficient.
5. **Fail closed.** Unknown permissions, inactive assets, unsupported booking modes, malformed ranges, and unresolved policy must reject the request before mutation.
6. **No booking in the past.** Ordinary users and agents cannot create or move reservations into past time. Any exceptional administrative correction must be explicit and audited.
7. **Auditable mutation.** Reservation creation, cancellation, release, policy changes, asset changes, and token lifecycle actions create audit events in the same transaction where practical.
8. **Immutable history.** Do not delete reservations or audit events as a normal workflow. Use state transitions and audit records.
9. **Idempotent agent mutations.** API creation requests must support an idempotency key scoped to the authenticated principal. Retrying the same request must not create duplicate reservations.
10. **Least privilege.** A user or token sees and changes only resources allowed by effective policy and scope.
11. **Data minimization.** The core product needs identity and contact email, not phone numbers. Do not copy legacy client or appointment data into fixtures, tests, logs, or docs.
12. **Reservation is not execution.** The core service grants entitlement. Any future machine gateway must verify a reservation through a separate, authenticated interface.

## Authentication and token rules

- Define a custom Django user model before the first production migration.
- Human browser access uses secure Django sessions and CSRF protection.
- Agent access uses separately revocable, expiring, scoped API tokens.
- Show a newly created token once. Store only an HMAC-derived verifier or another reviewed one-way representation, never the bearer token itself.
- Token verification uses a server-side secret distinct from Django's `SECRET_KEY`.
- Logs, exceptions, audit metadata, tests, screenshots, and PR descriptions must not contain bearer tokens, session cookies, passwords, private keys, or real personal records.
- Authorization must be checked at object and action level; authentication alone is not authorization.

## Reservation mutation rules

- Perform policy evaluation and reservation creation in a database transaction.
- Treat the database constraint as the final arbiter of a race. Convert a constraint conflict into a stable HTTP `409` response; do not expose database internals.
- Prefer cancel-and-recreate over silently rewriting reservation history.
- Distinguish cancellation before start from early release after start.
- A release must make the remaining future interval available without erasing the historical record.
- Every API mutation must return or expose a correlation identifier.

## Dependency policy

- Add no production dependency merely for convenience.
- A new production dependency must be allowed by the work order or justified in the PR with maintenance, security, licensing, and operational impact.
- Prefer standard Django/PostgreSQL capabilities over custom infrastructure.
- Install needed tools inside the Codex execution environment. Do not ask the human to perform routine package, browser, database, or formatter setup.
- Pin through `pyproject.toml` constraints and commit the generated `uv.lock`.

## Development workflow

1. Read this file and the assigned issue/work order.
2. Verify the current default branch, working tree, open PR context, and relevant docs.
3. Start from current `main` unless the work order explicitly names an existing repair branch.
4. Create one branch for one work order, normally `codex/<issue-number>-<short-name>`.
5. Keep the diff within scope. Do not opportunistically implement neighboring roadmap items.
6. Do not commit operating-system metadata or archive/download sidecars such as `*:Zone.Identifier`.
7. Commit only related files with a clear message.
8. Push the branch and open a pull request linked to the work-order issue.
9. Do not merge, self-approve, bypass branch protection, alter repository secrets, or modify production infrastructure.
10. Repair review findings on the same PR branch unless the strategic review explicitly requests a separate PR.

If a task requires an architectural, security, privacy, or data-migration decision not covered by accepted docs, stop before implementing the assumption. Report the decision needed and propose an ADR.

## Testing and verification

After the scaffold PR establishes commands, the standard evidence set is expected to include:

```bash
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py check
uv run pytest
```

Run focused tests while developing, then the relevant full suite before opening the PR. Database behavior that depends on PostgreSQL, including exclusion constraints and races, must be tested against PostgreSQL; SQLite is not acceptable evidence for those invariants.

Tests must cover dangerous negative paths, including:

- overlapping reservation rejection;
- back-to-back reservation acceptance;
- concurrent creation races;
- inactive or unauthorized asset rejection;
- token scope and expiry;
- idempotent retry behavior;
- cancellation/release authorization;
- timezone and daylight-saving boundaries;
- secrets absent from logs and API responses.

A skipped test is not a passing test. Report passed, failed, skipped, not run, and environment-blocked results separately.

## Migrations and data

- Review every migration; do not accept accidental migrations.
- Never edit an applied migration on a shared branch. Add a new migration.
- Avoid irreversible data migrations unless the work order includes backup and rollback evidence.
- Legacy SmartScheduling IDs may be stored as migration provenance, not used as primary keys.
- Bootstrap inventory is sanitized and incomplete. Do not invent hostnames, CUDA indices, GPU UUIDs, owners, or online state. Require administrator verification.

## Documentation contract

Update docs in the same PR when behavior, API, configuration, deployment, security posture, or limitations change.

- New architectural decisions require an ADR.
- New API behavior requires generated-schema tests and `docs/api-contract.md` updates if the design contract changes.
- New environment variables require `.env.example` and deployment documentation changes.
- User-visible behavior requires human UI documentation or release notes as appropriate.
- Never call the project production-ready until the release gates in `docs/deployment.md` and `docs/roadmap.md` are evidenced and accepted by a human maintainer.

## Pull request report

The PR description must contain:

```markdown
## Goal

## Scope implemented

## Files changed

## Verification
- command: exact result

## Database and migrations

## Security and privacy impact

## Documentation impact

## Known limitations / not run

## Agent report
- Branch:
- Commit:
- Work-order issue:
- Local tools or dependencies installed:
```

Use the repository PR template. Claims must point to tests, CI, migrations, or concrete files.

## Definition of done

A task is done only when:

- acceptance criteria are met;
- scope and non-goals were respected;
- relevant tests pass with exact evidence;
- migration state is intentional;
- security/privacy implications are addressed;
- documentation is synchronized;
- the branch and PR exist;
- remaining limitations are stated honestly;
- no production system or secret was touched;
- a human maintainer retains merge authority.
