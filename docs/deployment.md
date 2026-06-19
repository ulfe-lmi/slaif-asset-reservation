# Deployment and Operations

**Status:** target design; PR 1 establishes development deployment, later PRs harden production

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

PR 1 must provide a repeatable development path using:

- Python 3.13 managed by `uv`;
- committed `uv.lock`;
- PostgreSQL 17 through Docker Compose or an explicitly documented local service;
- synthetic seed data;
- one command or short sequence for migrations and tests.

No developer should need SmartScheduling credentials or production data.

## 4. Configuration

Expected categories; exact variable names are created and documented by implementation:

- Django secret key;
- token-verifier pepper distinct from Django secret;
- database URL/credentials;
- allowed hosts and canonical external URL;
- CSRF trusted origins;
- secure-proxy/HTTPS settings;
- default timezone and language;
- email backend/relay, if enabled;
- log level and structured-log destination;
- optional OIDC configuration later;
- backup destination configured outside application environment where possible.

Provide `.env.example` with safe placeholders and explanations. Never provide a production `.env`.

## 5. Containers

The production image should:

- use a pinned Python base image or digest policy established by the PR;
- run as a non-root user;
- install only locked production dependencies;
- exclude tests, caches, `.git`, local secrets, and development data;
- collect static assets at build or release time;
- expose no development server;
- include a health check or documented external probe;
- emit logs to stdout/stderr.

Database migrations run as a deliberate release step, not unpredictably in every worker startup.

## 6. Health endpoints

- `/health/live`: application process responds; no expensive dependencies.
- `/health/ready`: database reachable, required tables/migration state usable, critical configuration present.

Health responses contain no secrets, build environment, database host, or dependency versions beyond an approved release identifier.

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

- cleanup of expired idempotency records;
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
