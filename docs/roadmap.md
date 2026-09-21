# Roadmap and Work-Order Sequence

The sequence is intentionally narrow. Each implementation item should normally be one Codex work-order issue and one pull request.

## Phase 0: constitution bootstrap

### Bootstrap — project constitution and discovery

Contents:

- `AGENTS.md`;
- discovery, architecture, domain, API, security, test, deployment, migration, UI, and workflow documents;
- ADRs;
- sanitized asset inventory;
- GitHub issue/PR templates;
- Work Order 0001.

Acceptance:

- no application-readiness claim;
- no secrets or private client data;
- architecture and non-goals accepted by human lead;
- repository settings scheduled/configured after merge.

## Phase 1: executable foundation

### Work Order 0001 — Django/PostgreSQL scaffold

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

### Work Order 0002 — asset inventory and import

Delivers:

- `Asset` hierarchy, tags/capability validation, admin;
- sanitized YAML schema validation and idempotent import command;
- list/detail web placeholder and read-only API;
- verified tests that legacy IDs remain provenance;
- no invented hostname/CUDA/GPU UUID.

### Work Order 0003 — reservation and policy core

Delivers:

- reservation policy baseline;
- reservation model and lifecycle;
- PostgreSQL range/exclusion constraint;
- conflict translation;
- audit transaction integration;
- concurrency, boundary, DST, and policy tests;
- ADR amendment for effective end/release representation.

Non-goal: polished UI or public token API.

### Work Order 0004 — human reservation MVP

Delivers:

- login/member views;
- asset availability;
- create/list/detail/cancel/release own reservation;
- privacy-safe shared availability;
- accessible server-rendered UX;
- browser/form tests.

## Phase 2: unified agent API

### Work Order 0005 — scoped API token lifecycle

Status: merged.

Delivers:

- one-time token generation;
- HMAC/one-way verifier;
- scopes, expiry, revocation, last-use metadata;
- human token management UI;
- redaction and security tests;
- no administrative API tokens yet.

### Work Order 0006 — API v1 reservation operations

Status: merged.

Delivers:

- `/api/v1/me`;
- assets and availability;
- reservations create/read/list/cancel/release;
- stable problem details;
- idempotency;
- generated OpenAPI and contract tests;
- same domain service tests across web/API.

### Work Order 0007 — management, audit, and policy UX

Status: merged.

Delivers:

- resource-manager/admin workflows;
- maintenance blackouts;
- effective policy display/edit;
- audit views and safe export;
- conflict/affected-reservation handling;
- role matrix tests.

## Phase 3: internal alpha

### Work Order 0008 — operational hardening

Status: merged.

Delivers:

- production Compose/service configuration;
- reverse proxy choice;
- structured logging;
- health/readiness;
- backup and restore tooling/runbook;
- secure setting checks;
- migration/deployment smoke tests;
- operator runbooks.

### Work Order 0009 — SmartScheduling migration tooling

Status: merged.

Delivers:

- approved export parser using synthetic fixtures;
- dry-run/idempotent batch import;
- inventory/reservation reconciliation;
- no private export in Git;
- cutover runbook;
- legacy conflict reporting.

### Work Order 0010 — alpha verification and remediation

Status: completed verification.

Verification-only run, strategic/cross-model security and architecture audit, then narrowly scoped
repair pull requests. Work Order 0010 found no blocker, high, or medium findings. The first
docs-only repair addressed continuity drift after verification.

Internal-alpha gate is defined in `docs/discovery-brief.md`.

### Work Order 0011 — internal alpha deployment rehearsal

Status: merged.

Delivers:

- disposable production-shaped rehearsal script;
- temporary synthetic production-env handling;
- Docker runtime/static/bootstrap checks;
- fresh disposable migrations and bootstrap import smoke;
- health/login/management/API smoke checks;
- pilot readiness gate runbook.

### Work Order 0012 — internal alpha pilot preparation pack

Status: merged.

Delivers:

- first controlled internal lab pilot plan;
- operator checklist for assets, staff, users, policies, tokens, audit, backup, and rehearsal;
- placeholder-only communication templates;
- explicit go/no-go conditions and limitations;
- no deployment and no production data, secrets, DNS, TLS, or private SmartScheduling exports.

### Work Order 0014 — concentrated OAP workflow conversion (reserved)

Status: adopted. The one-time adoption was merged by the human, the Concentrated OAP workflow is
operational, and objectives 015-a through 027-a have been implemented on `main` (see `oap/orders/`).

Delivers:

- root PLAN/ARCHITECTURE/CRITICAL (candidate), router AGENTS.md, oap/ governance tree;
- preserved accepted architecture snapshot and compatibility pointer;
- Codex-only role model, helpers, fixture harness (tests/oap/);
- targeted doc/CI/manifest updates; no application behavior change.

Acceptance:

- application bytes, migrations, lockfile, inventory and history unchanged;
- fixture harness green at the reviewed head; product regression separately authorized;
- independent conversion audit and human adoption before any activation.

### Next roadmap item

Status: human-selected.

Current human selection (2026-09-17): deployment qualification for the first
controlled internal-alpha Docker deployment. Completed since that selection:
024-a (canonical installation/deployment documentation), 025-a/b/c
(deployment-qualification docs, image reproducibility, and the post-merge
full-rehearsal CI workflow), 026-a (materialized M-LOCAL-PILOT-EVIDENCE ICA
request at merged main 21f6204), 027-a (ICA findings F-001/F-002
doc-drift fix), and 028-a (post-027 current-state documentation
correction). The Independent Closure Audit was executed 2026-09-17 in a
fresh isolated context at product revision 21f6204 (report:
`docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md`; 37 IMPLEMENTED / 1
PARTIAL / 0 ABSENT / 0 UNPROVEN; no in-target blockers; the single PARTIAL
row's drift was corrected by 027-a). The protocol re-audit required after
remediation was executed 2026-09-22 in a fresh isolated context at current
main a9c3133 (report:
`docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-a9c3133.md`; 38 IMPLEMENTED / 0
PARTIAL / 0 ABSENT / 0 UNPROVEN; no in-target blockers; product-runtime
bytes unchanged since 21f6204). The next slice is the first real
internal-alpha deployment, human-authorized and performed per `INSTALL.md`
(deployment-gate brief presented 2026-09-17 against 21f6204, regenerated
2026-09-22 against a9c3133; a real deployment has not yet been
evidenced). The slice after that remains human-selected.

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
