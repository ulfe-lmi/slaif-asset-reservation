# DRAFT UNTIL STRATEGIC RECONCILIATION — 018-a — Prove isolated PostgreSQL backup and restore end to end

**State: DRAFT.** Not a FINAL order. Not publishable. Stored under
`oap/strategic-instructions/initial-orders/` (strategic home: `drafts/`). Finalization
requires fresh remote/state inspection and actual metadata; future base SHAs,
governance revisions, issue/PR numbers, timings and results remain UNRESOLVED here and
must never be fabricated.

## Milestone and prerequisites

Milestone: M-LOCAL-PILOT-EVIDENCE

- 017 accepted or equivalent ownership qualification
- Local-pilot evidence target selected

## Durable provenance

- A: SAR-027; docs/runbooks/backup-and-restore.md and internal-alpha-pilot-readiness.md
- E: prior evidence establishes wrapper refusal/dry-run but not an executed isolated restore round trip

Requirements: SAR-006, SAR-007, SAR-014, SAR-018, SAR-021, SAR-027, SAR-029, SAR-032

## Goal

Exercise the existing wrappers with PostgreSQL-native tools into a separate owned empty target and verify restored domain data/constraints without touching production.

## Inspect

- `src/slaif_reservation/api/management/commands/backup_database.py`
- `src/slaif_reservation/api/management/commands/restore_database.py`
- `src/slaif_reservation/api/management/commands/_postgres_tools.py`
- `docs/runbooks/backup-and-restore.md`
- `Dockerfile`

## Scope

Add one disposable integration drill and minimum wrapper fixes if the actual boundary fails. Two independently named source/target databases, synthetic data via existing services, protected temp dump, explicit apply. Never restore into source or current default development DB by assumption. No scheduler, cloud store, encryption product or production credentials.

## Non-goals

- No real deployment, credentials, private data or lab access; no new gateway, OIDC, monitoring, groups, public API surface or migration semantics beyond explicitly reconciled repair; no dependency by convenience. Coding never merges. Result/report/CI identities are actual observations, not draft promises.
- No active-order rewriting, self-merge, authority expansion or DHA invention.

## Change allowlist (draft; finalize from live state)

- Paths named under Inspect plus their direct test/doc companions and the exact
  order/active/report bytes for this objective.
- Everything else is protected; `forbidden_resources` in the final metadata will name
  production/lab/credential/remote boundaries explicitly.

## Numbered acceptance criteria

1. Source identity and empty target identity are verified separately; same-target/unknown target refuses before restore.
2. pg_dump and pg_restore really run; dry-run/refusal alone does not pass this order.
3. Restored user/asset/reservation/effective-end/audit/token verifier/idempotency/import provenance and relevant constraints/indexes match safe internal checks without printing secrets.
4. Original source remains unchanged; target operational_check and conflict-integrity test succeed.
5. Failure leaves safe bounded diagnostics and only owned cleanup; dump/DSN/password never logged or committed.
6. Record restore evidence at exact code/database-tool revisions and state remaining real-operator/backup-policy gaps.

## Tests and verification (exact named tests or tests to create)

- New isolated backup/restore integration script with finite timeouts and explicit disposable-target checks
- Existing tests/test_operational_hardening.py plus refusal/incorrect-tool-version/error redaction cases
- Fresh migration and operational_check in restored target; genuine exclusion conflict rejected

Required CI at the actual reviewed head: quality, test, security, container (plus any
adopted OAP checks). Finite timeouts; owned fixture resources; not-run/blocked limits
stated truthfully.

## Negative paths

Database apply is authorized only for owned fixture targets under selected work order; all real data/restore remains D2. Do not infer backup availability from filesystem existence.

## Documentation

Exact safe local drill, prerequisites/tools, actual result and limits in runbook; no production restore claim.

## Decision policy (D0/D1/D2)

D0 isolated test/repair. Changed recovery strategy may require D1/ADR; real restore or destructive unknown target is D2.

## Gate

Human pilot gate still needs actual operator-approved backup retention/location/restore cadence.

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
  further mutation. Expected report path: `oap/reports/018-a-isolated-backup-restore.md`.
- Coding never merges. Strategy review and the target gate remain independent of this
  report.

## Deferred human adjudication

- Decision: NONE

(Draft default. Reconcile before FINAL: replace only with an exact APPEND declaration
and complete strategy-authored payload when a matter truly meets all five conditions.)
