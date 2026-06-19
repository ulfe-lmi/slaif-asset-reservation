# Work Order 0001: Executable Django/PostgreSQL Foundation

Copy this into a GitHub work-order issue after the bootstrap PR is merged and current repository state is verified.

## Governing instructions

- Repository: `ulfe-lmi/slaif-asset-reservation`.
- Read root `AGENTS.md` first.
- Read accepted architecture and ADRs.
- If live repository state differs from this work order, report the difference in the issue/PR; do not silently invent a reconciliation.

## Current verified state

Expected after bootstrap:

- constitution, architecture docs, ADRs, templates, and sanitized inventory exist;
- no executable Django application, dependency lock, CI, Dockerfile, or database migration exists;
- `main` is clean and protected or protection is being configured.

Update this section with the actual `main` SHA before assigning the issue.

## Goal

Create a minimal, production-shaped, fully testable Django/PostgreSQL project foundation that later PRs can extend without replacing authentication, packaging, settings, or CI.

This PR establishes executable infrastructure only. It must leave `main` green and honestly described as pre-alpha.

## Domain behavior

- Define the custom user model before the first application migration.
- Do not implement assets, reservations, policies, API tokens, audit events, or SmartScheduling import yet.
- Expose only health endpoints and an OpenAPI-capable API shell.
- No user data or production secrets.

## Scope

Create and verify:

1. Python 3.13 project managed by `uv`.
2. Django 5.2 LTS and Django REST Framework 3.16 dependency baseline.
3. PostgreSQL 17 development/test service.
4. Django project under `src/slaif_reservation/`.
5. Minimal `accounts` app with custom UUID user model suitable for email-based identity.
6. Settings for local/test/production-shaped configuration with environment validation.
7. Root URL configuration.
8. `/health/live` and `/health/ready`.
9. DRF and generated OpenAPI shell, with schema and documentation endpoints protected/configured appropriately.
10. Initial migrations.
11. pytest/pytest-django, Ruff, mypy with Django support, coverage, and dependency-audit tooling.
12. Dockerfile and development `compose.yaml` or equivalent accepted Compose layout.
13. `.env.example`, `.dockerignore`, `.python-version`, `pyproject.toml`, and committed `uv.lock`.
14. GitHub Actions CI with uniquely named `quality`, `test`, `security`, and `container` jobs, or a documented smaller set if one job is not yet meaningful.
15. README/development/deployment documentation updated with exact commands.

## Non-goals

- No asset or reservation models.
- No booking UI or calendar.
- No API-token implementation.
- No OIDC.
- No HTMX/CSS/calendar dependency.
- No Redis, Celery, task queue, microservices, Kubernetes, Terraform, or production deployment.
- No import of bootstrap assets.
- No SmartScheduling network call.
- No production DNS/TLS assumption.
- No real email sending.
- No broad repository restructuring beyond this scaffold.

## Acceptance criteria

### Packaging and runtime

- `uv sync --locked --all-groups` succeeds in a clean environment.
- Python requirement is explicit and compatible with Python 3.13.
- dependency ranges follow the accepted baseline; lockfile is committed.
- development startup and test commands are documented.

### Django

- custom user model is configured before initial app migrations and uses UUID identity;
- `python manage.py check` succeeds;
- `makemigrations --check --dry-run` reports no drift after committed migrations;
- local/test configuration defaults are safe and production configuration fails fast when required secrets/hosts/database settings are missing;
- `DEBUG` is not accidentally enabled by a truthy string parser bug.

### Health

- liveness returns success without requiring database access;
- readiness checks database connectivity and returns failure without exposing connection details;
- tests cover both paths.

### API/OpenAPI

- `/api/v1/` namespace exists without implementing domain endpoints;
- OpenAPI schema generation succeeds;
- API docs exposure is explicit and does not weaken production authorization;
- schema test prevents accidental generation failure.

### PostgreSQL

- development/test path uses PostgreSQL 17;
- CI applies migrations to a fresh PostgreSQL database;
- no SQLite fallback is presented as the normal environment.

### Containers

- image builds;
- application runs as non-root in the image;
- development Compose can start PostgreSQL and the app or clearly separates app command while remaining reproducible;
- production secrets are not baked into image;
- migrations are not hidden as an unsafe side effect in every worker startup.

### Quality and tests

- Ruff lint and format check pass;
- mypy passes for scaffold code under the configured scope;
- pytest passes with coverage reported;
- dependency audit runs; any upstream advisory is reported, not silently ignored;
- CI is green on the PR.

### Documentation and security

- README retains pre-alpha language;
- environment variables are documented with placeholders;
- no credentials, tokens, cookies, personal data, or private legacy export are committed;
- security-sensitive Django production checks are documented and, where possible, tested;
- new production dependencies are justified in the PR.

## Files/areas to inspect

- `AGENTS.md`
- `README.md`
- `docs/discovery-brief.md`
- `docs/architecture.md`
- `docs/domain-model.md`
- `docs/security-model.md`
- `docs/testing-strategy.md`
- `docs/deployment.md`
- `docs/decisions/0001-django-modular-monolith.md`
- `docs/decisions/0002-postgresql-reservation-integrity.md`
- existing `.gitignore` and `LICENSE`

## Implementation guidance

Preferred shape:

```text
manage.py
pyproject.toml
uv.lock
.python-version
.env.example
.dockerignore
Dockerfile
compose.yaml
src/slaif_reservation/
  __init__.py
  config/
    settings/
    urls.py
    asgi.py
    wsgi.py
  accounts/
  api/
  web/
tests/
.github/workflows/ci.yml
```

Use conservative production dependencies. A reasonable starting set is Django, DRF, psycopg 3, an OpenAPI generator compatible with DRF, Gunicorn, and a reviewed static-file solution. Use standard library environment parsing or one justified configuration helper; do not accumulate overlapping settings packages.

The exact latest compatible patch versions must be resolved and locked during the PR. Do not switch to Django 6 solely because it is newer; the accepted baseline is the 5.2 LTS line.

## Tests required

At minimum:

- application imports/boots;
- custom user creation and unique email behavior;
- liveness success independent of DB;
- readiness success/failure;
- settings parsing and production fail-fast behavior;
- API root/schema generation;
- migrations apply to empty PostgreSQL;
- no migration drift;
- container build smoke.

Run and report exact output for:

```bash
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest
```

Also run the documented Docker/Compose and OpenAPI generation checks.

## Documentation required

Update:

- `README.md` quickstart and accurate status;
- `docs/deployment.md` with implemented development commands and remaining production gaps;
- `docs/testing-strategy.md` only if actual commands/tool choices differ;
- `docs/project-handoff.md` to record merged executable state, preferably in this PR if the content is factual and concise;
- add an ADR only if deviating from accepted stack/structure.

## Local setup allowed

Codex may install `uv`, Docker/Compose dependencies, PostgreSQL clients, build tools, and testing tools inside its execution environment. Document material setup. Do not ask the human to run routine setup commands.

No production credentials or external SmartScheduling access is permitted.

## Workflow

- start from current `main`;
- create `codex/<issue-number>-application-scaffold`;
- commit only scoped files;
- push and open one PR linked with `Closes #<issue>`;
- fill the PR template with exact evidence;
- do not merge;
- repair CI/review findings on the same branch unless strategic review changes the scope.

## Final report

Include:

- branch, commit, PR URL, issue;
- dependency versions and why each production dependency exists;
- files/modules created;
- exact test/check commands and pass/fail/skip counts;
- Docker/Compose evidence;
- migrations created;
- environment tools installed;
- security/privacy confirmation;
- known limitations and checks not run;
- any decision that needs strategic/human review.
