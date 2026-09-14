<!-- OAP-META
{
 "kind": "report",
 "id": "020-a",
 "order_path": "oap/orders/020-a-booking-maintenance-races.md",
 "order_sha256": "2ff7529aa66001265961456109645df2694ab8da0f09b4702851b8b6fb21f1c8",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 39,
 "pr_number": 40,
 "branch": "codex/39-oap-020-a-booking-maintenance-races",
 "implementation_head": "fd1a2a42ed8178af6d9eeec86637718a49f5d6ee",
 "base_sha": "219563eb8074c5124c7326f0a0c9d025bdba5b7a",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "fd1a2a42ed8178af6d9eeec86637718a49f5d6ee",
  "runs": [
   {"run_id": 34805717866, "workflow": "CI", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 34805717774, "workflow": "oap", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 020-a report — booking-vs-maintenance concurrency invariant under
# separate transactions

Order digest: 2ff7529aa66001265961456109645df2694ab8da0f09b4702851b8b6fb21f1c8
(committed `oap/orders/020-a-booking-maintenance-races.md`; byte-identical to
the materialized `.FINAL` source — re-hashed
`2ff7529a…f1c8` both on the untracked source and on the published copy).

Implementation head SHA: fd1a2a42ed8178af6d9eeec86637718a49f5d6ee

Report publication commit: SELF

**Result: COMPLETE** — all five scoped race tests are present, pass against
the current product code on real PostgreSQL 17 separate transactions, and no
interleaving exposed a genuine violation of accepted semantics. No product
code was changed and no test was weakened; the stop condition of the order
was not triggered.

## Reconciliation at start (C-05/C-06/CP-03)

- Ordered reads: root router → `oap/coding-instructions/AGENTS.md` →
  `ARCHITECTURE-for-agents.md` → `OAP-COMMUNICATION-coding-agent.md` → exact
  active order → `SECURITY-CORE.md`/`TESTING-CORE.md` → ordered subtree
  excerpts only: `tests/test_reservations_concurrency.py` in full,
  `reservations/services.py` (create reservation, create blackout,
  deactivate blackout, overlap helpers, lock helpers, policy locking),
  `MaintenanceBlackout`/`Reservation` model fields and exclusion constraint,
  blackout audit action constants, `reservations/exceptions.py` codes.
- `oap/active` = exactly `020-a` + LF (6 bytes). `oap/bin/check_state.py`
  on the CI-equivalent working tree (without the untracked `.FINAL` source;
  see Local-environment artifacts) → `state=ACTIVE_PENDING detail=valid
  final order is active; awaiting wake-up/invocation`, order `020-a` round
  `a`, branch `codex/39-oap-020-a-booking-maintenance-races`. Wrapper had
  already consumed the control OK; not consumed again.
- Local main = remote `origin/main` = `219563eb8074c5124c7326f0a0c9d025bdba5b7a`
  (= the order's `base_sha`; 019-a quiescent on top of merged PR #38).
  Worktree clean except the materialized order (untracked
  `oap/orders/020-a-booking-maintenance-races.FINAL.md`) and the pointer
  (untracked `oap/active`). Fresh round: no local/remote branch, no PR
  (`git ls-remote` + `gh` before creation); `pr_mode=CREATE_OR_RESUME`
  resolved to CREATE. PR #40 (GitHub-assigned number) on the order's exact
  branch, base `main`.
- Order hash check: committed order file sha256
  `2ff7529aa66001265961456109645df2694ab8da0f09b4702851b8b6fb21f1c8`
  matches the `.FINAL` source hash recorded above. DHA declaration:
  `- Decision: NONE` (no APPEND, no CRITICAL change this round).

## Pre-change state (acceptance criterion 1)

Four pre-existing tests in `tests/test_reservations_concurrency.py`:

1. `test_two_simultaneous_overlapping_creates_one_conflicts`
2. `test_simultaneous_adjacent_creates_both_commit`
3. `test_simultaneous_non_overlapping_creates_serialize_principal_upcoming_limit`
4. `test_policy_update_waits_for_reservation_operation_policy_lock`

Lock-acquisition sequences (reviewed 2026-09-14, base head), each service in
a single `transaction.atomic()` with real `SELECT … FOR UPDATE` row locks:

- `create_reservation`: `_lock_principal` (principal User row) →
  `_lock_asset` (Asset row) → `_validate_asset` → `lock_effective_policy`
  (resolved active policy row, `for_update=True`) → `_enforce_policy` →
  `_raise_if_blackout_overlap` → `_raise_if_asset_overlap` → insert (GiST
  exclusion as final arbiter) → audit append.
- `create_blackout`: `_lock_staff_actor` (staff User row) → `_lock_asset`
  (Asset row) → `overlapping_blocking_reservations` (plain SELECT) → raise
  `BLACKOUT_CONFLICT` iff overlaps and not `confirmed_overlap=True` →
  insert active blackout → audit with `overlapping_reservations` count in
  metadata.
- `deactivate_blackout`: `_lock_staff_actor` (staff User row) →
  `MaintenanceBlackout.objects.select_for_update().get(pk=…)` — locks the
  **blackout row only, NOT the asset row** → plain `Asset.objects.get`
  (no `FOR UPDATE`) → deactivate (idempotent) + audit if active.

Both overlap re-checks are **plain SELECTs** (no locks) executed after the
caller holds the asset row lock: `_raise_if_blackout_overlap` filters
`MaintenanceBlackout(active=True, start_at__lt=end_at, end_at__gt=start_at)`;
`_raise_if_asset_overlap` filters blocking reservations
(status confirmed/released, half-open overlap on `start_at`/
`effective_end_at`). Because a blocked `SELECT … FOR UPDATE` on the asset
row releases only at winner commit, the loser re-checks under a fresh
READ COMMITTED statement snapshot that includes the winner's row — the
mechanism the new tests prove. GiST exclusion constraint name:
`reservation_no_overlap_per_asset`
(`Reservation.EXCLUSION_CONSTRAINT_NAME`), `TsTzRange(start_at,
effective_end_at)` per asset (btree_gist via `BtreeGistExtension` in
`reservations/migrations/0001_initial.py`).

## New race tests (acceptance criterion 2)

Five tests appended to `tests/test_reservations_concurrency.py` (scope
items 1–5); all use real PostgreSQL transaction boundaries
(`@pytest.mark.django_db(transaction=True)`, per-thread
`close_old_connections`, barrier parallelism), no database mocks:

1. `test_reservation_vs_blackout_race_exactly_one_commits_across_repeats` —
   5 fresh asset/user/staff iterations, barrier-parallel
   `create_reservation(R)` vs `create_blackout(overlap R)`; per iteration
   exactly one `committed` + one `BLACKOUT_CONFLICT`, plus the final-state
   invariant (committed reservation ⇒ no active overlapping blackout, and
   vice versa).
2. `test_reservation_wins_blackout_blocked_on_asset_lock_then_conflicts` —
   deterministic reservation-first: monkeypatched
   `services._raise_if_blackout_overlap` signals after the reservation holds
   the asset lock and blocks until release (then calls the original check);
   blackout thread asserted still alive (blocked on the asset row lock)
   while paused; outcomes `reservation_committed` + `BLACKOUT_CONFLICT`;
   state: reservation present, no active blackout.
3. `test_blackout_wins_reservation_blocked_on_asset_lock_then_conflicts` —
   deterministic mirror: monkeypatched
   `services.overlapping_blocking_reservations` signals after the blackout's
   asset lock and blocks until release; reservation thread asserted alive
   (blocked on the asset row lock); outcomes `blackout_committed` +
   `BLACKOUT_CONFLICT`; state: active blackout present, no reservation.
4. `test_deactivation_vs_booking_race_never_books_over_active_blackout` —
   5 fresh iterations; seeded active blackout B covering R; barrier-parallel
   `create_reservation(R)` vs `deactivate_blackout(B)`; per iteration B ends
   deactivated (`deactivated_at` + `deactivated_by` recorded), reservation
   either committed or lost with `BLACKOUT_CONFLICT`, and never a committed
   reservation coexisting with an active B.
5. `test_staff_acknowledged_overlap_committed_alongside_reservation` —
   reservation commits first via the item-2 pause pattern; blackout with
   `confirmed_overlap=True` blocks on the asset lock then proceeds; both
   `committed`; state: reservation present AND active blackout present;
   `maintenance_blackout.created` audit event metadata
   `overlapping_reservations >= 1`.

Observed orderings in the non-deterministic iterations (truthful sampling
note; prints captured with `pytest -s`, disposable local PostgreSQL 17):

- Final committed code (1 run × 5 iterations): test 1 blackout-wins 5/5;
  test 4 reservation-conflict 5/5.
- Semantically identical pre-lint-refactor code (4 further runs × 5
  iterations; the only difference is closure-binding style for ruff B023):
  test 1 observed **both** orderings — reservation-wins 6 / blackout-wins
  14 (e.g. `['blackout_wins','reservation_wins','blackout_wins',
  'blackout_wins','blackout_wins']` and
  `['reservation_wins','blackout_wins','blackout_wins','reservation_wins',
  'reservation_wins']`); test 4 reservation-conflict 20/20.
- Interpretation: in test 4 the reservation's blackout SELECT usually runs
  before the deactivation commits (deactivation never contends for the
  asset lock, so it is not forced behind the reservation); on this host's
  timing the "deactivation commits first ⇒ reservation commits" ordering
  was not sampled in 25 iterations. Both orderings are permitted by the
  order's acceptance rule, and neither can violate the final-state
  invariant because once deactivated a blackout stays inactive.

Pre-existing-test byte-identity (proven by diff): the `git diff` of
`tests/test_reservations_concurrency.py` against base shows only (a) the
import block (added `AuditEvent`, `BLACKOUT_CONFLICT`, `MaintenanceBlackout`
imports; reformatted the models import) and (b) a pure append starting
after the last pre-existing line (diff hunk `@@ -261,0 +268 …`); no hunk
touches any of the four pre-existing test bodies. Result: 408 insertions,
2 deletions — the 2 deletions are the pre-existing models-import line
replacements inside the import block only.

## Gates (acceptance criterion 3)

Local, at implementation head `fd1a2a42ed8178af6d9eeec86637718a49f5d6ee`
(disposable `postgres:17` container `slaif-oap-020a-testpg`, loopback
127.0.0.1:54330 only, throwaway volume; migrations, bootstrap import and
`purge_expired_idempotency_records` applied to the disposable DB before
gates):

- Focused: `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test
  tests/test_reservations_concurrency.py` → **9 passed** (4 pre-existing +
  5 new), PASSED.
- Full: `uv run --env-file .env pytest` → **600 passed, 2 failed** — both
  failures are local-environment artifacts proven to pass in CI-equivalent
  state (see Local-environment artifacts); 0 failures relate to the new
  tests or product behavior.
- `uv sync --locked --all-groups` PASSED; `uv run ruff check .` PASSED;
  `uv run ruff format --check .` PASSED (181 files unchanged);
  `uv run mypy src` PASSED (119 source files);
  `uv run --env-file .env python manage.py check` PASSED (0 issues);
  `… manage.py makemigrations --check --dry-run` PASSED (no changes);
  `… manage.py spectacular --validate --fail-on-warn` PASSED (rc=0);
  `… manage.py operational_check` PASSED (database/migrations/static/
  bootstrap/idempotency_cleanup_command/operational all ok);
  `uv run pip-audit` PASSED (no known vulnerabilities);
  `git diff --check` PASSED.

CI at exact implementation head (observed after publication of the
implementation commit, before report commit):

- CI run 34805717866: quality **success**, test **success** (3m25s; log
  line `602 passed in 122.25s` = 597 baseline at base + 5 new race tests,
  real PostgreSQL 17 service), security **success**, container **success**.
- oap run 34805717774: oap-harness **success**.
- Report-head CI: NOT YET OBSERVED AT AUTHORING (the report commit lands
  after this report's content was frozen).

## Acceptance criteria verdict

1. **MET** — pre-change state recorded above (four test names, exact lock
   sequences including deactivate-blackout locking the blackout row not the
   asset row, plain-SELECT nature of both overlap re-checks, exclusion
   constraint `reservation_no_overlap_per_asset`).
2. **MET** — five race tests present, all pass against current product
   code; pre-existing tests byte-identical (diff evidence above); observed
   orderings recorded above.
3. **MET** — full local suite + all quality gates green (modulo the two
   proven local-environment artifacts, which pass in the CI checkout state
   and did pass in CI); all four CI jobs plus oap-harness green at the
   exact implementation head; CI test job count 602 includes the 5 new race
   tests on real PostgreSQL.
4. **N/A** — criterion 2 held truthfully; no violation interleaving was
   observed, so no PARTIAL/FAILED stop was required.
5. **MET** — implementation diff touches only allowed paths:
   `tests/test_reservations_concurrency.py`,
   `oap/orders/020-a-booking-maintenance-races.md`, `oap/active`
   (`git show --stat` at head: 3 files, 615 insertions, 2 deletions; no
   `src/`, no docs, no dependency changes).

## Local-environment artifacts (evidence index, not defects)

- `tests/oap/test_ba38_39_tmux_config.py::Ba39OperationPrereqs::
  test_ba39_strategic_same_prerequisites` FAILED locally with
  `conflicting OAP_ROLE=CODING; refusing` because this coding session's
  launcher exports `OAP_ROLE=CODING` and `oap_launch.py` refuses a
  conflicting role by design. PASSED with the variable unset
  (`env -u OAP_ROLE … pytest …` → 1 passed). CI sets no such variable.
- `tests/oap/test_ba51_52_continuity.py::Ba52HistoricalContinuity::
  test_ba52_real_reports_orders_history_untouched` FAILED locally with
  `2 != 1: pointer must bind exactly one order` because the untracked
  strategy-side `020-a-booking-maintenance-races.FINAL.md` source sits in
  `oap/orders/` next to the published copy on this host. PASSED when only
  the published copy is present (file temporarily moved aside and restored
  byte-identical, sha256 verified) — the CI checkout contains only the
  published copy.
- `oap/bin/check_state.py` likewise reports `state=CORRUPT` only while the
  `.FINAL` source is present locally; `state=ACTIVE_PENDING` in the
  CI-equivalent state.

## Uncertainty, privacy, dependencies, limits

- Non-deterministic race tests sample finite interleavings (25 iterations
  per repeated test across all runs). The invariant is additionally
  structurally grounded in the asset-row-lock serialization + READ COMMITTED
  re-check analyzed above; finite sampling can never prove absence of a
  violating interleaving in general.
- The test 4 "reservation wins" ordering (deactivation commits before the
  reservation's blackout SELECT) was not observed on this host; both
  outcomes remain permitted and both were exercised in other tests.
- No credentials, tokens, pepper, or private data appear in this report,
  the tests, or the diff; test users/passwords are the file's existing
  synthetic sentinels. Disposable infrastructure: container
  `slaif-oap-020a-testpg`, volume `slaif-oap-020a-testpg-data`, port
  127.0.0.1:54330 (loopback only), all owned by this round and slated for
  cleanup; no production/lab/Neumann/real-export contact.
- DHA: `- Decision: NONE` — no CRITICAL append, no human adjudication, no
  gate clearance performed by coding.
- Limits: this round proves the booking-vs-maintenance concurrency
  invariant only; legacy-import-vs-booking concurrency remains explicitly
  deferred per the order. Development merge is strategy's delegated act
  after review; coding has not merged, approved, or enabled auto-merge.
  This report is not a release, deployment, or milestone certificate.
