# DRAFT UNTIL STRATEGIC RECONCILIATION — 016-a — Qualify and contain pilot-readiness failure boundaries

**State: DRAFT.** Not a FINAL order. Not publishable. Stored under
`oap/strategic-instructions/initial-orders/` (strategic home: `drafts/`). Finalization
requires fresh remote/state inspection and actual metadata; future base SHAs,
governance revisions, issue/PR numbers, timings and results remain UNRESOLVED here and
must never be fabricated.

## Milestone and prerequisites

Milestone: M-LOCAL-PILOT-EVIDENCE

- 015 accepted
- Human-selected local-pilot evidence target; not authorized during bootstrap

## Durable provenance

- A: SAR-025 and original WO0013 read-only safe-command contract
- E: inspected pilot_readiness_check.py evaluates application counts before database_migration_ready and uses broad exception catch in policy coverage; not reproduced here

Requirements: SAR-008, SAR-025, SAR-026, SAR-032

## Goal

Reproduce through the actual CLI whether DB-down/unmigrated/query-failure state yields safe structured readiness output, then make the smallest in-scope repair if required.

## Inspect

- `src/slaif_reservation/api/management/commands/pilot_readiness_check.py`
- `src/slaif_reservation/config/operational.py`
- `tests/test_pilot_readiness_check.py`
- `docs/runbooks/internal-alpha-pilot-readiness.md`

## Scope

One operator command and focused tests/docs. Keep aggregate-only read-only semantics and strict/non-strict contract. Check connectivity/migration before dependent tables; do not convert unexpected errors into policy absence or falsely pass. No new pilot gates/product policy without strategic reconciliation.

## Non-goals

- No real deployment, credentials, private data or lab access; no new gateway, OIDC, monitoring, groups, public API surface or migration semantics beyond explicitly reconciled repair; no dependency by convenience. Coding never merges. Result/report/CI identities are actual observations, not draft promises.
- No active-order rewriting, self-merge, authority expansion or DHA invention.

## Change allowlist (draft; finalize from live state)

- Paths named under Inspect plus their direct test/doc companions and the exact
  order/active/report bytes for this objective.
- Everything else is protected; `forbidden_resources` in the final metadata will name
  production/lab/credential/remote boundaries explicitly.

## Numbered acceptance criteria

1. Real command invocation against owned unreachable DB is bounded and redacted, with machine-readable failure if that is the reconciled contract.
2. Unmigrated/missing-table case does not produce a sensitive raw traceback and cannot pass a readiness gate.
3. Strict mode returns nonzero for required failure; non-strict and JSON semantics are explicitly documented, not guessed.
4. Expected missing/ambiguous policies are distinguished from DB/programming failure; no catch-all silently declaring readiness.
5. SQL write interception or field snapshots prove no inserts/updates/deletes/schema changes, not just equal row counts.
6. Normal ready/warning behavior and existing JSON keys remain compatible or a deliberate versioned correction is justified.

## Tests and verification (exact named tests or tests to create)

- uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test tests/test_pilot_readiness_check.py
- Subprocess CLI failure tests with finite timeouts and synthetic credential sentinels; disconnected and unmigrated isolated PostgreSQL targets
- Full standard product regression from TESTING.md; no parallel independent pytest on same DB

Required CI at the actual reviewed head: quality, test, security, container (plus any
adopted OAP checks). Finite timeouts; owned fixture resources; not-run/blocked limits
stated truthfully.

## Negative paths

Deliberately unreachable/synthetic URLs only. Do not aim checks at real hosts or expose connection strings. Diagnostic order stops if the entry boundary is not actually reached.

## Documentation

Command contract/runbooks/testing strategy and evidence-linked issue; update source/projection only if contract changes.

## Decision policy (D0/D1/D2)

D0 reproduction/repair within existing command guarantee; D1 only if a material unresolved safety contract meets all five; no real DB access (D2).

## Gate

Actual CLI evidence reviewed; no production-readiness claim from successful counts.

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
  further mutation. Expected report path: `oap/reports/016-a-pilot-readiness-failure-boundaries.md`.
- Coding never merges. Strategy review and the target gate remain independent of this
  report.

## Deferred human adjudication

- Decision: NONE

(Draft default. Reconcile before FINAL: replace only with an exact APPEND declaration
and complete strategy-authored payload when a matter truly meets all five conditions.)
