<!-- OAP-META
{
 "id": "020-a",
 "round": "a",
 "base_sha": "219563eb8074c5124c7326f0a0c9d025bdba5b7a",
 "issue_number": 39,
 "branch": "codex/39-oap-020-a-booking-maintenance-races",
 "pr_mode": "CREATE_OR_RESUME",
 "previous_round": null,
 "allowed_paths": [
  "tests/test_reservations_concurrency.py",
  "oap/orders/020-a-booking-maintenance-races.md",
  "oap/active",
  "oap/reports/020-a-booking-maintenance-races.md"
 ],
 "forbidden_resources": [
  "any change under src/ (no product behavior, model, API, template, settings, or migration changes; this round is evidence-only)",
  "any change to reservation/blackout/policy service semantics, lock behavior, or interval rules",
  "any weakening, skipping, or loosening of a race test to make it pass",
  "any change under docs/, deploy/, .github/, data/, or other test files",
  "new dependencies or removed dependencies",
  "deployment of any kind; real/production databases; real lab/Neumann machines; real SmartScheduling data",
  "credentials, auth files, sessions, tokens, auth homes",
  "DNS/TLS/firewall changes, public exposure, repository visibility or branch-protection changes",
  "any mutating GitHub operation except pushing this branch and opening this objective's PR",
  "merging or auto-merging any PR (merge is strategy's delegated act after review)",
  "ICA activity, milestone completion claims, or work from other drafts/objectives (including legacy-import concurrency, which is explicitly deferred)",
  "model provider endpoints other than the configured qwen-neumann role profile"
 ]
}
-->

# 020-a — Prove the booking-vs-maintenance concurrency invariant under
# separate transactions

## Goal

The reservation authority's core trust property (SAR-001: an accepted
reservation remains policy-compliant, auditable and exclusive for its
asset and effective time) is proven under real separate transactions only
for reservation-vs-reservation and policy-vs-reservation. The
booking-vs-maintenance races are unproven. This round adds
barrier-controlled separate-transaction race tests proving: no
interleaving commits a reservation overlapping an ACTIVE blackout; both
commit orderings of reservation-vs-blackout are handled (exactly one side
commits, the other loses with BLACKOUT_CONFLICT); a deactivation-vs-
booking race never books over an active blackout; and the
staff-acknowledged-overlap path (confirmed_overlap=True) may commit with a
prior reservation. Evidence-only: if a test exposes a genuine violation of
accepted semantics, the round stops and reports the exact interleaving
(no product fix in this round, no weakened test).

## Durable provenance and requirements

- H: in-session human principal instruction 2026-09-14 — continue the
  strategy → coding → review → merge loop autonomously; prefer work that
  directly enables actual users over OAP machinery.
- E: origin/main 219563eb8074c5124c7326f0a0c9d025bdba5b7a (019-a
  quiescent, INACTIVE, CI green at that head).
  tests/test_reservations_concurrency.py — 4 existing tests, real
  threading.Barrier parallelism with per-thread connections
  (transaction=True): two simultaneous overlapping creates (exactly one
  RESERVATION_CONFLICT), adjacent creates both commit, principal
  upcoming-limit serialization, and policy-update-waits-for-reservation
  (deterministic pause-after-lock via monkeypatch of
  services._raise_if_asset_overlap).
  src/slaif_reservation/reservations/services.py (reviewed 2026-09-14):
  create_reservation locks principal row -> asset row (select_for_update)
  -> policy rows, then plain-SELECT checks _raise_if_blackout_overlap and
  _raise_if_asset_overlap before insert (GiST exclusion
  reservation_no_overlap_per_asset as final arbiter). create_blackout
  locks staff actor -> asset row, then overlap check, raising
  BLACKOUT_CONFLICT unless confirmed_overlap=True; records
  overlapping_reservations count in audit metadata. deactivate_blackout
  locks the BLACKOUT row only (select_for_update().get(pk)) — NOT the
  asset row.
- A: S-12 (one proof-sized objective), S-15 (report boundary), S-19
  (name the exact failing boundary; real PostgreSQL transaction
  boundaries, not mocks).
- C: S-16 / S-17 (exact-head review; delegated development merge; main
  workflows verified CI-only).
- Reconciliation: the strategic-home draft
  019-a-booking-maintenance-concurrency.md (DRAFT UNTIL STRATEGIC
  RECONCILIATION) is retired as a queue item and reconciled into this
  bounded first PR. Its import-vs-booking concurrency scope is EXPLICITLY
  DEFERRED to a separate future objective (coverage reassessed 2026-09-14:
  staff-driven batch import is lower pilot urgency than live
  booking/maintenance races; the requirement is recorded here, not
  dropped). Its policy-vs-booking scope is already evidenced by the
  existing policy-lock test.
Requirements: SAR-001 (one reservation authority; exclusivity), SAR-006/
SAR-007/ SAR-008 (policy/audit/lifecycle invariants preserved), SAR-032
(evidence before readiness).

## Current reconciled state and prerequisites

- Base main (local and remote): 219563eb8074c5124c7326f0a0c9d025bdba5b7a.
  Worktree must be clean on main before starting; `oap/active` absent
  (INACTIVE).
- Known facts (verify, do not assume): the test harness
  run_parallel uses a threading.Barrier and per-thread
  close_old_connections (separate connections, real commits under
  transaction=True); the deterministic pause pattern in the existing
  policy-lock test monkeypatches a service-internal helper to signal a
  threading.Event after the lock is held and block until release;
  create_blackout's overlap check calls the module-level
  services.overlapping_blocking_reservations after _lock_asset;
  create_reservation's blackout check is the module-level
  services._raise_if_blackout_overlap (called after asset+policy locks);
  blackout audit metadata records overlapping_reservations;
  BLACKOUT_CONFLICT is the blackout-related ReservationDomainError code
  raised to reservation creators for active-blackout overlap.

## Ordered read set

Standard compact read set, plus: tests/test_reservations_concurrency.py
(in full), src/slaif_reservation/reservations/services.py (create
reservation, create blackout, deactivate blackout, overlap helpers,
lock helpers), the MaintenanceBlackout and Reservation models (fields,
exclusion constraint name), the blackout audit action constants, and the
blackout exception codes in reservations/exceptions.py.

## Scope and allowed paths

New race tests in tests/test_reservations_concurrency.py (extend the
existing file; reuse make_user/make_asset/make_policy, run_parallel, and
the pause-after-lock pattern; keep the four existing tests
byte-identical). All tests use real PostgreSQL transaction boundaries
(transaction=True, separate connections), no mocks of the database:

1. Non-deterministic reservation x blackout race (confirmed_overlap
   False): barrier-parallel create_reservation(range R, asset X) and
   create_blackout(overlapping R, asset X). Repeat across 5 fresh
   asset/user iterations to sample interleavings. Per iteration assert
   exactly one outcome "committed" and one BLACKOUT_CONFLICT (never both
   committed), and the final-state invariant: a committed reservation on
   X/R coexists with NO active blackout overlapping R; a committed
   blackout coexists with NO reservation on X/R.
2. Deterministic reservation-wins ordering: monkeypatch
   services._raise_if_blackout_overlap to signal an event (reservation
   holds the asset lock) and block until release; run the two threads;
   assert the blackout thread is still running while the reservation
   holds the lock (it is blocked on the asset row lock); release; assert
   outcomes reservation "committed" + blackout BLACKOUT_CONFLICT; state:
   reservation present, no active blackout.
3. Deterministic blackout-wins ordering (mirror): monkeypatch
   services.overlapping_blocking_reservations (used by create_blackout
   after its asset lock) to signal + block; assert the reservation thread
   blocks on the asset lock; release; assert blackout "committed" +
   reservation BLACKOUT_CONFLICT; state: active blackout present, no
   reservation on X/R.
4. Deactivation x booking race: seed an active blackout B covering R on
   asset X; barrier-parallel create_reservation(R) and
   deactivate_blackout(B). Repeat across 5 fresh iterations. Per
   iteration assert: B ends deactivated; the reservation either committed
   (then B was already deactivated before its check — consistent) or lost
   with BLACKOUT_CONFLICT; NEVER a committed reservation overlapping R
   while B is active at the end. Record which orderings were actually
   observed across the iterations in the report (truthful sampling note).
5. Staff-acknowledged overlap: reservation commits first (deterministic
   pause pattern as in item 2); blackout created with
   confirmed_overlap=True blocks on the asset lock, then proceeds; assert
   BOTH "committed"; state: reservation present AND active blackout
   present with audit metadata overlapping_reservations >= 1 (the
   acknowledged-overlap path remains legal under race conditions).

Non-negotiable: if any test exposes a genuine violation (e.g., both
committed with an unacknowledged overlap, or a committed reservation over
an active blackout), do NOT change product code and do NOT weaken the
test. Stop, and publish a truthful PARTIAL/FAILED report naming the exact
race, observed vs expected, and the minimal reproduction; strategy
decides the repair round.

## Non-goals

- No product behavior change of any kind; no src/ change; no docs change.
- No legacy-import concurrency tests (explicitly deferred).
- No OAP/governance changes, no canary work, no ICA, no milestone claim.
- No deployment, no real data, no lab/Neumann contact.
- No merge, auto-merge, approval or settings change.

## Numbered acceptance criteria

1. The report records the pre-change state: the four existing test names,
   the exact lock-acquisition sequence of create_reservation /
   create_blackout / deactivate_blackout (including that
   deactivate_blackout locks the blackout row, not the asset row), the
   plain-SELECT nature of the blackout overlap check, and the GiST
   exclusion constraint name.
2. The new race tests (scope items 1–5) are present in
   tests/test_reservations_concurrency.py, pass against the current
   product code, and the four pre-existing tests are byte-identical
   (prove by diff). The report records which orderings were observed in
   the non-deterministic iterations.
3. Full pytest suite, quality gates (ruff check, ruff format --check,
   mypy), makemigrations --check --dry-run, manage.py check,
   operational_check, spectacular --validate --fail-on-warn, and the CI
   container + security jobs all green at the exact implementation head;
   the CI test job shows the new race tests running (counted in the pass
   total, on real PostgreSQL).
4. If criterion 2 cannot hold truthfully: a PARTIAL/FAILED report with
   the exact failing race (observed vs expected, minimal repro), no
   product change, no weakened test.
5. The diff touches only allowed_paths.

## Deferred human adjudication

- Decision: NONE
