<!-- OAP-META
{
  "kind": "report",
  "id": "049-a",
  "order_path": "oap/orders/049-a-booking-eligibility.md",
  "order_sha256": "e7cc60381ab705fd508201453ad7e5a2488f9fffcaf06dd14b45c53278980d63",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 101,
  "pr_number": 102,
  "branch": "codex/101-oap-049-a-booking-eligibility",
  "implementation_head": "5fb13875f90c00bd222125856fb5e1f1f13d2350",
  "base_sha": "12947e9b368445eeb4a48416421626224b49f4dc",
  "result": "PARTIAL",
  "observed_implementation_ci": {
    "observed_head": "5fb13875f90c00bd222125856fb5e1f1f13d2350",
    "runs": [
      {
        "run_id": 39072679355,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      },
      {
        "run_id": 39072679343,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "success",
          "container": "success",
          "test": "failure"
        }
      }
    ],
    "test_job_summary": "2 failed, 1173 passed, 1 warning in 564.18s (0:09:24)",
    "failed_tests": [
      "tests/test_legacy_import.py::test_apply_revalidates_missing_future_policy_inside_transaction",
      "tests/test_restore_drill.py::RestoreDrillRoundTrip::test_real_round_trip_verifies_and_cleans_up"
    ],
    "warning": "tests/test_product_entry.py:558 UserWarning: Overriding setting DATABASES can lead to unexpected behavior. (pre-existing, unrelated)"
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 049-a — one authoritative booking capability and exact-asset group eligibility

Implementation head SHA: 5fb13875f90c00bd222125856fb5e1f1f13d2350
Report publication commit: SELF

PARTIAL for the 049-a A16/SAR-049 booking-eligibility slice (D0). Issue
101, PR #102 (created this round, body carries `Closes #101`), exact base
`12947e9b368445eeb4a48416421626224b49f4dc` (merged 048/PR #100). The
implementation is complete and pushed at the implementation head above, but
the normal FULL CI at that head is NOT fully green: the `test` job failed
with exactly 2 failures, both fixture-grant gaps in pre-existing
positive-booking fixtures (one in a file outside this order's allowed
paths). Both failures are recorded below as unaccepted; no gate, predicate,
planner/apply behavior, or new-test change was made to force green CI.
Quality/security/container and oap-harness passed at the implementation
head. No merge, no auto-merge, no CRITICAL mutation, no deployment, no
real DB/data/exposure operation.

## Unaccepted CI failures (exact)

CI run 39072679343 (workflow CI, head
`5fb13875f90c00bd222125856fb5e1f1f13d2350`), job `test` FAILED
(2026-10-17T21:51:27Z → 2026-10-17T22:01:52Z, 10m25s):
`2 failed, 1173 passed, 1 warning in 564.18s (0:09:24)`.

1. `tests/test_legacy_import.py::test_apply_revalidates_missing_future_policy_inside_transaction`
   — AssertionError at line 509: `assert result.counts["policy_not_configured"] == 1`
   got 0. Root cause: this pre-existing positive fixture's mapped future
   appointment user has no explicit `reservations.book_assets` grant
   (pre-049 fixtures predate the gate), so the shared future-import booking
   classification (code `booking_not_authorized`, existing `error`
   classification) surfaces before the apply-time policy revalidation the
   test pins. The order anticipates exactly this class ("Many old positive
   fixtures need explicit book grant"), but `tests/test_legacy_import.py`
   is NOT in this order's allowed_paths, so the fixture grant cannot be
   added in this round: scope blocker, not a gate-design rejection.
2. `tests/test_restore_drill.py::RestoreDrillRoundTrip::test_real_round_trip_verifies_and_cleans_up`
   — `django.core.management.base.CommandError: point-in-time probe failed:
   The principal is not authorized to book this asset.`
   (src/slaif_reservation/api/management/commands/restore_drill.py:538).
   Root cause: the restore drill's point-in-time probe principal lacks the
   booking grant. This round's fixture adaptation of
   `tests/test_restore_drill.py` (an allowed path) granted the grant to the
   drill's importing member only; the probe uses a different principal. The
   restore drill cannot run on the local host (no `pg_dump`/`pg_restore`),
   so this adaptation was never locally verified; CI exposed the gap.

All other 1173 CI tests passed at the implementation head, including every
new test from this round (52 in `tests/test_booking_authorization.py`,
1 in `tests/test_booking_access_upgrade.py`, 5 in
`tests/browser/test_booking_authorization_browser.py`) and the adapted
existing fixtures. The single warning is the pre-existing, unrelated
`test_product_entry.py:558` DATABASES-override `UserWarning`.

## Acceptance evidence (order items 1-9)

1. **Model + one new forward migration.** PASSED (local + CI).
   `Asset.booking_restricted` (Boolean, default False) and
   `Asset.allowed_booking_groups` (M2M to existing `auth.Group`,
   `related_name="allowed_booking_assets"`); only new migration
   `assets/0003_booking_access.py` (deps: assets 0002, auth 0012).
   `manage.py makemigrations --check --dry-run` → "No changes detected"
   (local, owned env). Real-PG populated upgrade
   (`tests/test_booking_access_upgrade.py`, 1 passed locally and in CI):
   assets pinned at 0002 with users/groups/policies/reservations/blackouts/
   audit/tokens → leaf migrations; every asset unrestricted with empty
   group list, every other row's identity/content preserved, idempotent
   re-run, post-upgrade defaults unrestricted. No merged migration,
   reservation model or exclusion constraint touched.
2. **Shared predicate + row-locked authoritative gate.** PASSED (local + CI).
   `src/slaif_reservation/assets/authorization.py` (new):
   `user_can_book_asset` / `batch_asset_booking_states` / `user_group_ids`
   on `has_reservation_permission(user, BOOKING_BASELINE_PERMISSION)` +
   actual group membership; no caches; `asset=None` = global check only;
   restricted+empty fails closed; superusers keep `has_perm` but still need
   an allowed group on restricted assets; staff/unrelated Administration
   permissions never bypass; only the booked asset is checked. Enforced in
   `create_reservation` after the fresh principal + asset row locks, before
   any write (`BOOKING_NOT_AUTHORIZED = "booking_not_authorized"`).
   Owner list/inspect/cancel/release unchanged after grant/membership loss
   (covered by new tests, including via owned-token scopes).
3. **Browser GET/POST denial + eligibility display.** PASSED (local + CI).
   Direct GET on an ineligible reserve page redirects with the message;
   forged POSTs create nothing (server + raw `page.request` POST with
   session CSRF). List per-row "You can book" column; detail "Booking
   access" line with reason; Reserve action only when eligible; reservable
   filter help corrected to the asset-flag wording; no group names or
   account metadata on member surfaces (asserted in tests).
4. **Bearer auth before idempotent replay.** PASSED (local + CI).
   403 `booking_not_authorized` preflight on every creation request before
   any cached replay; denied cached POST writes no reservation/audit/
   idempotency record; revoked grant → 403 on cached POST with the original
   record unchanged; restored grant → same-key replay returns the original
   status/body/correlation; missing-asset 404 callback and its idempotent
   recording preserved; `reservations:create` scope still required
   independently; no idempotency core changes.
5. **Administration configuration.** PASSED (local + CI).
   Asset admin: booking-restricted + allowed-groups fields with the
   required help (unrestricted vs restricted, empty denies all, any-one
   group suffices, no parent inheritance, global `book_assets` still
   required, no machine/login rights, no existing-reservation rewrite);
   existing `web/admin-form-guidance.js` bound via admin media (JS file
   untouched). Accounts admin groups/user_permissions and Group
   permissions help now state booking grants are active while
   management/read-all capabilities "take effect when their enforcement is
   active"; staff-flag sentence retained verbatim.
6. **Legacy-import boundary.** IMPLEMENTED; ONE UNACCEPTED CI FAILURE.
   FUTURE confirmed appointments reuse the SAME current predicate at plan
   and at the locked-fresh apply revalidation (no reservation/success audit
   when no longer authorized; plan is advisory); completed-past historical
   exception preserved (`test_apply_past_completed_still_imported_without_grant`,
   `test_planner_past_completed_exception_preserved` pass locally and in
   CI); existing policy/time/status classifications and
   source-idempotency/audit/locks/parser untouched; bootstrap reuses
   existing assets unchanged with a focused pin
   (`test_bootstrap_assets.py::test_repeated_apply_preserves_configured_booking_access`).
   UNACCEPTED: failure #1 above — the pre-existing positive fixture in
   `tests/test_legacy_import.py` (outside this order's allowed paths)
   needs its future-appointment user granted `book_assets` explicitly;
   deferred to the next suffix with the legitimate fixture path. No
   planner/apply behavior was weakened to accommodate it.
7. **Positive/negative test matrix.** PASSED (local + CI) for all NEW tests.
   `tests/test_booking_authorization.py` (52 passed): no-grant (ordinary
   AND staff/unrelated-admin-perms), non-staff book grant, direct +
   multi-group union, restricted empty / last-group-deleted, five asset
   kinds, parent↔child non-inheritance both directions, superuser
   restricted non-membership denied / membership allowed, inactive +
   service denial, browser/API/service parity, forged POSTs, token loses
   grant/membership/asset access (denial without replacement;
   scope-missing still denied), owner lifecycle after loss, unchanged
   conflict/exclusion/policy-counter/blackout/audit/idempotency authority
   for eligible principals. `tests/test_booking_access_upgrade.py`
   (1 passed): populated old-asset migration + preservation. No autouse
   grants, no UserManager changes, no assertion weakening; existing
   positive booking fixtures granted `book_assets` via real Permission
   records in allowed files; negative cases preserved and new
   viewer/no-grant cases added.
8. **Focused Chromium 1440/390.** PASSED (local; browser tests green in CI
   within the 1173). New `tests/browser/test_booking_authorization_browser.py`
   (5 passed locally): eligible AND ineligible assets both visible with
   per-row + detail eligibility, Reserve action absent for ineligible with
   clear reason, eligible booking end-to-end, direct GET redirect + forged
   raw POST denied (nothing created), admin dual-select help bound /
   keyboard-reachable / no overflow / no framework wording, default +
   custom theme functional. Exactly TWO privacy-safe screenshots captured
   and actually viewed in this fresh context: (a) member detail of the
   restricted asset at 1440 (Booking access line + warning note; no group
   names/tokens/member metadata), (b) admin asset change Booking access
   fieldset at 1440 (restricted checkbox + bound dual-select with the
   selected operator group; no member data). Touched browser suites
   re-run locally: 21 passed (form guidance + human MVP + SLAIF design) +
   37 passed (branding + product entry + pilot path + reservation
   shortcuts) + the pilot browser test inside `tests/test_pilot_path.py`
   re-run under the browser runner (1 passed). No redesign/CSS framework.
9. **Docs + local/CI checks.** Docs PASSED; implementation CI PARTIAL (see
   above). Docs updated to proved-current behavior: README + INSTALL
   "broad member access" wording replaced (global book_assets + per-asset
   groups; project/org still deferred; new ordinary accounts need a
   deliberate book grant; Compose project names untouched);
   `docs/authorization.md` booking eligibility moved to implemented
   (management/read-all remain planned; example group names are operator
   configuration, not constants); `docs/human-ui.md` eligibility display;
   `docs/api-contract.md` 403 code + auth-before-replay invariant;
   `docs/ux/form-guidance-inventory.md` (reservable filter, groups/
   user_permissions, new asset fields incl. dual-select binding).
   Local checks (owned isolated env, OAP_ROLE unset): ruff check "All
   checks passed!", ruff format --check "232 files already formatted",
   mypy src "no issues found in 139 source files", `manage.py check`
   "no issues (0 silenced)", `makemigrations --check --dry-run` "No
   changes detected", OpenAPI `spectacular --validate --fail-on-warn`
   exit 0, changed-doc relative link check 52/52 targets exist,
   `git diff --check` clean, OAP stdlib harness "Ran 160 tests, OK".
   Focused local suites: 403 passed across the 15 touched server files
   (incl. real-PG concurrency), 52 + 1 new server files, 63 browser
   passes total. Restore drill NOT RUN locally (host lacks
   `pg_dump`/`pg_restore` — environmental; CI ran it and exposed failure
   #2). No local full pytest, no operational/HTTPS/Gunicorn/visual detours.
   CI at the implementation head: quality success (19s), security
   success (15s), container success (30s), oap-harness success (36s),
   test FAILURE (10m25s) as recorded above.

## Limits / uncertainties

- The two `test`-job failures above are UNACCEPTED and unremediated in
  this round: failure #1 requires a fixture grant in
  `tests/test_legacy_import.py`, which is outside this order's
  allowed_paths (scope blocker); failure #2 requires completing the
  `tests/test_restore_drill.py` probe-principal grant (allowed path) and
  verifying it where the restore drill can run (CI). Strategy's next
  immutable suffix on the same issue/PR carries the corrections; this
  frozen implementation is preserved unchanged.
- Report-head CI not observed at authoring; the automatic required
  report-head full CI is preserved, not waived, and must pass at the exact
  frozen report head before any conditional merge.
- Target gate unchanged: this is the booking-eligibility slice only.
  Management capabilities, cross-user read-all, qualification and a fresh
  independent ICA at the exact merged revision remain separate; no
  deployment, no audit claim, no ICA acceptance.
