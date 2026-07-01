# ADR 0012: Operational Hardening and Deployment Shape

**Status:** accepted
**Date:** 2026-07-01

## Context

Work Orders 0001 through 0007 created the reservation authority, human and API workflows,
management UI, audit evidence, and maintenance blackouts. Before an internal alpha can be operated
on a Linux server, the project needs a concrete but still example-only production shape, safe
configuration checks, deployment smoke commands, backup/restore wrappers, structured logs, and
operator runbooks.

This decision does not deploy the service and does not touch real hosts, secrets, DNS, TLS
certificates, production databases, or repository settings.

## Decision

The supported first internal-alpha deployment shape is:

- one Django/Gunicorn application container built from this repository;
- one PostgreSQL 17 container or managed PostgreSQL instance reachable only from the application
  network;
- a boring reverse proxy, initially documented with Caddy, terminating TLS and forwarding requests
  to the application;
- static files collected into the image and served by WhiteNoise or the reverse proxy after an
  operator verifies the final host setup;
- deliberate release commands for migrations and operational checks, not hidden migration side
  effects on ordinary worker startup;
- systemd timer or cron entries operated outside the application for recurring management commands.

The repository includes example files only:

- `compose.production.example.yaml`;
- `deploy/env.production.example`;
- `deploy/Caddyfile.example`.

Production settings fail closed when required secrets, hosts, origins, database configuration, or
token pepper are absent or obviously unsafe. HSTS remains explicit opt-in until the final HTTPS host
and subdomain ownership are verified. Production uses structured JSON logs with an allowlist of
operational fields and defensive redaction of credential/body concepts.

Operational smoke is provided by `python manage.py operational_check`. It verifies database
connectivity, applied migrations, required static assets, critical settings, bootstrap inventory
validation, and the idempotency cleanup command registration.

Database backup and restore use PostgreSQL-native tools through wrappers:

- `python manage.py backup_database --output <path>`;
- `python manage.py backup_database --output <path> --apply`;
- `python manage.py restore_database --input <path>`;
- `python manage.py restore_database --input <path> --apply`.

The wrappers default to validation-only dry-run behavior, require `DATABASE_URL`, avoid printing
passwords, and do not implement retention. Backup retention and scheduling remain operator policy.

Expired API idempotency rows are cleaned by:

- `python manage.py purge_expired_idempotency_records`;
- `python manage.py purge_expired_idempotency_records --apply`.

The command defaults to dry-run, deletes only expired rows in apply mode, supports batching, and is
safe to rerun. Scheduling remains operator responsibility.

## Consequences

The service has a concrete internal-alpha deployment contract without depending on Kubernetes,
Terraform, Ansible, cloud SDKs, Redis, Celery, Prometheus, Grafana, Sentry, or a queue. Operators get
clear examples and runbooks, but a real deployment still requires human-managed secrets, TLS, DNS,
database storage, backup storage, monitoring, and scheduling.

Replacing the API-token pepper still invalidates existing tokens until a future key-ring/rotation
decision exists. Production OIDC, notifications, email, full monitoring, SmartScheduling migration
tooling, execution gateway integration, projects/resource restrictions, and automated backup
scheduling remain outside this slice.
