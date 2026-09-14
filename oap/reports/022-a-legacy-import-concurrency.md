<!-- OAP-META
{
 "kind": "report",
 "id": "022-a",
 "order_path": "oap/orders/022-a-legacy-import-concurrency.md",
 "order_sha256": "f6f85ad9f300d6c6094e52d382088b517b86331d79e351e2942d50c42b64d9a6",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 43,
 "pr_number": 44,
 "branch": "codex/43-oap-022-a-legacy-import-concurrency",
 "implementation_head": "f20e4d29434ae77ba3c082077592360b4e098fe4",
 "base_sha": "2cf9c8a959590f20b04919a42bf9574d35f1dc9a",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "f20e4d29434ae77ba3c082077592360b4e098fe4",
  "runs": [
   {"run_id": 34810745946, "workflow": "CI", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 34810745898, "workflow": "oap", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 022-a report — legacy-import-apply vs ordinary-service concurrency invariant

Order digest: f6f85ad9f300d6c6094e52d382088b517b86331d79e351e2942d50c42b64d9a6
(committed `oap/orders/022-a-legacy-import-concurrency.md`; byte-identical to
the materialized `.FINAL` source — `sha256sum` of both files before the
rename: f6f85ad9f300d6c6094e52d382088b517b86331d79e351e2942d50c42b64d9a6).

Implementation head SHA: f20e4d29434ae77ba3c082077592360b4e098fe4

Report publication commit: SELF

**Result: COMPLETE** — the four scope race tests exist in exactly
`tests/test_legacy_import_concurrency.py` and pass against the current
product code on real PostgreSQL 17 (local disposable `postgres:17`
container; CI `postgres:17` service), separate transactions, no database
mocks. No numbered check exposed a genuine violation of accepted semantics,
so the stop condition was not triggered: no product code was changed and no
test was weakened.

## Reconciliation at start (C-05/C-06/CP-03)

- Ordered reads: root router → `oap/coding-instructions/AGENTS.md` →
  `ARCHITECTURE-for-agents.md` → `OAP-COMMUNICATION-coding-agent.md` →
  exact active order → `SECURITY-CORE.md`/`TESTING-CORE.md` → ordered
  subtree excerpts only: `tests/test_reservations_concurrency.py` (in
  full), `tests/test_legacy_import.py` (fixture/plan construction and
  would_create/apply paths), `src/slaif_reservation/legacy_import/
  importer.py`, `src/slaif_reservation/legacy_import/planner.py`,
  `src/slaif_reservation/legacy_import/mapping.py`,
  `src/slaif_reservation/legacy_import/models.py`,
  `src/slaif_reservation/reservations/services.py`,
  `src/slaif_reservation/reservations/models.py` (source/status/exclusion
  constants), `src/slaif_reservation/reservations/exceptions.py`,
  `src/slaif_reservation/audit/models.py`,
  `reservations/migrations/0001_initial.py` (exclusion constraint name),
  `tests/conftest.py`, `pyproject.toml` (pytest/ruff/mypy config),
  `config/settings/test.py`, `.github/workflows/ci.yml`.
- `oap/active` = exactly `022-a` + LF (6 bytes). Wrapper had already
  consumed the control OK; not consumed again.
- Local main = remote `origin/main` =
  2cf9c8a959590f20b04919a42bf9574d35f1dc9a (= the order's `base_sha`;
  021-a quiescent on top of merged PR #42). Worktree clean except the
  materialized order (untracked
  `oap/orders/022-a-legacy-import-concurrency.FINAL.md`) and the pointer
  (untracked `oap/active`). Fresh round: no local/remote branch and no PR
  for issue #43 (verified with `git ls-remote origin` and `gh pr list`
  before creation); `pr_mode=CREATE_OR_RESUME` resolved to CREATE.
  PR #44 (GitHub-assigned number, recorded truthfully) on the order's
  exact branch `codex/43-oap-022-a-legacy-import-concurrency`, base
  `main`.
- Order hash check: committed order file sha256
  f6f85ad9f300d6c6094e52d382088b517b86331d79e351e2942d50c42b64d9a6 matches
  the `.FINAL` source (bytes preserved by rename; both hashes above).
  DHA declaration: `- Decision: NONE` (no APPEND, no CRITICAL change this
  round).

## Pre-change state (acceptance criterion 1)

Verified by direct source reading at base
2cf9c8a959590f20b04919a42bf9574d35f1dc9a (identical to the implementation
head for `src/`, which is untouched this round).

**`apply_import` (importer.py) exact lock-acquisition sequence.** Outer
`transaction.atomic()`; `_create_batch` inserts the `LegacyImportBatch`
row (mode `apply`, status `applied`) first. Then per `would_create`
record, `_revalidate_for_apply` locks, in this order:
1. `LegacyImportRecord.objects.select_for_update()` filtered by
   `(legacy_source, legacy_id)` → `first()` (row lock on an existing
   record only; `None` → no lock);
2. `Asset.objects.select_for_update().get(pk=item.asset_id)` — the shared
   **asset-row lock**;
3. `UserModel.objects.select_for_update().get(pk=item.user_id)` — user-row
   lock;
4. `importer._asset_allowed(asset)` — pure check
   (`active and reservable and booking_mode == exclusive`); **this is the
   verified import-side pause seam: it executes after the asset-row and
   user-row locks, before the policy lock and the probes** (the order's
   default seam, confirmed at its expected position);
5. `lock_effective_policy(asset)` → `_resolve_effective_policy(
   for_update=True)`: `select_for_update` candidate scan exact-asset →
   parent → global;
6. `_enforce_policy(...)` — **only when
   `appointment.start_at >= timezone.now()`** (future appointments;
   read-only upcoming/concurrent counts). This is the SAR-030 historical
   import exception: the policy gate applies to future appointments only,
   while the overlap/blackout revalidation below is NOT gated on the
   past/future split;
7. `MaintenanceBlackout.objects.select_for_update()...exists()` — locking
   EXISTS probe on overlapping ACTIVE blackout rows;
8. `Reservation.objects.select_for_update()...exists()` — locking EXISTS
   probe on overlapping `confirmed`/`released` reservation rows
   (half-open `[start_at, effective_end_at)` per SAR-006).

Only if still `would_create` does `_create_imported_reservation` run,
inside an inner `transaction.atomic()` **savepoint**: it re-locks asset +
user (`select_for_update`), ORM-saves a `SOURCE_MIGRATION` confirmed
reservation, appends the audit event
(`reservation.created`, `source=migration`, `actor_user=None`), and saves
the `LegacyImportRecord` (`RESULT_IMPORTED`, referencing the reservation).
An `IntegrityError` exiting the savepoint is classified by
`_mark_constraint_conflict` — verified: that function returns
`classification="reservation_conflict"`, i.e. **both** the revalidation
probe path and the IntegrityError path converge on the same
`reservation_conflict` classification; the final batch summary counts
materialize it. (In this two-party same-asset race the probe path is what
executes: the import holds the asset-row lock across probe→insert, and the
booking side cannot commit on that asset without the same lock, so a
committed overlap cannot appear between probe and insert. The named
exclusion `reservation_no_overlap_per_asset` remains the final arbiter for
paths that bypass the asset lock, per SAR-007.)

**`create_reservation` (services.py) lock sequence.** Outer
`transaction.atomic()`; `_lock_principal` (user-row lock) → `_lock_asset`
(**asset-row lock**) → `_validate_asset` → `lock_effective_policy`
(policy-row lock) → `_enforce_policy` (read-only) →
`_raise_if_blackout_overlap` (**module-level seam called AFTER the
principal→asset→policy locks**; plain SELECT; the verified booking-side
pause seam) → `_raise_if_asset_overlap` (plain SELECT) → insert inside an
inner `transaction.atomic()` savepoint; `IntegrityError` translates to
`RESERVATION_CONFLICT` **only** for the exact named exclusion
`reservation_no_overlap_per_asset` (`_is_named_reservation_constraint`,
SAR-007); then `append_audit_event` (`reservation.created`,
`source=web` by default, `actor_user=principal`).

**`create_blackout` (services.py) lock sequence.** Outer
`transaction.atomic()`; `_lock_staff_actor` (user-row lock) → `_lock_asset`
(**asset-row lock**) → `overlapping_blocking_reservations` (plain SELECT
on confirmed/released half-open overlap) → raise `BLACKOUT_CONFLICT` iff
overlaps exist and `confirmed_overlap` is not `True` → insert blackout
(`active=True`) + `append_audit_event` (`maintenance_blackout.created`,
`source=admin`, actor=staff).

**Shared asset-row-lock serialization point.** All three paths hold the
same asset-row lock across their check→insert windows; the race therefore
serializes on that row, with the advisory SELECT checks / locking probes /
named GiST exclusion as layered final arbiters (SAR-007/SAR-009).

**Plan-construction seam reused.** `importer.build_plan` is a verified
thin re-export (`def build_plan(export, mapping): return
plan_import(export, mapping)`); the new tests call `plan_import` directly
with `parse_synthetic_export` + `load_mapping` over the same
`slaif-smartscheduling-synthetic-v1` / `slaif-smartscheduling-mapping-v1`
fixture format as `tests/test_legacy_import.py` (`write_export`/
`write_mapping` conventions), parameterized per iteration with fresh
`res-<i>` / `person-<i>` / `appointment-<i>` legacy IDs and fresh
asset/user identifiers so iterations are independent. Future
(`confirmed`-status) policy-valid appointments classify `would_create`;
asserted in `build_plan` before each race.

**Exclusion constraint.** `reservation_no_overlap_per_asset`
(`reservations/migrations/0001_initial.py:186`), matching
`Reservation.EXCLUSION_CONSTRAINT_NAME`.

## New race tests (acceptance criterion 2)

Exactly one new file: `tests/test_legacy_import_concurrency.py`
(608 lines, 4 tests, all `@pytest.mark.django_db(transaction=True)`,
per-thread `close_old_connections`, real separate PostgreSQL
transactions, no database mocks). The `run_parallel` barrier harness is an
equivalent local copy of the 020-a harness (the suite has no
cross-test-module imports, so the order's authorized fallback was used);
the pause-after-lock pattern mirrors `tests/test_reservations_concurrency.py`.

1. `test_apply_vs_reservation_race_exactly_one_commits_across_repeats` —
   scope item 1. Five fresh iterations of barrier-parallel
   `apply_import` (one `would_create` item, window R, asset X, mapped user
   U1) vs `create_reservation` (asset X, user U2, window R). Per
   iteration: exactly one committed blocking reservation on X/R (never
   both); import-lost ⇒ `reservation_conflict` in the batch summary with
   NO migration row, NO `LegacyImportRecord` row and NO migration audit
   for that asset; booking-lost ⇒ `RESERVATION_CONFLICT` with no row; the
   single committed row carries exactly one success audit
   (`reservation.created`) — import win: `source=migration`, actor
   `None`, `LegacyImportRecord` `RESULT_IMPORTED` referencing the row;
   booking win: `source=web`, actor=U2.
2. `test_import_wins_reservation_blocked_on_asset_lock_then_conflicts` —
   scope item 2 (deterministic import-wins). Seams: import side paused at
   `importer._asset_allowed` (verified after the asset-row lock); booking
   side paused at `services._raise_if_blackout_overlap` (the order's
   prescribed booking-side seam, verified after the booking's
   principal→asset→policy locks). Sequence: import acquires the asset-row
   lock and pauses; booking blocks on the asset-row lock (asserted alive);
   import released, its apply returns with the item classified
   `imported`, and at that moment exactly one (migration) reservation is
   committed — the booking cannot commit before its gated release;
   booking then passes the asset lock, pauses at the advisory seam, is
   released, and loses with `RESERVATION_CONFLICT` at
   `_raise_if_asset_overlap`. Final state: exactly one reservation on
   X/R, `SOURCE_MIGRATION`, exactly one audit (`source=migration`, actor
   `None`), `LegacyImportRecord` `RESULT_IMPORTED` referencing it, batch
   summary `imported=1`.
3. `test_reservation_wins_import_blocked_on_asset_lock_then_conflicts` —
   scope item 3 (deterministic booking-wins, mirror). Booking side paused
   at `services._raise_if_blackout_overlap` (verified after the booking's
   asset-row lock); the import thread is unpatched and blocks on the real
   database asset-row lock (asserted alive) while the booking holds it.
   Release; booking commits. Import then classifies its item
   `reservation_conflict` (batch summary `reservation_conflict=1`,
   `imported=0`) with NO migration row, NO import audit and NO
   `LegacyImportRecord` row. Final state: exactly one reservation on X/R,
   the booking side's (`source=web`, actor=U2) with its single success
   audit.
4. `test_apply_vs_blackout_race_never_leaves_migration_over_active_blackout`
   — scope item 4. Five fresh iterations of barrier-parallel
   `apply_import` (one `would_create` item, window M, asset X) vs
   `create_blackout` (asset X, range overlapping M,
   `confirmed_overlap=False`, staff actor). Per iteration the final-state
   invariant holds: NEVER a committed migration reservation overlapping
   X/M while an ACTIVE blackout overlaps X/M —
   `(reservation_count, blackout_count) ∈ {(1,0), (0,1)}`; blackout-first
   ⇒ item classified `blackout_conflict` with no reservation row, no
   import artifacts, and the blackout's single creation audit;
   import-first ⇒ `BLACKOUT_CONFLICT` with no blackout row on the fresh
   asset and the migration row's single success audit.

**Verified seam choices and deviations (recorded per the order's own
"verify, do not assume" clause).**
- Test 2: the order's literal sentence "the import side must complete
  while the booking thread is still blocked on the asset row lock" cannot
  hold literally under the verified code: `_revalidate_for_apply`
  unconditionally takes the SAME asset-row lock (step 2 above) before the
  import writes, so the import cannot complete while the booking HOLDS
  that lock. The test therefore forces the import-wins ordering by
  additionally pausing the import side at the verified seam
  `importer._asset_allowed`; the order's prescribed booking-side pause
  (`services._raise_if_blackout_overlap`) is kept and gates the booking's
  post-lock advisory stage. The strongest true statement is asserted: at
  the instant the import apply returns `imported`, exactly one
  (migration) reservation is committed and the booking has not committed
  (it cannot pass the gated seam before release), and it then loses with
  `RESERVATION_CONFLICT`.
- Test 3: the order's default import-side seam
  (`importer._asset_allowed`) is verified to execute AFTER the asset-row
  lock, so pausing the import there would make the import the lock holder
  (the import-wins direction) — contradicting the item's own assertion
  that "the import thread blocks while the booking holds the asset
  lock". Deterministic booking-wins requires the booking side to hold the
  lock while paused; the verified booking-side seam
  `services._raise_if_blackout_overlap` (after the booking's asset-row
  lock) is used, mirroring the 020-a
  `test_blackout_wins_reservation_blocked_on_asset_lock_then_conflicts`
  pattern. The import thread blocks on the real database asset-row lock;
  no import-side patch is applied.
- "LegacyImportRecord classified reservation_conflict /
  blackout_conflict" (order items 1/3/4): verified — the code writes no
  per-item DB record row for non-imported items (records are created only
  by `_create_imported_reservation`, `RESULT_IMPORTED`); the losing
  classification is materialized in the final in-plan record and in the
  durable `LegacyImportBatch.summary` counts, which the tests assert
  (`reservation_conflict=1`/`blackout_conflict=1`, `imported=0`), together
  with the absence assertions (no migration row, no `LegacyImportRecord`
  row, no migration audit for the lost item).

**Observed orderings in the non-deterministic iterations (items 1 and 4;
local, disposable PostgreSQL 17, 3 independent runs × 5 fresh iterations
each = 15 iterations per race, via `-s` captured prints):**
- Item 1 (apply × create_reservation): `booking_wins` in all 15
  iterations (3 runs: 5/5, 5/5, 5/5).
- Item 4 (apply × create_blackout): `blackout_wins` in all 15 iterations
  (3 runs: 5/5, 5/5, 5/5).
- Structural cause (recorded truthfully): the import path performs the
  batch INSERT and the import-record probe BEFORE reaching the shared
  asset-row lock, while the booking/blackout paths reach the same lock
  after fewer statements; under barrier start the service side therefore
  reaches the asset-row lock first on every iteration of this fast local
  DB. A scratch probe (6 iterations, alternating call order) confirmed
  the skew is structural, not list-order dependent (6/6 `booking_wins`
  both orders; the scratch file was deleted and is not in the diff).
  The import-wins interleaving for apply × create_reservation is
  nonetheless proven deterministically by test 2. For item 4 the
  `import_wins` branch is not sampled by the barrier race; its
  final-state assertions mirror test 2's import-wins state, and the
  blackout-conflict side of the invariant (`reservation committed first
  ⇒ create_blackout raises BLACKOUT_CONFLICT`, no blackout row) is
  independently established by the pre-existing 020-a test
  `test_reservation_wins_blackout_blocked_on_asset_lock_then_conflicts`.
- No iteration observed a violation: never two committed blocking
  reservations, never a committed migration row over an ACTIVE blackout,
  never an audit for a rolled-back import, never two success audits for
  one row. The stop condition (genuine violation ⇒ stop, no fix, no
  weakening) was NOT triggered.

Pre-existing-test byte-identity (proven by diff):
`git diff 2cf9c8a959590f20b04919a42bf9574d35f1dc9a
f20e4d29434ae77ba3c082077592360b4e098fe4 --stat -- tests/` shows exactly
one file — `tests/test_legacy_import_concurrency.py` (+608; 608
insertions, 0 deletions); the whole implementation commit shows exactly 3
files — the new test, `oap/active` (+1) and
`oap/orders/022-a-legacy-import-concurrency.md` (+253) — 862 insertions,
0 deletions. No `src/`, no docs, no dependency, no governance change.

## Stop condition (acceptance criterion 4)

NOT triggered. Every invariant held in every iteration (local and CI); no
product change was made and no test was weakened. (Had it triggered:
PARTIAL/FAILED report with the exact failing race, minimal repro, no
product fix — strategy would decide the repair round.)

## Gates (acceptance criterion 3)

Local, at implementation head f20e4d29434ae77ba3c082077592360b4e098fe4
(disposable owned `postgres:17` container `slaif-022a-testdb`,
loopback-only 127.0.0.1:54330, matching `.env`
`TEST_DATABASE_URL`; migrations, bootstrap import and
`purge_expired_idempotency_records` applied to the disposable DB before
the operational gates; working tree identical to the committed tree at
that head):

- Focused: `uv run --env-file .env pytest
  --ds=slaif_reservation.config.settings.test
  tests/test_legacy_import_concurrency.py` → **4 passed** (4.12s),
  PASSED; repeated 3 more times consecutively (4 passed each time), with
  `-s` ordering prints captured above.
- Full: `env -u OAP_ROLE uv run --env-file .env pytest
  --ds=slaif_reservation.config.settings.test` → **609 passed** (0
  failed, 0 skipped) in 143.47s = 605 baseline at the 021-a head + 4 new
  race tests, PASSED. (See Local-environment notes for `OAP_ROLE`.)
- `uv sync --locked --all-groups` PASSED (68 packages checked).
- `uv run ruff check .` PASSED; `uv run ruff format --check .` PASSED.
- `uv run mypy src` PASSED (119 source files, strict).
- `uv run --env-file .env python manage.py check` PASSED (0 issues).
- `uv run --env-file .env python manage.py makemigrations --check
  --dry-run` PASSED (no changes).
- `uv run --env-file .env python manage.py operational_check` PASSED
  (database/migrations/static/bootstrap/idempotency_cleanup_command/
  operational all ok).
- `uv run --env-file .env python manage.py spectacular --validate
  --fail-on-warn` PASSED (rc=0).
- `uv run pip-audit` PASSED (no known vulnerabilities).
- `git diff --check` PASSED.

CI at the exact implementation head f20e4d29434ae77ba3c082077592360b4e098fe4
(observed after push of the implementation commit, before this report was
written; PR #44):

- CI run 34810745946: quality **success**, test **success** (log line
  `609 passed in 127.47s`, with the line `tests/test_legacy_import_
  concurrency.py ....` showing the four new race tests running on the
  real PostgreSQL 17 service and counted in the pass total), security
  **success**, container **success**.
- oap run 34810745898: oap-harness **success**.
- Report-head CI: NOT YET OBSERVED AT AUTHORING (the report commit lands
  after this report's content was frozen).

## Local-environment notes (evidence-index caveats)

- The coding launcher exports `OAP_ROLE=CODING` in the process
  environment; the path-gated OAP harness test
  `tests/oap/test_ba38_39_tmux_config.py::Ba39OperationPrereqs::
  test_ba39_strategic_same_prerequisites` rejects a strategic launch when
  a conflicting `OAP_ROLE` leaks into its subprocess. With `OAP_ROLE`
  unset the file passes 12/12, and the full 609-test run above (clean
  environment) is green. CI runs in a clean environment; the oap-harness
  CI job at the implementation head is green. This is an environment
  artifact of this launcher, not a product or test defect; no OAP
  harness file was touched (forbidden by the order).
- Local evidence used a disposable PostgreSQL 17.11 container owned by
  this round (loopback only); the authoritative concurrency evidence is
  the CI `postgres:17` service run at the exact head, per SAR-032.

## SAR → check → test mapping (evidence matrix)

Actual revision for every row:
f20e4d29434ae77ba3c082077592360b4e098fe4. "T1"–"T4" = the four tests in
`tests/test_legacy_import_concurrency.py`.

| SAR | Check | Test |
| --- | --- | --- |
| SAR-001 | Exactly one committed blocking reservation per race on the shared asset/window; loser classified, no second row | T1, T2, T3, T4 |
| SAR-006 | Blocking probe/window uses `confirmed`/`released` half-open `[start_at, effective_end_at)` (asserted counts use the same filter) | T1, T3, T4 |
| SAR-007 | Booking loses via `RESERVATION_CONFLICT` (advisory or exact named-exclusion translation); import-side `IntegrityError` path verified to map to `reservation_conflict` (unreachable in this race due to the shared asset-row lock) | T1, T2 |
| SAR-009 | Consistent lock ordering across import/web paths proven by deterministic lock-hold/lock-wait sequences (import-wins, booking-wins, blackout races); atomic audited lifecycle — single success audit per committed row, migration audit without actor, no audit for rolled-back imports | T1–T4 |
| SAR-020 | Blackout-first ⇒ `blackout_conflict`, no row; import-first ⇒ `BLACKOUT_CONFLICT`, no blackout row; never migration row over ACTIVE blackout | T4 |
| SAR-028 | Synthetic fixture format only; local files; no live export, no real SmartScheduling data | T1–T4 (fixture writers) |
| SAR-029 | Apply revalidates current state transactionally; final-result batch summary counts reflect the conflict | T1, T3, T4 |
| SAR-030 | Future appointment (policy gate applies); overlap/blackout revalidation not past/future-gated (verified in source; fixture uses future `confirmed` appointment) | T1–T4 |
| SAR-032 | Full evidence at the exact head (this report + observed CI at f20e4d2) | — |

## Acceptance criteria verdict

1. **MET** — pre-change state recorded above: the importer's exact
   lock-acquisition sequence (including the locking EXISTS probes, the
   inner savepoint around the write, the IntegrityError →
   `reservation_conflict` mapping via `_mark_constraint_conflict`, and
   that the policy gate applies only to future appointments while
   overlap/blackout revalidation is not gated), the
   `create_reservation` lock sequence, the plan-construction seam reused
   (`build_plan` = `plan_import` re-export; synthetic v1 fixture format),
   the verified pause seam(s) and their call positions, and the shared
   asset-row-lock serialization point.
2. **MET** — the four new race tests are present in exactly
   `tests/test_legacy_import_concurrency.py`, pass against the current
   product code (local 4/4 repeated; full suite 609 passed; CI 609
   passed), and every pre-existing test file is byte-identical (diff
   evidence above). Observed orderings recorded truthfully (15/15
   `booking_wins` item 1; 15/15 `blackout_wins` item 4; structural cause
   and coverage of the unsampled import-wins direction documented).
3. **MET** — full pytest suite, ruff check, ruff format --check, mypy,
   makemigrations --check --dry-run, manage.py check, operational_check,
   spectacular --validate --fail-on-warn and pip-audit all green at the
   exact implementation head locally; CI quality/test/security/container
   (and oap-harness) all success at head
   f20e4d29434ae77ba3c082077592360b4e098fe4, with the CI test job showing
   the four new race tests running (counted in `609 passed`, real
   PostgreSQL 17 service).
4. **MET (not triggered)** — no check exposed a genuine violation; no
   product change, no weakened test.
5. **MET** — the diff touches only allowed_paths:
   `tests/test_legacy_import_concurrency.py`,
   `oap/orders/022-a-legacy-import-concurrency.md`, `oap/active`
   (implementation) plus this report file (report-only commit).

## Privacy / dependencies / DHA / limits

- No credentials, tokens, peppers, verifiers, passwords, cookies, CSRF
  values, raw request payloads, private exports, physical locators, auth
  homes or sidecar traces appear in the diff, this report, or any log
  artifact; fixtures are synthetic with `not-a-secret` placeholder
  passwords only (existing test convention).
- No new or removed dependencies; `uv.lock` untouched.
- DHA: `Decision: NONE` — no CRITICAL entry created, appended or
  dispositioned by this round.
- Limits: the non-deterministic races sample real interleavings but the
  barrier start on this host strongly favors the service side (documented
  above); the deterministic tests prove both directions for
  apply × create_reservation and the blackout invariant holds per
  iteration regardless of direction. Report-head CI is not observed at
  authoring and is not claimed. This report is evidence, not strategic
  acceptance; merge remains strategy's delegated act after review.
