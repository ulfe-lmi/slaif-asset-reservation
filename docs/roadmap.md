# Roadmap and PR Sequence

The sequence is intentionally narrow. Each implementation item should normally be one Codex work-order issue and one pull request.

## Phase 0: constitution bootstrap

### PR 0 — project constitution and discovery

Contents:

- `AGENTS.md`;
- discovery, architecture, domain, API, security, test, deployment, migration, UI, and workflow documents;
- ADRs;
- sanitized asset inventory;
- GitHub issue/PR templates;
- PR 1 work order.

Acceptance:

- no application-readiness claim;
- no secrets or private client data;
- architecture and non-goals accepted by human lead;
- repository settings scheduled/configured after merge.

## Phase 1: executable foundation

### PR 1 — Django/PostgreSQL scaffold

Use `docs/work-orders/0001-application-scaffold.md`.

Delivers:

- Python/uv project;
- Django custom user from first migration;
- DRF/OpenAPI shell;
- PostgreSQL development environment;
- health endpoints;
- test/tooling baseline;
- Docker image/Compose development path;
- green CI;
- production settings fail-fast skeleton.

Non-goal: asset/reservation behavior.

### PR 2 — asset inventory and import

Delivers:

- `Asset` hierarchy, tags/capability validation, admin;
- sanitized YAML schema validation and idempotent import command;
- list/detail web placeholder and read-only API;
- verified tests that legacy IDs remain provenance;
- no invented hostname/CUDA/GPU UUID.

### PR 3 — reservation and policy core

Delivers:

- reservation policy baseline;
- reservation model and lifecycle;
- PostgreSQL range/exclusion constraint;
- conflict translation;
- audit transaction integration;
- concurrency, boundary, DST, and policy tests;
- ADR amendment for effective end/release representation.

Non-goal: polished UI or public token API.

### PR 4 — human reservation MVP

Delivers:

- login/member views;
- asset availability;
- create/list/detail/cancel/release own reservation;
- privacy-safe shared availability;
- accessible server-rendered UX;
- browser/form tests.

## Phase 2: unified agent API

### PR 5 — scoped API token lifecycle

Delivers:

- one-time token generation;
- HMAC/one-way verifier;
- scopes, expiry, revocation, last-use metadata;
- human token management UI;
- redaction and security tests;
- no administrative API tokens yet.

### PR 6 — API v1 reservation operations

Delivers:

- `/api/v1/me`;
- assets and availability;
- reservations create/read/list/cancel/release;
- stable problem details;
- idempotency;
- generated OpenAPI and contract tests;
- same domain service tests across web/API.

### PR 7 — management, audit, and policy UX

Delivers:

- resource-manager/admin workflows;
- maintenance blackouts;
- effective policy display/edit;
- audit views and safe export;
- conflict/affected-reservation handling;
- role matrix tests.

## Phase 3: internal alpha

### PR 8 — operational hardening

Delivers:

- production Compose/service configuration;
- reverse proxy choice;
- structured logging;
- health/readiness;
- backup and restore tooling/runbook;
- secure setting checks;
- migration/deployment smoke tests;
- operator runbooks.

### PR 9 — SmartScheduling migration tooling

Delivers:

- approved export parser using synthetic fixtures;
- dry-run/idempotent batch import;
- inventory/reservation reconciliation;
- no private export in Git;
- cutover runbook;
- legacy conflict reporting.

### PR 10 — alpha verification and remediation

Verification-only run, strategic/cross-model security and architecture audit, then narrowly scoped repair PRs. Do not combine unrelated audit findings into one large repair.

Internal-alpha gate is defined in `docs/discovery-brief.md`.

## Phase 4: operational beta

Potential work, subject to new work orders/ADRs:

- institutional OIDC;
- email notifications;
- improved calendar and accessibility audit;
- policy/quota refinements;
- retention/export workflows;
- deployment rehearsal and production cutover;
- monitoring integration;
- public documentation if repository/deployment visibility changes.

## Phase 5: machine integration

Only after reservation beta:

- internal reservation-verification API;
- deterministic Neumann gateway integration;
- physical inventory/probe agent;
- atomic capability-based allocation;
- gateway audit correlation;
- optional scheduler adapters.

The gateway remains a separate trust boundary and service. Do not embed arbitrary process execution into the reservation web application.

## Release language

- **Bootstrap:** docs/governance only.
- **Pre-alpha:** executable scaffold; core product incomplete.
- **Internal alpha:** human and agent core paths proven, operational limitations accepted.
- **Operational beta:** deployed to intended users with backup/restore, monitoring, security review, and cutover evidence.
- **Production-ready:** separate explicit human release decision; never inferred from feature count or green unit tests alone.
