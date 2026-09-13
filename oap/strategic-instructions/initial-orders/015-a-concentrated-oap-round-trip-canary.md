# DRAFT UNTIL STRATEGIC RECONCILIATION — 015-a — Concentrated OAP round-trip canary on the existing repository

**State: DRAFT.** Not a FINAL order. Not publishable. Stored under
`oap/strategic-instructions/initial-orders/` (strategic home: `drafts/`). Finalization
requires fresh remote/state inspection and actual metadata; future base SHAs,
governance revisions, issue/PR numbers, timings and results remain UNRESOLVED here and
must never be fabricated.

## Milestone and prerequisites

Milestone: M-CONVERSION

- Human-merged conversion adoption WO0014
- Qualified roles/runtime/remote and attributable activation for M-CONVERSION

## Durable provenance

- H: current user requests Codex-only Concentrated OAP conversion of existing project
- A: generator sections 5,10,12-15; OAP-PROTOCOL OP01-OP16

Requirements: SAR-033, SAR-034, SAR-035, SAR-037, SAR-038

## Goal

Demonstrate one actual activated coding round and strategic review without changing product behavior; create a small oap/WORKFLOW-CANARY.md with safe measured invocation/publication evidence.

## Inspect

- `oap/bin/`
- `oap/governance/`
- `AGENTS.md`
- `oap/coding-instructions/`
- `oap/strategic-instructions/`
- `.github/workflows/ci.yml`

## Scope

Use the accepted real private development remote and configured Codex roles only after activation. Add only the canary document, its exact order/active bytes and final report. Record model-visible role/cwd/homes and implementation/report identities without auth data. Strategy performs independent review and delegated development merge only after all gates; this order never tells coding to merge.

## Non-goals

- No real deployment, credentials, private data or lab access; no new gateway, OIDC, monitoring, groups, public API surface or migration semantics beyond explicitly reconciled repair; no dependency by convenience. Coding never merges. Result/report/CI identities are actual observations, not draft promises.
- No active-order rewriting, self-merge, authority expansion or DHA invention.

## Change allowlist (draft; finalize from live state)

- Paths named under Inspect plus their direct test/doc companions and the exact
  order/active/report bytes for this objective.
- Everything else is protected; `forbidden_resources` in the final metadata will name
  production/lab/credential/remote boundaries explicitly.

## Numbered acceptance criteria

1. The existing product bytes/migrations/lockfile/inventory are unchanged; the complete diff is allowed governance evidence only.
2. Wrapper consumes exactly one wake-up and one fresh coding invocation uses the compact read set; no second consumer or idle model polling.
3. One objective issue/branch/PR exists; the PR is created before report composition.
4. Final report-only commit has literal implementation head first parent, SELF marker and only matching report path changed.
5. Remote publication is verified before response OK; report correctly distinguishes implementation-head CI from later report-head CI.
6. Strategy reviews exact report head and four required jobs, strongest reason not to merge, authority and side effects; no release claim.

## Tests and verification (exact named tests or tests to create)

- python3 -m unittest discover -s tests/oap -p 'test_*.py' -v
- oap/bin/check_governance.py --repo <actual> --strategic-home <actual>
- oap/bin/check_state.py --repo <actual> --strategic-home <actual>
- oap/bin/verify_report.py --repo <actual> --id 015-a --pr <actual> --head <actual-report-head> --remote origin
- Verify exact remote current-head quality/test/security/container; actual URLs/SHAs only

Required CI at the actual reviewed head: quality, test, security, container (plus any
adopted OAP checks). Finite timeouts; owned fixture resources; not-run/blocked limits
stated truthfully.

## Negative paths

Lost-response replay and duplicate signals remain fixture tests; do not deliberately corrupt the real remote to prove recovery. If publication fails, leave truthful local evidence and no completion signal.

## Documentation

oap/WORKFLOW-CANARY.md and exact immutable report; no README production status change.

## Decision policy (D0/D1/D2)

D0 under activated development delegation. D2 for visibility/credentials/release or unreviewed merge side effect. DHA draft default NONE, reconciled before FINAL.

## Gate

Independent conversion audit tied to accepted merged governance and actual canary report; human M-CONVERSION acceptance remains separate.

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
  further mutation. Expected report path: `oap/reports/015-a-concentrated-oap-round-trip-canary.md`.
- Coding never merges. Strategy review and the target gate remain independent of this
  report.

## Deferred human adjudication

- Decision: NONE

(Draft default. Reconcile before FINAL: replace only with an exact APPEND declaration
and complete strategy-authored payload when a matter truly meets all five conditions.)
