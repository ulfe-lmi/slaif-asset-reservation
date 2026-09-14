# Project Documentation

## Canonical entry points

- [`INSTALL.md`](../INSTALL.md) — canonical installation and deployment document (root level).
  Docker/Compose is the deployment path; `uv` is the development path.
- [`deployment.md`](deployment.md) — deeper deployment reference and rationale.

## Strategic baseline

- `discovery-brief.md` — product category, goals, scope, risks, and release gates.
- `architecture.md` — system/container architecture and trust boundaries.
- `domain-model.md` — entities, lifecycle, constraints, and time semantics.
- `api-contract.md` — intended `/api/v1/` behavior for agents.
- `human-ui.md` — browser workflows and accessibility baseline.
- `security-model.md` — assets, threats, controls, and security gates.
- `testing-strategy.md` — evidence required from implementation PRs.
- `deployment.md` — target Linux deployment and operational gates.
- `migration-from-smartscheduling.md` — sanitized migration plan.

## Governance and continuity

- `oap-workflow.md` — Concentrated OAP conversion profile (roles, publication,
  reporting, adoption); legacy loop text archived under
  `bootstrap/1/previous/`.
- `OAP-RUNBOOK.md` — setup/operation/adoption runbook for the candidate profile.
- `AGENT-ROLE-SETUP.md` — Codex-only role homes and client qualification.
- `BOOTSTRAP-SOURCES.md` — conversion provenance, preserved bytes, drift record.
- `DECISION-POLICY.md` — D0/D1/D2 policy for this project.
- `READINESS.md` — readiness dimensions and milestone gates.
- `RUNTIME-CONSTRAINTS.md` — development control-plane runtime limits.
- `bootstrap/1/` — immutable conversion snapshots (inputs, previous bytes).
- `repository-settings.md` — manual GitHub protection settings.
- `roadmap.md` — work-order sequence and milestone language.
- `project-handoff.md` — historical strategic snapshot (see its header); live state is GitHub `main` + `oap/`.
- `decisions/` — accepted architecture decision records.
- `work-orders/` — issue-ready strategic task baselines.
