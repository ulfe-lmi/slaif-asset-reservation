<!-- OAP-META
{
  "id": "031-b",
  "round": "b",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "696b87965920817f1a6b36589562a4af68e75497",
  "issue_number": 61,
  "branch": "codex/61-oap-031-a-gunicorn-idle-connections",
  "pr_mode": "AMEND",
  "previous_round": "031-a",
  "pr_number": 62,
  "allowed_paths": [
    "tests/test_gunicorn_responsiveness.py (startup-failure cleanup and slow-client sensitivity only)",
    "oap/orders/031-b-gunicorn-regression-review.md",
    "oap/active",
    "oap/reports/031-b-gunicorn-regression-review.md"
  ],
  "forbidden_resources": [
    "all other application/domain/auth/policy/UI/dependency/migration/inventory/workflow/canonical governance edits",
    "foreign/user dirty or ignored files, existing deployment files, live services or their images/containers/volumes",
    "actual public exposure, host LAN/DNS/TLS/firewall changes, real secrets/private/production data/lab/Neumann probes",
    "merge or auto-merge, force-push/rebase/reset/clean/stash, authentication copying"
  ],
  "requirements": [
    "SAR-022",
    "SAR-024",
    "SAR-025",
    "SAR-031",
    "SAR-032",
    "SAR-033",
    "SAR-035",
    "SAR-038"
  ],
  "decision_class": "D0",
  "target_gate": "M-INTERNET-UX-PILOT development; real exposure remains human D2",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "8483a070026f382bb9b698e9346f3cb33f7dea44f8190b231431585986ebb17d",
    "PLAN.md": "d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06"
  }
}
-->

# 031-b — Close real-server regression review gaps

## Goal / provenance
H: the selected human requirement 8 mandates durable real Gunicorn regression and safe owned-resource cleanup. A: S-16/S-19, preceding 031-a numbered criterion 3, SAR-031/SAR-032. E: independently verified report head 820028778ea2ca5b21bfa1510804bbcd1054d78f, implementation 49d176474f09f149d87d8366dae803eda3fd14be, PR62 OPEN on the same branch, all five report-head checks SUCCESS. Exact-source review found test_gthread_shutdown_cleans_children_on_failure lacks server.stop in finally when wait_ready/assertion fails; partial-header test neither settles nor checks held state before/after probes, permitting a scheduling false positive. I: no new product judgment. C: D0 bounded test correction, no CRITICAL.

## Scope / non-goals
Amend existing issue61/PR62/branch only. Preserve all 031-a configuration, docs, order and report bytes. No application/dependency/migration/runtime-config/workflow/governance changes. No reset/clean/stash, foreign resources, real exposure, data, secrets, DNS/TLS/firewall, or merge/auto-merge. Read compact coding law, exact order and new test only; do not absorb strategic history.

## Numbered acceptance
1. Guarantee owned subprocess/socket cleanup in every server-using test, including a readiness/assertion failure BEFORE explicit stop. Make stop idempotent or track completed cleanup appropriately. The cleanup regression must deliberately inject a failure inside the protected region, execute finally cleanup, and prove process/session children are gone without leaking them on its own failure. Keep bounded termination/kill/reap and unique loopback ports.
2. For six partial-header blockers, allow a bounded settle interval, assert all six remain open before AND after probing both actual Django endpoints. Strengthen sensitivity with real old-sync partial-header negative control (six partial clients held, warm, bounded timeout on both endpoints, held-open proof, close/recovery), or parameterize the existing old-sync test to exercise both silent and partial variants. No mocks or sleep-only claim. Retain genuine keep-alive test and shipped command pinning.
3. Run focused real-server regression locally; meaningful startup/failure cleanup proof, ruff lint/format/type and diff checks; full exact implementation-head CI all five SUCCESS before COMPLETE. Existing unchanged PostgreSQL/browser/concurrency checks still run through full CI. Do not claim local full-suite success when environmental failures remain. No unnecessary broad re-runs beyond these checks.
4. Normal immutable sequence, same PR Closes #61: implementation/order/active push -> exact-head checks -> report-only commit (literal full implementation SHA firstparent, SELF, unknown report-head checks at authoring) -> push and verify actual remote -> notify then exit. Record the review gaps and proof of their correction; previous report remains historical, not rewritten.

## Negative paths / strongest objection
A test fixture can leak server children precisely when startup fails, or accidentally probe before slow requests occupy workers. Deliberate exception/finally proof and real old-sync silent/partial controls address those gaps. Added waits increase suite time; keep limits finite, one short settle per variant, no pixel/UI/load expansion. Safe local anonymous routes and dead database URL only.

## Verification / documentation
Tests only; existing operator prose remains correct. Report exact commands, results, child cleanup, held states, old/new behavior and implementation/report CI separation. No new milestone/public-readiness claim.

## Recovery / reporting
Same objective and PR, correction suffix b, previous a immutable. On interruption reconcile durable state, do not create another PR. Expected report oap/reports/031-b-gunicorn-regression-review.md. Wrapper consumed control; never wait twice. Dedicated qualified qwen-neumann profile unchanged. FIFO is notification only; durable report publication is authoritative even if no reader is present.

## Deferred human adjudication
- Decision: NONE
