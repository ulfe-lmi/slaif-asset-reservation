# SLAIF Asset Reservation

A professional reservation authority for shared laboratory assets, designed for both authenticated humans and authenticated software agents.

The initial deployment targets scattered Linux compute machines and their GPUs. The domain model remains asset-oriented so that other exclusive laboratory resources can be added without recreating the legacy appointment-salon abstraction.

## Status

**Pre-alpha executable foundation. Not production-ready and not yet a reservation system.**

The repository contains a minimal Django/PostgreSQL application scaffold: custom user model,
health checks, an empty `/api/v1/` namespace, generated OpenAPI support with local Swagger UI
assets, CI, and container configuration. Asset, reservation, policy, audit, API-token, and UI
workflows are deliberately not implemented yet.

Verified starting point for this implementation slice:

```text
main SHA before Work Order 0001: 5cf7fbc46c7d45e966215ebf07a81e8722b8a572
```

## Product promise

A reservation accepted by the system is:

- conflict-free for its asset and time range;
- evaluated under the same policy for web and API clients;
- attributable to an authenticated principal;
- auditable;
- revocable or releasable through explicit state transitions.

## Intended clients

- **Humans:** browser-based resource discovery, availability, reservation, cancellation, and administration.
- **Agents:** versioned REST API with scoped, expiring tokens; idempotent mutations; stable machine-readable errors.
- **Future execution gateways:** deterministic services that verify reservation entitlement before using a machine or accelerator. Workload execution is deliberately outside the core application.

## Chosen shape

- Django 5.2 LTS monolith
- Django REST Framework 3.16
- PostgreSQL 17
- server-rendered UI, progressively enhanced
- OpenAPI-described `/api/v1/`
- Docker Compose deployment on an external Linux server behind HTTPS

## Development Quickstart

Prerequisites:

- Python 3.13 managed by `uv`
- Docker with Compose v2

Start PostgreSQL and install dependencies:

```bash
docker compose up -d db
uv sync --locked --all-groups
```

The committed Compose file is for development only. It publishes PostgreSQL and the application
only on `127.0.0.1`; app-to-database traffic inside Compose still uses the internal `db` hostname.

For host-side commands, copy the example environment and pass it explicitly to `uv run`. Django
does not automatically load `.env` files.

```bash
cp .env.example .env
```

Run migrations and local checks:

```bash
uv run --env-file .env python manage.py migrate
uv run --env-file .env python manage.py check
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test
```

Run the local application:

```bash
uv run --env-file .env python manage.py runserver
```

Health endpoints:

```bash
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready
```

Generate and validate the current OpenAPI shell:

```bash
mkdir -p build/openapi
uv run --env-file .env python manage.py spectacular --file build/openapi/schema.yaml --validate --fail-on-warn
```

Run the full scaffold evidence set:

```bash
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
DATABASE_URL=postgres://slaif:slaif@localhost:5432/slaif_reservation uv run python manage.py check
DATABASE_URL=postgres://slaif:slaif@localhost:5432/slaif_reservation uv run python manage.py makemigrations --check --dry-run
DATABASE_URL=postgres://slaif:slaif@localhost:5432/slaif_reservation TEST_DATABASE_URL=postgres://slaif:slaif@localhost:5432/slaif_reservation uv run pytest
uv run pip-audit
docker compose config
docker build --tag slaif-asset-reservation:local .
test "$(docker image inspect slaif-asset-reservation:local --format '{{.Config.User}}')" = "10001:10001"
```

## Configuration

`.env.example` documents host-side local placeholders for `uv run --env-file .env ...`.
Do not commit a real `.env`. Compose does not load this file into the application service; it
sets its own container-internal `DATABASE_URL` that uses hostname `db`.

Current environment variables:

- `DJANGO_SETTINGS_MODULE`: selects `local`, `test`, or `production` settings.
- `DATABASE_URL`: PostgreSQL connection URL. SQLite is not the normal development or CI path.
- `TEST_DATABASE_URL`: optional PostgreSQL URL for pytest.
- `SLAIF_DJANGO_SECRET_KEY`: required by production settings.
- `SLAIF_DEBUG`: parsed strictly; values such as `false` and `0` disable debug.
- `SLAIF_ALLOWED_HOSTS`: comma-separated host allowlist.
- `SLAIF_CSRF_TRUSTED_ORIGINS`: comma-separated CSRF trusted origins.
- `SLAIF_ENABLE_API_DOCS`: exposes schema/docs routes when explicitly enabled.
- `SLAIF_PUBLIC_API_DOCS`: allows anonymous docs only in non-production settings. Production
  always forces private docs when docs routes are enabled.
- `SLAIF_SECURE_SSL_REDIRECT`, `SLAIF_SECURE_HSTS_SECONDS`,
  `SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SLAIF_SECURE_HSTS_PRELOAD`: production-shaped
  HTTPS controls. HSTS defaults to disabled until HTTPS is verified, then must be enabled
  explicitly.

## Production Dependencies

- `Django`: web framework, authentication, admin, ORM, migrations, sessions, CSRF, and settings.
- `djangorestframework`: versioned API foundation for later agent endpoints.
- `drf-spectacular`: generated OpenAPI schema from implemented DRF views.
- `drf-spectacular-sidecar`: local Swagger UI CSS, JavaScript, and favicon assets so API
  documentation does not depend on an unpinned CDN resource.
- `psycopg[binary]`: PostgreSQL driver for Django and health/readiness checks.
- `gunicorn`: production WSGI process runner used by the container image.
- `whitenoise`: conservative static-file middleware for the monolith deployment shape.

See:

- [Discovery brief](docs/discovery-brief.md)
- [Architecture](docs/architecture.md)
- [Domain model](docs/domain-model.md)
- [API contract](docs/api-contract.md)
- [Human UI requirements](docs/human-ui.md)
- [Security model](docs/security-model.md)
- [OAP/Codex workflow](docs/oap-workflow.md)
- [Roadmap](docs/roadmap.md)

## Repository workflow

All implementation is performed through issue-scoped pull requests. Codex reads `AGENTS.md`, implements one approved work order, runs verification, opens a PR, and does not merge it. The strategic model reviews evidence and prepares a decision brief; a human maintainer decides whether to merge.

## Legacy system

The current scheduler repurposes SmartScheduling employees as GPUs and services as fixed reservation durations. Its sanitized resource inventory is retained in `data/bootstrap/assets.yaml` only as migration input. The new application does not preserve salon-specific concepts.

## License

Apache License 2.0. See `LICENSE`.
