# Contributing

This repository uses an Orchestrated Agentic Programming workflow. A Codex-only Concentrated OAP conversion candidate (bootstrap generation 1) is materialized locally and inactive: until its one-time human-merged adoption (WO0014, see `docs/decisions/0014-concentrated-oap-workflow-conversion.md` and `docs/OAP-RUNBOOK.md`), the legacy human-per-merge workflow below remains in force.

## Before implementation

- Read `AGENTS.md`.
- Read the linked work-order issue and relevant architecture documents.
- Verify current `main` and existing open PRs.
- Do not begin from an unapproved broad feature description.

## Work units

One approved work order should normally produce one pull request. The issue must state:

- verified current state;
- goal;
- scope;
- explicit non-goals;
- acceptance criteria;
- tests and documentation required;
- security or migration constraints.

## Branches

Use:

```text
codex/<issue-number>-<short-name>
```

Human-authored branches may use another clear prefix. Never commit directly to `main`.

## Commits and pull requests

- Keep commits scoped and reviewable.
- Link the work-order issue.
- Use `.github/PULL_REQUEST_TEMPLATE.md`.
- Report exact test commands and outcomes.
- Do not report skipped or unrun checks as passed.
- Do not merge your own PR.

## Architecture changes

An architectural, security-boundary, persistence, authentication, or deployment change requires an ADR under `docs/decisions/`. A feature PR must not smuggle in such a decision without review.

## Secrets and personal data

Do not place credentials, browser cookies, anti-forgery tokens, API tokens, private client exports, appointment details, or production data in commits, issues, PRs, fixtures, screenshots, or logs.

## Development environment

The executable development workflow is established by Work Order 0001. Until then, this repository contains architecture, governance, and sanitized bootstrap data only.
