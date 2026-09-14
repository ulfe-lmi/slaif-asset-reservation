<!-- OAP-META
{
 "id": "022-a",
 "round": "a",
 "base_sha": "2cf9c8a959590f20b04919a42bf9574d35f1dc9a",
 "issue_number": 43,
 "branch": "codex/43-oap-022-a-legacy-import-concurrency",
 "pr_mode": "CREATE_OR_RESUME",
 "previous_round": null,
 "allowed_paths": [
  "tests/test_legacy_import_concurrency.py",
  "oap/orders/022-a-legacy-import-concurrency.md",
  "oap/active",
  "oap/reports/022-a-legacy-import-concurrency.md"
 ],
 "forbidden_resources": [
  "any change under src/ (no product behavior, model, service, importer, API, template, settings, or migration changes; this round is evidence-only)",
  "any change to legacy-import apply semantics, reservation/blackout/policy service semantics, lock behavior, or interval rules",
  "any change to tests other than the one named new test file (all existing test files byte-identical)",
  "any weakening, skipping, or loosening of a race test to make it pass",
  "any change under docs/, deploy/, data/, .github/, oap/ helpers or workflows (no OAP expansion)",
  "new dependencies or removed dependencies",
  "deployment of any kind; real/production databases; real lab/Neumann machines; real SmartScheduling data (synthetic fixture format only)",
  "credentials, auth files, sessions, tokens, auth homes",
  "DNS/TLS/firewall changes, public exposure, repository visibility or branch-protection changes",
  "any mutating GitHub operation except pushing this branch and opening this objective's PR",
  "merging or auto-merging any PR (merge is strategy's delegated act after review)",
  "ICA activity, milestone completion claims, canary work, or work from other drafts/objectives",
  "model provider endpoints other than the configured qwen-neumann role profile"
 ]
}
-->

# 022-a — Prove the legacy-import-apply vs ordinary-service concurrency
# invariant under separate transactions

## Goal

The last unproven cross-service race of the implemented product (A-06:
"concurrency across policy changes, blackout creation, API idempotency,
legacy apply and ordinary booking needs consistent locking and
boundary-faithful tests"; A-11: "concurrent import and ordinary service
lock interaction requires real qualification"). The importer's apply path
revalidates and writes SOURCE_MIGRATION reservations directly; ordinary
bookings and staff blackouts run concurrently in production-shaped
operation. This round adds barrier-controlled separate-transaction race
tests proving: a concurrent apply-vs-booking interleaving never yields two
committed blocking reservations on the same asset/window (exactly one
side commits; the loser is classified reservation_conflict /
constraint_conflict on the import side or loses with RESERVATION_CONFLICT
on the booking side, with exactly one success audit for the committed row);
both deterministic orderings hold; and apply-vs-blackout never leaves a
committed migration reservation overlapping an ACTIVE unacknowledged
blackout. Evidence-only: if a test exposes a genuine violation of
accepted semantics, the round stops and reports the exact interleaving
(no product fix in this round, no weakened test).

## Durable provenance and requirements

- H: in-session human principal instruction 2026-09-14 (reaffirmed) —
  continue the autonomous strategy -> coding -> review -> merge loop;
  smallest product PR that materially advances the real reservation-system
  MVP; no canary work, no OAP expansion, no ICA.
- E: origin/main = local main = 2cf9c8a959590f20b04919a42bf9574d35f1dc9a
  (021-a quiescent, INACTIVE, CI 5/5 green at report head
  06f4517838de6152309eb455599bbf72c8e9f51d). 605 tests passed at the 021-a implementation
  head. Importer lock sequence (source-observed 2026-09-14, verify):
  apply_import opens an outer transaction, creates the batch, then per
  would_create item calls _revalidate_for_apply which locks in order:
  existing LegacyImportRecord (select_for_update), asset row
  (select_for_update), user row (select_for_update), effective policy
  (lock_effective_policy / _resolve_effective_policy(for_update=True)),
  then locking EXISTS probes on overlapping ACTIVE blackout rows and on
  overlapping confirmed/released reservation rows; only if still
  would_create does _create_imported_reservation re-lock asset + user and
  ORM-save a SOURCE_MIGRATION confirmed reservation plus audit event plus
  record, inside an inner transaction.atomic() savepoint whose
  IntegrityError exit classifies the item constraint_conflict
  (_mark_constraint_conflict). create_reservation (020-a report): locks
  principal -> asset -> policy, then plain-SELECT advisory checks
  (_raise_if_blackout_overlap, _raise_if_asset_overlap), then insert with
  the GiST exclusion reservation_no_overlap_per_asset as final arbiter and
  exact named-exclusion translation only. BOTH paths therefore hold the
  asset-row lock across their check->insert window.
- A: SAR-001 (one reservation authority; exclusivity across all write
  paths), SAR-006 (confirmed/released block [start_at,
  effective_end_at) — the importer's blocking probe uses exactly those
  statuses), SAR-007 (named GiST exclusion final arbiter; only the exact
  named exclusion failure translates to a booking conflict; the import
  side maps IntegrityError to constraint_conflict), SAR-009 (atomic
  audited lifecycle; consistent lock ordering across web/API/management/
  import paths), SAR-028 (synthetic migration boundary — fixture format
  only, no live export), SAR-030 (historical import exception — policy
  enforcement applies to future appointments only; the overlap/blackout
  revalidation is NOT gated on the past/future split), SAR-032 (evidence
  before readiness).
- C: S-12 (one proof-sized objective), S-15 (report boundary), S-19 (real
  separate-transaction PostgreSQL boundaries, not mocks), S-16/S-17
  (exact-head review; delegated merge).
- Reconciliation: the legacy-import-vs-booking concurrency scope,
  EXPLICITLY DEFERRED in the 019-a and 020-a orders (requirement recorded,
  not dropped), is picked up here as the next smallest product PR after
  021-a. No other deferred scope enters this round.

## Current reconciled state and prerequisites

- Base main (local and remote): 2cf9c8a959590f20b04919a42bf9574d35f1dc9a.
  Worktree must be clean on main before starting; `oap/active` absent
  (INACTIVE).
- Fresh round: no local/remote branch codex/43-oap-022-a-legacy-import-
  concurrency, no PR for issue #43 (verify with git ls-remote and gh
  before creation); pr_mode CREATE_OR_RESUME resolves to CREATE. The PR
  number is GitHub-assigned; record it truthfully.
- Known facts (verify, do not assume): the 020-a test module
  tests/test_reservations_concurrency.py provides the run_parallel
  barrier harness (threading.Barrier, per-thread connections,
  transaction=True) and the pause-after-lock pattern (monkeypatch a
  service-internal helper to signal a threading.Event after the lock is
  held, block until release); services._raise_if_blackout_overlap is the
  module-level seam called by create_reservation AFTER the asset+policy
  locks (import-wins pause point for the booking side);
  importer._asset_allowed is called by _revalidate_for_apply AFTER the
  asset row lock is held (booking-wins pause point for the import side —
  verify its exact call position; if it is not after the asset lock,
  choose another verified module-level seam inside _revalidate_for_apply
  that provably executes after the asset lock, and record the choice in
  the report); tests/test_legacy_import.py contains the synthetic
  export/mapping construction helpers and a plan-construction seam
  (build_plan) producing would_create items for future, policy-valid,
  mapped appointments — verify and reuse the exact seam rather than
  inventing a new fixture format.

## Ordered read set

Standard compact read set, plus: tests/test_reservations_concurrency.py
(in full — harness, pause pattern, fixtures, existing assertions),
tests/test_legacy_import.py (synthetic export/mapping/plan construction
and the would_create path), src/slaif_reservation/legacy_import/importer.
py (apply_import, _revalidate_for_apply, _create_imported_reservation,
_mark_constraint_conflict, _existing_record_classification,
_asset_allowed, plan classification constants),
src/slaif_reservation/reservations/services.py (create_reservation,
create_blackout, _raise_if_blackout_overlap, lock helpers,
_resolve_effective_policy), the LegacyImportBatch/LegacyImportRecord
models (fields, RESULT_*, PLAN_CLASSIFICATIONS), and the reservation
exclusion constraint name in the migrations.

## Scope and allowed paths

One NEW test file, tests/test_legacy_import_concurrency.py, real
PostgreSQL separate transactions (transaction=True, per-thread
connections), no mocks of the database. Reuse the run_parallel harness
and pause-after-lock pattern (import from the existing test module if
clean under the suite's import conventions; otherwise an equivalent local
copy in the new file — the existing file stays byte-identical). Each
iteration uses FRESH asset/user/appointment identifiers so iterations are
independent:

1. Non-deterministic apply x create_reservation race: barrier-parallel
   apply_import(plan with exactly one would_create item, window R on
   asset X, mapped user U1) and
   create_reservation(asset=X, user=U2, window R). Repeat across 5
   fresh iterations to sample interleavings. Per iteration assert:
   EXACTLY ONE committed blocking reservation on X/R (never both
   committed); if the import side lost: its LegacyImportRecord is
   classified reservation_conflict (or constraint_conflict — record
   which occurred, if the latter include the exact IntegrityError
   mapping) with NO migration reservation row and NO import audit
   event; if the booking side lost: RESERVATION_CONFLICT raised with no
   row; the single committed row has exactly one success audit event
   (source migration or web/api respectively). Record which orderings
   were actually observed across the iterations (truthful sampling
   note in the report).
2. Deterministic import-wins ordering: monkeypatch
   services._raise_if_blackout_overlap to signal an event (booking holds
   the asset lock) and block until release; run the two threads; the
   import side must complete (its apply returns with the item classified
   imported) while the booking thread is still blocked on the asset row
   lock; release; assert the booking side lost with RESERVATION_CONFLICT
   (or the exact named-exclusion translation). Final state: exactly one
   reservation on X/R, SOURCE_MIGRATION, with its audit event present
   (source migration, no actor user) and the import record
   RESULT_IMPORTED referencing it.
3. Deterministic booking-wins ordering (mirror): monkeypatch the
   verified import-side pause seam (default importer._asset_allowed,
   see Known facts) to signal + block; run the two threads; assert the
   import thread blocks while the booking holds the asset lock; release;
   assert the import item is classified reservation_conflict with NO
   migration reservation row, NO import audit event, and the batch
   summary count reflecting the conflict; final state: exactly one
   reservation on X/R, the booking side's, with its audit event.
4. Non-deterministic apply x create_blackout race: barrier-parallel
   apply_import(one would_create item, window M on asset X) and
   create_blackout(asset=X, range overlapping M, confirmed_overlap
   False, staff actor). Repeat across 5 fresh iterations. Per iteration
   assert the final-state invariant: NEVER a committed migration
   reservation overlapping X/M while an ACTIVE blackout overlaps X/M.
   If the blackout committed first: the import item is classified
   blackout_conflict with no reservation row. If the import committed
   first: create_blackout raised BLACKOUT_CONFLICT (no blackout row, or
   a consistent prior state) — record the exact observed outcome.
   Record which orderings were actually observed (truthful sampling
   note).

Non-negotiable: if any test exposes a genuine violation (both committed
on an unacknowledged overlap; a committed migration reservation over an
active blackout; an audit event for a rolled-back import; two success
audits for one row), do NOT change product code and do NOT weaken the
test. Stop, and publish a truthful PARTIAL/FAILED report naming the exact
race, observed vs expected, and the minimal reproduction; strategy
decides the repair round.

## Non-goals

- No product behavior change of any kind; no src/ change; no docs change.
- No policy-vs-booking, API-idempotency-vs-booking, or web-vs-web race
  re-testing (already evidenced by pre-existing and 020-a tests).
- No legacy-import parser/mapping/planner changes or new fixture
  formats; synthetic fixture format only, no live export, no real
  SmartScheduling data.
- No OAP/governance changes, no canary work, no ICA, no milestone claim.
- No deployment, no real data, no lab/Neumann contact.
- No merge, auto-merge, approval or settings change.

## Numbered acceptance criteria

1. The report records the pre-change state: the importer's exact
   lock-acquisition sequence (including the locking EXISTS probes, the
   inner savepoint around the write, the IntegrityError ->
   constraint_conflict mapping, and that the policy gate applies only to
   future appointments while overlap/blackout revalidation is not
   gated), the create_reservation lock sequence, the plan-construction
   seam reused, the verified pause seam(s) and their call positions, and
   the shared asset-row-lock serialization point.
2. The new race tests (scope items 1–4) are present in exactly
   tests/test_legacy_import_concurrency.py, pass against the current
   product code, and every pre-existing test file is byte-identical
   (prove by diff). The report records which orderings were observed in
   the non-deterministic iterations (items 1 and 4).
3. Full pytest suite, quality gates (ruff check, ruff format --check,
   mypy), makemigrations --check --dry-run, manage.py check,
   operational_check, spectacular --validate --fail-on-warn, and the CI
   container + security (pip-audit) jobs all green at the exact
   implementation head; the CI test job shows the new race tests running
   (counted in the pass total, on real PostgreSQL).
4. If criterion 2 cannot hold truthfully: a PARTIAL/FAILED report with
   the exact failing race (observed vs expected, minimal repro), no
   product change, no weakened test.
5. The diff touches only allowed_paths.

## Deferred human adjudication

- Decision: NONE
