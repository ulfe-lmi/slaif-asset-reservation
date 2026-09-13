# DRAFT UNTIL STRATEGIC RECONCILIATION — 017-a — Qualify rehearsal ownership and failure-safe cleanup

**State: DRAFT.** Not a FINAL order. Not publishable. Stored under
`oap/strategic-instructions/initial-orders/` (strategic home: `drafts/`). Finalization
requires fresh remote/state inspection and actual metadata; future base SHAs,
governance revisions, issue/PR numbers, timings and results remain UNRESOLVED here and
must never be fabricated.

## Milestone and prerequisites

Milestone: M-LOCAL-PILOT-EVIDENCE

- 015 accepted
- Local-pilot evidence target selected

## Durable provenance

- A: SAR-031; WO0011 requires disposable owned files/resources and no real env overwrite
- E: baseline rehearsal uses deployment file paths and configurable project name; existing operational test writes REHEARSAL_ENV directly; negative ownership coverage needs qualification

Requirements: SAR-024, SAR-026, SAR-031, SAR-032, SAR-035

## Goal

Prove rehearsal/tests cannot overwrite or remove an existing operator env/secret or unrelated Compose resources; repair only reproduced ownership/cleanup defects.

## Inspect

- `deploy/rehearse_internal_alpha_deployment.sh`
- `compose.production.example.yaml`
- `tests/test_operational_hardening.py`
- `.github/workflows/ci.yml`

## Scope

Narrow rehearsal helper/test safety changes. Use a temporary checkout fixture, no valuable env files. Qualify symlinks (including dangling), existing files/directories, parallel invocations, project-name collisions and partial startup. Keep accepted one-port loopback shape and production fail-closed configuration.

## Non-goals

- No real deployment, credentials, private data or lab access; no new gateway, OIDC, monitoring, groups, public API surface or migration semantics beyond explicitly reconciled repair; no dependency by convenience. Coding never merges. Result/report/CI identities are actual observations, not draft promises.
- No active-order rewriting, self-merge, authority expansion or DHA invention.

## Change allowlist (draft; finalize from live state)

- Paths named under Inspect plus their direct test/doc companions and the exact
  order/active/report bytes for this objective.
- Everything else is protected; `forbidden_resources` in the final metadata will name
  production/lab/credential/remote boundaries explicitly.

## Numbered acceptance criteria

1. Existing env/password paths, symlinks and parent-path escapes remain byte/inode-preserved and trigger safe refusal.
2. Tests themselves never create/unlink a fixture in the real working checkout deployment path.
3. Existing Docker project/container/volume under colliding name is never adopted or down -v removed.
4. Failure after partial resource creation cleans only owned resource identities; signals/quit do not leave misleading success.
5. No unsafe YAML/shell interpolation through configurable image/project/port values; valid TCP port bounds and clean argv.
6. Actual rendered Compose has exactly intended loopback binding; full isolated rehearsal succeeds and cleanup is verified.

## Tests and verification (exact named tests or tests to create)

- Focused subprocess tests in copied temporary repository with fake Docker ownership inventory and sentinel files
- Real local Docker rehearsal in fresh unique project only after fake failure tests pass; inspect resources before/after
- uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test tests/test_operational_hardening.py
- Run preserved full product tests and container job checks

Required CI at the actual reviewed head: quality, test, security, container (plus any
adopted OAP checks). Finite timeouts; owned fixture resources; not-run/blocked limits
stated truthfully.

## Negative paths

Never run baseline destructive-path tests against a checkout with real env/secrets. Fake a foreign Compose resource to prove refusal; do not target an actual production name.

## Documentation

Rehearsal ownership/cleanup requirements, actual command and resource IDs redacted as needed; maintain docs/production separation.

## Decision policy (D0/D1/D2)

D0 contained resource-safety repair; D2 any permission to delete non-owned state or contact remote Docker; do not downgrade to D1.

## Gate

Owned-resource proof plus regressions; deployment remains unauthorized.

## PR mode and reporting requirements

- Round `a`: `pr_mode=CREATE_OR_RESUME`; later suffixes `AMEND` the same objective
  issue/branch/PR.
- Compact read set: root router -> `oap/coding-instructions/AGENTS.md` ->
  `ARCHITECTURE-for-agents.md` -> `OAP-COMMUNICATION-coding-agent.md` -> exact active
  order -> `oap/coding-instructions/SECURITY-CORE.md` + `TESTING-CORE.md` -> only
  ordered excerpts. No full-source dump into routine coding context.
- PR created/amended BEFORE final report; literal implementation head; report-only
  first-parent commit; `Report publication commit: SELF`; truthful implementation vs
  report-head CI; remote verification receipt; exact two-byte response OK; then no
  further mutation. Expected report path: `oap/reports/017-a-rehearsal-ownership-cleanup.md`.
- Coding never merges. Strategy review and the target gate remain independent of this
  report.

## Deferred human adjudication

- Decision: NONE

(Draft default. Reconcile before FINAL: replace only with an exact APPEND declaration
and complete strategy-authored payload when a matter truly meets all five conditions.)
