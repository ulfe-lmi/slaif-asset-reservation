# DRAFT UNTIL STRATEGIC RECONCILIATION — 020-a — Record human-agent-management pilot path through actual adapters

**State: DRAFT.** Not a FINAL order. Not publishable. Stored under
`oap/strategic-instructions/initial-orders/` (strategic home: `drafts/`). Finalization
requires fresh remote/state inspection and actual metadata; future base SHAs,
governance revisions, issue/PR numbers, timings and results remain UNRESOLVED here and
must never be fabricated.

## Milestone and prerequisites

Milestone: M-LOCAL-PILOT-EVIDENCE

- 016-019 accepted or explicitly reassessed with evidence
- Local-pilot evidence target selected

## Durable provenance

- H: original human/agent unified reservation goal
- A: SAR-001, SAR-011-SAR-020; operator pilot preparation runbook
- E: rehearsal currently emphasizes anonymous smoke and historical browser tests; integrated target evidence remains to assemble

Requirements: SAR-001, SAR-011, SAR-012, SAR-013, SAR-014, SAR-015, SAR-016, SAR-017, SAR-018, SAR-019, SAR-020, SAR-021, SAR-023, SAR-024, SAR-032

## Goal

Prove the intended local pilot workflow via actual browser/HTTP/API/DB boundaries with synthetic principals and fresh isolated resources; prepare exact-revision evidence for ICA.

## Inspect

- `deploy/rehearse_internal_alpha_deployment.sh`
- `tests/browser/`
- `tests/test_api_v1_reservations.py`
- `docs/runbooks/internal-alpha-pilot-preparation.md`
- `docs/api-contract.md`

## Scope

Synthetic staff/member fixtures through accepted local setup, browser token issuance and own booking, HTTP bearer create/replay/cancel/release, staff blackout/audit boundaries, correct rejected credentials/ownership and correlation. Do not use force_authenticate or bypass services for the actual boundary under test. Asset UUID may come from operator fixture: asset discovery remains staff-session-only and is disclosed as a limitation.

## Non-goals

- No real deployment, credentials, private data or lab access; no new gateway, OIDC, monitoring, groups, public API surface or migration semantics beyond explicitly reconciled repair; no dependency by convenience. Coding never merges. Result/report/CI identities are actual observations, not draft promises.
- No active-order rewriting, self-merge, authority expansion or DHA invention.

## Change allowlist (draft; finalize from live state)

- Paths named under Inspect plus their direct test/doc companions and the exact
  order/active/report bytes for this objective.
- Everything else is protected; `forbidden_resources` in the final metadata will name
  production/lab/credential/remote boundaries explicitly.

## Numbered acceptance criteria

1. Browser active member and staff paths execute actual session/CSRF behavior, with no service-account/inactive bypass.
2. Token appears once, subsequent browser history/list and captured logs do not leak it; wrong/revoked/expired attempts fail generically.
3. Bearer mutation replay preserves response/correlation/Location and one audit event; other-owner access is non-disclosing.
4. Staff maintenance affects availability and booking correctly without revealing reason to ordinary caller or auto-cancelling existing bookings.
5. Required app settings remain production-shaped except documented local TLS absence; actual socket exposure is loopback only.
6. Evidence matrix names each SAR requirement, entry point, test, actual revision and remaining UNPROVEN target gaps, without self-certifying ICA.

## Tests and verification (exact named tests or tests to create)

- Dedicated owned disposable stack end-to-end script/test using actual HTTP and Playwright; no real model/Neumann calls
- Run existing browser suite explicitly with --browser chromium and full API/management suites sequentially
- Capture only sanitized machine-readable outcomes; disable secret-bearing screenshots/traces/videos

Required CI at the actual reviewed head: quality, test, security, container (plus any
adopted OAP checks). Finite timeouts; owned fixture resources; not-run/blocked limits
stated truthfully.

## Negative paths

No pilot users/real accounts/real lab resources. TLS/OIDC/monitoring/atomic asset discovery are excluded rather than mocked into a false feature claim.

## Documentation

Exact run result and ICA request/evidence index; retain manual real-pilot gates, not a new planning-only loop.

## Decision policy (D0/D1/D2)

D0 approved local evidence assembly; no real target authorization inferred. Human product target remains D2.

## Gate

Fresh independent full-architecture ICA at exact merged revision, then human judgment; no code agent self-certification.

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
  further mutation. Expected report path: `oap/reports/020-a-pilot-path-actual-adapters.md`.
- Coding never merges. Strategy review and the target gate remain independent of this
  report.

## Deferred human adjudication

- Decision: NONE

(Draft default. Reconcile before FINAL: replace only with an exact APPEND declaration
and complete strategy-authored payload when a matter truly meets all five conditions.)
