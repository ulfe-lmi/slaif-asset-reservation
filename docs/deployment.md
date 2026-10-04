# Deployment and Operations

**Status:** CI-green, production-shaped internal-alpha candidate; a real deployment has not yet
been evidenced

## 1. Target

A maintained Linux server hosts the reservation application outside individual compute machines. It is reachable over HTTPS by authorized humans and agents. The initial workload is small enough for one web service and one PostgreSQL instance.

## 2. Service layout

```text
reverse proxy (Caddy or Nginx)
  -> Django/Gunicorn application
  -> PostgreSQL 17 on a private network

systemd timer or cron
  -> idempotent Django management commands
```

Do not run PostgreSQL on a public interface. Do not colocate production secrets in the repository or image.

## 3. Development environment

Work Order 0001 provides a repeatable development path using:

- Python 3.13 managed by `uv`;
- committed `uv.lock`;
- PostgreSQL 17 through Docker Compose;
- synthetic test data only;
- documented commands for migrations, checks, tests, OpenAPI validation, and container smoke.

No developer should need SmartScheduling credentials or production data.

The committed Compose file is development-only. It publishes PostgreSQL and the application on
`127.0.0.1` only, while keeping app-to-database communication on the internal Compose network.

The complete development installation procedure (database, locked dependencies, env file,
migrations, bootstrap import, runserver, superuser, health checks) is owned by `INSTALL.md`,
sections 3 and 4. The standard verification command set for changes is in `TESTING.md`.

Migrations are a deliberate command. They are not hidden inside the application worker startup.

Work Order 0003 adds PostgreSQL-specific reservation migrations. The migration chain installs the
`btree_gist` extension with `BtreeGistExtension()` and creates the
`reservation_no_overlap_per_asset` exclusion constraint. The deployment/migration role must be
allowed to create this extension, or an operator must preinstall it in the target database before
running migrations.

Work Order 0007 adds maintenance-blackout tables and audit action constraints. No background cleanup
or notification scheduler is introduced; blackout creation/deactivation is synchronous through the
staff management UI.

Work Order 0008 adds example-only production deployment artifacts:

- `compose.production.example.yaml`;
- `deploy/env.production.example`;
- `deploy/Caddyfile.example`;
- operator runbooks under `docs/runbooks/`.

These files describe the supported first internal-alpha shape but are not a real deployment. The
development Compose file remains unchanged and loopback-only.

Work Order 0011 adds the disposable internal-alpha rehearsal entry point
`deploy/rehearse_internal_alpha_deployment.sh`. The script creates temporary ignored
`deploy/env.production` and `deploy/secrets/postgres_password` files with synthetic values,
validates `compose.production.example.yaml`, builds the runtime image, applies migrations to
disposable PostgreSQL, runs bootstrap/import and operational checks, starts the app, verifies
health/login/management/API smoke paths, validates OpenAPI, then removes the temporary
env/secret files and Compose volume. It is local rehearsal evidence only, not a production
deployment. Its full behavior, modes (`--config-only`, `--status`, `--cleanup-owned`), and
evidence boundaries are documented in `INSTALL.md`, section 6.

Work Order 0004 adds local browser workflow tests. Development and CI install Chromium with:

```bash
uv run playwright install --with-deps chromium
```

The installed browser/runtime packages are development/test tooling only and are not production
application dependencies.

## 4. Configuration

Implemented variables:

- `DJANGO_SETTINGS_MODULE`;
- `DATABASE_URL`;
- `TEST_DATABASE_URL`;
- `SLAIF_DJANGO_SECRET_KEY`;
- `SLAIF_DEBUG`;
- `SLAIF_ALLOWED_HOSTS`;
- `SLAIF_CSRF_TRUSTED_ORIGINS`;
- `SLAIF_ENABLE_API_DOCS`;
- `SLAIF_PUBLIC_API_DOCS`;
- `SLAIF_SECURE_SSL_REDIRECT`;
- `SLAIF_SECURE_HSTS_SECONDS`;
- `SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS`;
- `SLAIF_SECURE_HSTS_PRELOAD`.
- `SLAIF_API_TOKEN_PEPPER`;
- `SLAIF_API_TOKEN_MAX_LIFETIME_DAYS`.

`SLAIF_SECURE_HSTS_SECONDS`, `SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS`, and
`SLAIF_SECURE_HSTS_PRELOAD` default to disabled in production settings. Enable them only after
the final HTTPS hostname, redirects, and subdomain ownership are verified. `SECURE_SSL_REDIRECT`
and secure session/CSRF cookies remain enabled by default in production settings.

`SLAIF_API_TOKEN_PEPPER` is required in production. Generate and store it as a protected deployment
secret outside the repository and image. It must be at least 32 UTF-8 bytes, distinct from
`SLAIF_DJANGO_SECRET_KEY`, and not the documented development placeholder. Replacing this single
pepper invalidates all existing API tokens until a future key-ring/rotation design is accepted.

`SLAIF_API_TOKEN_MAX_LIFETIME_DAYS` defaults to 90 and must be from 1 through 365.

Deferred variables:

- canonical external URL, email relay, structured-log destination, OIDC, and backup destination.
- login throttling/rate-limit configuration, because public local-auth hardening is deferred.

`.env.example` is for host-side local commands run explicitly as `uv run --env-file .env ...`;
Django does not automatically load it. Its `DATABASE_URL` points at the loopback-published
development database. Compose supplies the application service with its own container-internal
`DATABASE_URL` that uses hostname `db`. Never provide a production `.env`.

For production-shaped configuration, copy `deploy/env.production.example` on the deployment host and
replace every placeholder from a protected secret store into an untracked `deploy/env.production`
file. Never commit `deploy/env.production`. The production Compose example can render with
`docker compose -f compose.production.example.yaml config` before that file exists, but the
application cannot start successfully without the required runtime environment. Production settings
reject placeholder or too-short `SLAIF_DJANGO_SECRET_KEY` values and reject documented
development/test/example API-token peppers, including whitespace-padded forms.

`compose.production.example.yaml` publishes the app on loopback only. By default it binds
`127.0.0.1:8000`; set `SLAIF_APP_HOST_PORT` when rendering or running the example to choose a
different host port. The rehearsal script sets this variable from `SLAIF_REHEARSAL_PORT` so the
smoke checks probe only the configured rehearsal port.

## 5. Containers

The scaffold image:

- uses the Python 3.13 slim image;
- run as a non-root user;
- install only locked production dependencies;
- collects Django admin and drf-spectacular-sidecar static assets during image build;
- includes only the sanitized `data/bootstrap` inventory files needed by `operational_check`;
- exclude tests, caches, `.git`, local secrets, and development data;
- does not bake secrets into the image;
- expose no development server;
- emit logs to stdout/stderr.

Database migrations run as a deliberate release step, not unpredictably in every worker startup.

Build and inspect the runtime user:

```bash
docker build --tag slaif-asset-reservation:local .
docker image inspect slaif-asset-reservation:local --format '{{.Config.User}}'
docker run --rm --entrypoint test slaif-asset-reservation:local -f /app/staticfiles/admin/css/base.css
docker run --rm --entrypoint test slaif-asset-reservation:local -f /app/staticfiles/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js
docker run --rm --entrypoint test slaif-asset-reservation:local -f /app/data/bootstrap/assets.yaml
docker run --rm --entrypoint test slaif-asset-reservation:local -f /app/data/bootstrap/assets.schema.json
```

The configured runtime user must be `10001:10001`.

### Production dependencies

- `Django`: web framework, authentication, admin, ORM, migrations, sessions, CSRF, and settings.
- `djangorestframework`: versioned API foundation for later agent endpoints.
- `drf-spectacular`: generated OpenAPI schema from implemented DRF views.
- `drf-spectacular-sidecar`: local Swagger UI CSS, JavaScript, and favicon assets so API
  documentation does not depend on an unpinned CDN resource.
- `jsonschema`: Draft 2020-12 validation for the sanitized bootstrap inventory schema.
- `psycopg[binary]`: PostgreSQL driver for Django and health/readiness checks.
- `PyYAML`: safe parsing for the sanitized bootstrap inventory import command.
- `gunicorn`: production WSGI process runner used by the container image.
- `whitenoise`: conservative static-file middleware for the monolith deployment shape.

Locked versions are recorded in `uv.lock`.

### Gunicorn worker pool

All three supported defaults (the `Dockerfile` `CMD`, the development
`compose.yaml` app command, and the production example
`compose.production.example.yaml` app command) run Gunicorn with the
`gthread` worker pool:

```text
gunicorn slaif_reservation.config.wsgi:application
  --bind 0.0.0.0:8000
  --workers 3
  --threads 8
  --keep-alive 5
  --timeout 30
```

- The legacy `sync` pool processes one request per worker, and a client
  that connects and sends nothing — or stalls part-way through the header
  block — blocks that worker in a socket read. Three such clients occupy
  all three workers, and new connections sit in the listen backlog until a
  blocker disconnects or the arbiter's worker timeout restarts a worker.
  That is the idle-connection starvation failure: new requests time out on
  the LAN while slow or idle clients merely hold connections.
- `gthread` accepts connections in a worker event loop and serves each
  request in a pool thread. Idle keep-alive connections wait in the event
  loop and are closed after the 5 s keep-alive; only a stalled header read
  occupies a thread. The baseline is 3 workers x 8 threads = 24 request
  slots: six slow clients can occupy one full worker's thread pool while
  the remaining workers and threads keep `/health/live` and ordinary page
  loads responsive, and the existing 3-worker process isolation is
  retained.
- `--timeout 30` keeps the standard arbiter worker timeout; the binds are
  unchanged (container-internal `0.0.0.0:8000`; the service is published
  on host loopback only).
- This is a responsiveness baseline for the supported reverse-proxied
  shape, not a load guarantee and not authorization to expose Gunicorn
  directly to the internet. The application stays reachable exclusively
  through the HTTPS reverse proxy (section 8), which must buffer client
  bodies and enforce its own read/idle timeouts; a slow-client flood is a
  proxy abuse-control concern, not something worker sizing solves.

Troubleshooting: if new requests queue while the service otherwise looks
up, suspect clients holding connections without completing requests
(idle or partial-header clients). The regression below reproduces the
starvation with the old `sync` configuration and proves the shipped
`gthread` defaults stay responsive:

```bash
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test \
  tests/test_gunicorn_responsiveness.py -v
```

The test launches the real installed Gunicorn with the real Django routes
on unique loopback ports (the anonymous `/health/live` and `/login/` GETs
need no database), pins the supported commands to the `gthread` baseline,
and shuts its children down even after failures.

## 6. Health endpoints

- `/health/live`: application process responds; no expensive dependencies.
- `/health/ready`: database reachable and migration state is current.

Health responses contain no secrets, build environment, database host, or dependency versions beyond an approved release identifier.

Local smoke:

```bash
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready
```

Deployment smoke command:

```bash
python manage.py operational_check
```

It verifies database connectivity, applied migrations, required static assets, critical settings,
sanitized bootstrap inventory validation, and idempotency cleanup command registration. It does not
require production secrets when run under local/test settings.

For a disposable production-shaped smoke run, use the rehearsal described in `INSTALL.md`,
section 6. The rehearsal uses production settings with synthetic local-only values and disables
SSL redirect because no real reverse proxy or TLS endpoint exists in this local check.

## 7. Database lifecycle

### Migrations

- run `migrate --plan` or equivalent review before production migration;
- back up before destructive/large migrations;
- use backward-compatible expand/contract patterns once zero-downtime matters;
- do not edit previously deployed migrations;
- record application release and migration state.

### Backup

Work Order 0008 adds PostgreSQL-native wrappers:

```bash
python manage.py backup_database --output /backups/slaif-YYYYMMDD.dump
python manage.py backup_database --output /backups/slaif-YYYYMMDD.dump --apply
python manage.py restore_database --input /backups/slaif-YYYYMMDD.dump
python manage.py restore_database --input /backups/slaif-YYYYMMDD.dump --apply
```

The default mode validates only. Apply mode uses `pg_dump` or `pg_restore`, requires
`DATABASE_URL`, writes or reads an explicit path, and avoids printing database passwords. Retention,
encryption, off-host copy, restore-drill cadence, and failure alerts remain operator policy.

A backup without a restore test into an isolated database is not release evidence.

The internal-alpha pilot readiness runbook documents the backup/restore rehearsal gate:

```text
docs/runbooks/internal-alpha-pilot-readiness.md
```

The pilot preparation pack documents the operator checklist and placeholder-only participant
communication templates for a future controlled internal lab pilot:

```text
docs/runbooks/internal-alpha-pilot-preparation.md
```

## 8. Reverse proxy and TLS

- valid certificate and automatic renewal;
- HTTP to HTTPS redirect;
- preserve validated client/proxy headers;
- request and upload limits;
- sensible timeouts;
- security headers coordinated with Django;
- API access logs redacted according to the security model;
- optional network restriction for `/admin/`.

Caddy is the documented first internal-alpha example in `deploy/Caddyfile.example`; Nginx remains
acceptable if already operated institutionally. The reverse proxy must terminate HTTPS, forward
`X-Forwarded-Proto`, enforce request-size/timeouts, preserve the configured host, and coordinate
with `SLAIF_ALLOWED_HOSTS`, `SLAIF_CSRF_TRUSTED_ORIGINS`, `SECURE_PROXY_SSL_HEADER`, secure cookies,
and HSTS. HSTS remains disabled until the final HTTPS host and subdomain ownership are verified.

## 9. Logging and monitoring

Minimum implemented application-side posture:

- production JSON logs to stdout/stderr with timestamp, level, logger, message, request path,
  method, status, duration, and request ID where available;
- defensive redaction of Authorization, bearer-token-shaped values, token secrets, verifiers,
  peppers, cookies, CSRF values, passwords, raw request bodies, reservation purposes, and
  cancellation reasons.

Remaining operator monitoring minimum:

- reverse-proxy logs with secrets/queries reviewed;
- health probe;
- service restart monitoring;
- PostgreSQL disk/connection/backup monitoring;
- alerts for sustained 5xx, failed readiness, backup failure, and disk pressure;
- reservation conflict metrics treated as product signal, not necessarily errors.

Prometheus/Grafana integration is optional until an operator requirement is confirmed.

## 10. Scheduled work

Use idempotent management commands for:

- cleanup of expired idempotency records:

  ```bash
  python manage.py purge_expired_idempotency_records
  python manage.py purge_expired_idempotency_records --apply
  ```

  The default mode is dry-run. Scheduling remains operator responsibility;
- notifications/reminders if approved;
- audit/consistency checks;
- export and backup verification helpers.

Every command supports dry-run where mutation risk exists and returns a non-zero exit status on failure. A queue system requires a later ADR.

## 11. Release process

1. approved PRs merged to protected `main`;
2. CI green on release commit;
3. version/tag and release notes;
4. image build from commit and provenance recorded;
5. database backup;
6. migration review and execution;
7. application deployment;
8. readiness and smoke tests;
9. rollback decision window;
10. release result recorded.

Codex may prepare changes and evidence. A human operator authorizes production deployment and release.

## 12. Rollback

Before beta, document:

- application image rollback;
- database compatibility window;
- when migration rollback is unsafe;
- restore-from-backup escalation;
- how to put the service into read-only/maintenance mode;
- how to communicate reservation uncertainty during an incident.

Do not promise automatic rollback until tested.

## 13. Production-readiness gates

Do not label the service production-ready until all are evidenced:

- accepted authentication method and administrator access path;
- TLS and secure settings verification;
- database conflict/concurrency tests;
- token lifecycle and redaction tests;
- backup and isolated restore drill;
- migration and rollback runbook;
- monitoring/alert path;
- privacy/retention decision;
- administrator and incident runbooks;
- migration/cutover plan from SmartScheduling;
- human security and release approval.

## 14. Remaining Production Gaps

The scaffold is intentionally not production-ready. Remaining gaps include:

- accepted production host, DNS, TLS, and reverse-proxy configuration;
- production secret-management integration and operator-managed secret rotation;
- administrator verification of imported asset hardware identity and capabilities;
- no real deployment performed and no live TLS/DNS/certificate issuance;
- no backup scheduler or restore drill against a production copy;
- no production monitoring stack or alert routing;
- no OIDC, email, password reset, or notifications;
- no real SmartScheduling export processed, production import performed, or cutover rehearsed;
- no execution gateway integration;
- reverse-proxy static-asset strategy for production if WhiteNoise is later replaced;
- no projects/resource restrictions or delegated resource-manager roles beyond active staff.
