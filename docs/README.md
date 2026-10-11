# Project Documentation

## Start here

- [README.md](../README.md) — product overview, capabilities, and the
  documentation map.
- [QUICKSTART.md](../QUICKSTART.md) — the essential Docker path to a running
  local evaluation instance (loopback-only, development settings).
- [INSTALL.md](../INSTALL.md) — the full operator installation and deployment
  guide for the authenticated HTTPS pilot (private Compose services, protected secrets, proxy, backup/restore,
  upgrades, rollback).
- [ARCHITECTURE.md](../ARCHITECTURE.md) — the canonical system architecture.

- [Demo inventory and bootstrap format](../data/bootstrap/README.md) — optional,
  entirely fictitious local demo; preparing generic operator inventory.

Remote users use the HTTPS hostname configured through INSTALL, not port 8000.

## Users and API clients

- [api-contract.md](api-contract.md) — the implemented `/api/v1/` contract:
  [authentication and scopes](api-contract.md#authentication-and-scopes),
  idempotency, problem details, and every endpoint.
- [security-model.md](security-model.md#5-api-token-design) — API token
  design: creation, verification, revocation and rotation.
- [human-ui.md](human-ui.md) — browser workflows: member navigation, core
  screens, accessibility baseline.
- [domain-model.md](domain-model.md) — entities, reservation lifecycle,
  policy resolution, and time semantics (UTC, half-open effective-end
  history).

## Operators

- [deployment.md](deployment.md) — deeper deployment reference and rationale:
  configuration reference, container image facts, proxy/TLS, logging,
  scheduled work, release process, rollback, readiness gates.
- [branding.md](branding.md) — optional same-image operator branding
  (CSS/logo/favicon/images): slots, limits, fallback, refresh semantics.
- [ux/visual-design.md](ux/visual-design.md) — default SLAIF visual system,
  responsive layouts, appearance tokens and packaged font provenance.
- [runbooks/](runbooks/) — operator checklists, pilot readiness, backup and restore,
  database-unavailable response, token/pepper incidents, blackouts,
  idempotency cleanup, SmartScheduling migration.
- [runbooks/internal-alpha-pilot-preparation.md](runbooks/internal-alpha-pilot-preparation.md) —
  internal-network preparation pack; use INSTALL for the current Internet-facing boundary.
- [runbooks/internal-alpha-pilot-readiness.md](runbooks/internal-alpha-pilot-readiness.md) —
  database/inventory readiness gates, complementing current HTTPS/security qualification.
- [runbooks/backup-and-restore.md](runbooks/backup-and-restore.md) — backup
  and restore runbook.
- [runbooks/smartscheduling-migration.md](runbooks/smartscheduling-migration.md) —
  SmartScheduling migration runbook (the real private cutover remains
  separate and human-supervised).
- [security-model.md](security-model.md) — security model: protected assets,
  trust boundaries, threats and controls, token design, privacy and logging.
- [SECURITY.md](../SECURITY.md) — project security posture and vulnerability
  reporting.

## Developers

- [TESTING.md](../TESTING.md) — the standard verification command set and
  required evidence.
- [testing-strategy.md](testing-strategy.md) — test layers, critical test
  matrix, and evidence expectations.
- [CONTRIBUTING.md](../CONTRIBUTING.md) — development setup, privacy and
  security rules, pull requests.
- [security-model.md](security-model.md) — protected assets, trust
  boundaries, threats and controls, token design, privacy and logging.
- [decisions/](decisions/) — accepted architecture decision records (ADRs);
  [architecture.md](architecture.md) is a compatibility pointer to the
  canonical [ARCHITECTURE.md](../ARCHITECTURE.md).

## Governance and history

Specialist and historical material, not installation instructions:

- [AGENTS.md](../AGENTS.md) — the root role router.
- [PLAN.md](../PLAN.md) — the canonical product plan.
- [ARCHITECTURE-for-agents.md](../ARCHITECTURE-for-agents.md) — the compact
  executor projection of the canonical architecture.
- [CRITICAL.md](../CRITICAL.md) — the deferred human adjudication register.
- [READINESS.md](READINESS.md) — initial-conversion readiness baseline
  (governance baseline, not part of the current operator path).
- [oap-workflow.md](oap-workflow.md) — the adopted and operational
  Concentrated OAP workflow (roles, publication, reporting).
- [OAP-RUNBOOK.md](OAP-RUNBOOK.md) — setup, operation, and adoption runbook.
- [AGENT-ROLE-SETUP.md](AGENT-ROLE-SETUP.md) — Codex-only role homes and
  client qualification.
- [DECISION-POLICY.md](DECISION-POLICY.md) — D0/D1/D2 decision policy.
- [RUNTIME-CONSTRAINTS.md](RUNTIME-CONSTRAINTS.md) — development
  control-plane runtime limits.
- [repository-settings.md](repository-settings.md) — manual GitHub
  protection settings.
- [audit/](audit/) — independent closure-audit protocol, request and report
  templates, and audit reports (immutable evidence records).
- [Current Internet/UX software audit](audit/reports/M-INTERNET-UX-PILOT-cd5a436.md)
  and [publication freshness](audit/qualification/M-INTERNET-UX-PILOT-FRESHNESS.md)
  — exact-revision evidence for human judgment; real exposure remains separate.
- [oap/README.md](../oap/README.md) — the local OAP control plane layout
  (orders, reports, pointer).
- [migration-from-smartscheduling.md](migration-from-smartscheduling.md) —
  the sanitized migration plan (the real migration/cutover remains separate
  and human-supervised).
- [roadmap.md](roadmap.md) — historical work-order sequence and milestone
  language; current selected product scope is in PLAN.md.
- [project-handoff.md](project-handoff.md) — historical strategic snapshot
  (see its header); live state is GitHub `main` plus `oap/`.
- [work-orders/](work-orders/) — historical accepted work-order baselines.
- [bootstrap/](bootstrap/) — immutable conversion snapshots (inputs,
  previous bytes) and [BOOTSTRAP-SOURCES.md](BOOTSTRAP-SOURCES.md) with the
  conversion provenance and drift record.
