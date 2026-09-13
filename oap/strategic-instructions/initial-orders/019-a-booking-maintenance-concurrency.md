# DRAFT UNTIL STRATEGIC RECONCILIATION — 019-a — Qualify booking versus maintenance and import concurrency

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

- A: SAR-007, SAR-009, SAR-020, SAR-029
- E: existing four concurrency tests and pre-insert blackout checks do not by themselves prove every cross-service race

Requirements: SAR-001, SAR-006, SAR-007, SAR-008, SAR-009, SAR-019, SAR-020, SAR-029, SAR-032

## Goal

Exercise actual PostgreSQL transaction boundaries when ordinary booking/import overlaps maintenance or policy changes; repair only an evidenced violation of accepted semantics.

## Inspect

- `src/slaif_reservation/reservations/services.py`
- `src/slaif_reservation/legacy_import/importer.py`
- `src/slaif_reservation/api/idempotency.py`
- `tests/test_reservations_concurrency.py`

## Scope

Barrier-controlled separate DB connections, both commit orderings, bounded lock timeouts. Preserve existing half-open intervals, confirmation rules and no auto-cancellation. Do not invent parent-child booking exclusion or fairness policy. Inspect consistent principal/asset/policy locks across entry points before changes.

## Non-goals

- No real deployment, credentials, private data or lab access; no new gateway, OIDC, monitoring, groups, public API surface or migration semantics beyond explicitly reconciled repair; no dependency by convenience. Coding never merges. Result/report/CI identities are actual observations, not draft promises.
- No active-order rewriting, self-merge, authority expansion or DHA invention.

## Change allowlist (draft; finalize from live state)

- Paths named under Inspect plus their direct test/doc companions and the exact
  order/active/report bytes for this objective.
- Everything else is protected; `forbidden_resources` in the final metadata will name
  production/lab/credential/remote boundaries explicitly.

## Numbered acceptance criteria

1. If maintenance commits first, later overlapping booking cannot be accepted; if booking wins, maintenance honors affected-reservation confirmation semantics.
2. Concurrent duplicate import retains one source+legacy-ID mapping and no partial reservation/audit; changed mapping is classified.
3. Policy/asset/user changes between plan and apply cannot bypass future-booking constraints.
4. Unrelated integrity/database failures are not misreported as reservation_conflict.
5. Any fix proves the failing case before change and preserves web/API/management/migration parity and audit rollback.
6. Tests use real transactions/threads/connections, not mocks replacing the lock/exclusion boundary.

## Tests and verification (exact named tests or tests to create)

- uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test tests/test_reservations_concurrency.py tests/test_legacy_import.py
- New deterministic concurrency cases with barrier timeouts and both orderings; no timing-only sleep proof
- Full product suites sequentially; schema/migration verification if changes become necessary

Required CI at the actual reviewed head: quality, test, security, container (plus any
adopted OAP checks). Finite timeouts; owned fixture resources; not-run/blocked limits
stated truthfully.

## Negative paths

Unexpected failure first triggers a bounded diagnosis. Do not weaken exclusion, bypass policy, shorten audit obligations or use a new lock service.

## Documentation

Concurrency ownership rationale and new evidence; ADR only for deliberate accepted architectural change.

## Decision policy (D0/D1/D2)

D0 test/bug repair; material competing safe lock strategies may be D1 only after all five conditions; production locks/data remain D2.

## Gate

ICA must assess actual transaction paths and current revision, not test count alone.

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
  further mutation. Expected report path: `oap/reports/019-a-booking-maintenance-concurrency.md`.
- Coding never merges. Strategy review and the target gate remain independent of this
  report.

## Deferred human adjudication

- Decision: NONE

(Draft default. Reconcile before FINAL: replace only with an exact APPEND declaration
and complete strategy-authored payload when a matter truly meets all five conditions.)
