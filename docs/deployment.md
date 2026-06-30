# Deployment and Operations

**Status:** development foundation implemented; later implementation slices harden production

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

Start the database:

```bash
docker compose up -d db
```

Install locked dependencies:

```bash
uv sync --locked --all-groups
```

Apply migrations to the local PostgreSQL service:

```bash
cp .env.example .env
uv run --env-file .env python manage.py migrate
```

Validate and optionally import the sanitized bootstrap inventory:

```bash
uv run --env-file .env python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml
uv run --env-file .env python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml --apply
```

Run the application locally:

```bash
uv run --env-file .env python manage.py runserver
```

Start the Compose application service:

```bash
docker compose up --build app
```

Migrations are a deliberate command. They are not hidden inside the application worker startup.

Work Order 0003 adds PostgreSQL-specific reservation migrations. The migration chain installs the
`btree_gist` extension with `BtreeGistExtension()` and creates the
`reservation_no_overlap_per_asset` exclusion constraint. The deployment/migration role must be
allowed to create this extension, or an operator must preinstall it in the target database before
running migrations.

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

## 5. Containers

The scaffold image:

- uses the Python 3.13 slim image;
- run as a non-root user;
- install only locked production dependencies;
- collects Django admin and drf-spectacular-sidecar static assets during image build;
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
```

The configured runtime user must be `10001:10001`.

## 6. Health endpoints

- `/health/live`: application process responds; no expensive dependencies.
- `/health/ready`: database reachable. Later production hardening may add required migration-state
  checks once domain migrations exist.

Health responses contain no secrets, build environment, database host, or dependency versions beyond an approved release identifier.

Local smoke:

```bash
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready
```

## 7. Database lifecycle

### Migrations

- run `migrate --plan` or equivalent review before production migration;
- back up before destructive/large migrations;
- use backward-compatible expand/contract patterns once zero-downtime matters;
- do not edit previously deployed migrations;
- record application release and migration state.

### Backup

Before beta:

- automated daily logical or physical backup;
- protected/encrypted storage;
- retention policy;
- failure alert;
- documented restore command;
- successful restore drill into an isolated database;
- reconciliation of key record counts after restore.

A backup without a restore test is not release evidence.

## 8. Reverse proxy and TLS

- valid certificate and automatic renewal;
- HTTP to HTTPS redirect;
- preserve validated client/proxy headers;
- request and upload limits;
- sensible timeouts;
- security headers coordinated with Django;
- API access logs redacted according to the security model;
- optional network restriction for `/admin/`.

Caddy is a reasonable small-deployment default; Nginx is equally acceptable if already operated institutionally. Select in the deployment PR based on the actual host environment.

## 9. Logging and monitoring

Minimum:

- structured application logs;
- reverse-proxy logs with secrets/queries reviewed;
- health probe;
- service restart monitoring;
- PostgreSQL disk/connection/backup monitoring;
- alerts for sustained 5xx, failed readiness, backup failure, and disk pressure;
- reservation conflict metrics treated as product signal, not necessarily errors.

Prometheus/Grafana integration is optional until an operator requirement is confirmed.

## 10. Scheduled work

Use idempotent management commands for:

- cleanup of expired idempotency records. Work Order 0006 adds `expires_at` on records but does not
  add a scheduler or cleanup command; stored rows remain authoritative until cleanup is implemented;
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
- production secret management;
- token-verifier pepper and API-token lifecycle implementation;
- API-token, ordinary member authorization, reservation HTTP routes, and availability behavior;
- administrator verification of imported asset hardware identity and capabilities;
- backup/restore runbook and restore drill;
- logging redaction tests beyond the current health/settings scaffold;
- reverse-proxy static-asset strategy for production if WhiteNoise is later replaced;
- operational monitoring and incident runbooks.
