# Project Documentation

## Start here

- [QUICKSTART.md](../QUICKSTART.md) — the essential Docker path to a running
  local evaluation instance (loopback-only, development settings).
- [INSTALL.md](../INSTALL.md) — the full operator installation and deployment
  guide (production-shaped Compose, protected secrets, proxy, backup/restore,
  upgrades, rollback).
- [README.md](../README.md) — product overview, capabilities, and the
  documentation map.

## Users and API clients

- [api-contract.md](api-contract.md) — the implemented `/api/v1/` contract:
  authentication and scopes, idempotency, problem details, and every
  endpoint.
- [human-ui.md](human-ui.md) — browser workflows: member navigation, core
  screens, accessibility baseline.
- [domain-model.md](domain-model.md) — entities, reservation lifecycle,
  policy resolution, and time semantics (UTC, half-open effective-end
  history).

## Operators

- [deployment.md](deployment.md) — deeper deployment reference and rationale:
  configuration reference, container image facts, proxy/TLS, logging,
  scheduled work, release process, rollback, readiness gates.
- [runbooks/](runbooks/) — operator runbooks: first internal-alpha deployment
  checklist, pilot preparation and readiness gates, backup and restore,
  database-unavailable response, token/pepper incidents, blackouts,
  idempotency cleanup, SmartScheduling migration.
- [READINESS.md](READINESS.md) — readiness as separate dimensions, not a
  single green flag.
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
- [decisions/](decisions/) — accepted architecture decision records (ADRs).
- [ARCHITECTURE.md](../ARCHITECTURE.md) — the canonical system architecture;
  [architecture.md](architecture.md) is a compatibility pointer to it.

## Governance and history

Specialist and historical material, not installation instructions:

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
- [audit/](audit/) — independent code-audit protocol, request and report
  templates, and audit reports (immutable evidence records).
- [oap/README.md](../oap/README.md) — the local OAP control plane layout
  (orders, reports, pointer).
- [migration-from-smartscheduling.md](migration-from-smartscheduling.md) —
  the sanitized migration plan (the real migration/cutover remains separate
  and human-supervised).
- [roadmap.md](roadmap.md) — historical work-order sequence and milestone
  language.
- [project-handoff.md](project-handoff.md) — historical strategic snapshot
  (see its header); live state is GitHub `main` plus `oap/`.
- [work-orders/](work-orders/) — historical accepted work-order baselines.
- [bootstrap/](bootstrap/) — immutable conversion snapshots (inputs,
  previous bytes) and [BOOTSTRAP-SOURCES.md](BOOTSTRAP-SOURCES.md) with the
  conversion provenance and drift record.
