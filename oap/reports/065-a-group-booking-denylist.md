<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "065-a",
  "order_path": "oap/orders/065-a-group-booking-denylist.md",
  "order_sha256": "1060b7ddf69a63996cc5b8100772f22e75116fd239f2c8fabd3084db98e61cc6",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 135,
  "pr_number": 136,
  "branch": "codex/135-oap-065-a-group-booking-denylist",
  "implementation_head": "e29e7f9a07c387c7209154e5c06233f07658aea0",
  "base_sha": "6d4c7184327ec07a6ad12869e62c43dadea99837",
  "previous_round": null,
  "pr_mode": "CREATE_OR_RESUME",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "e29e7f9a07c387c7209154e5c06233f07658aea0",
    "runs": [
      {
        "run_id": 44659822822,
        "workflow": "CI",
        "jobs": {
          "quality": "PASS",
          "test": "PASS",
          "security": "PASS",
          "container": "PASS"
        }
      },
      {
        "run_id": 44659822814,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "PASS"
        }
      }
    ]
  },
  "local_equivalent_checks": "real owned PostgreSQL 17 (127.0.0.1:54330) product suites: 221 focused server tests PASSED (test_booking_authorization, test_assets_models, test_assets_admin, test_bootstrap_assets, test_migrations, test_form_guidance, test_api_v1_reservations, test_authorization_upgrade); real Chromium browser suites PASSED (6/6 booking authorization incl. new denylist test, 8/8 form guidance); full local non-browser run 1404 passed / 9 skipped with ONE local-only oap-harness failure (test_ba38_39_tmux_config strategic print-only) that STRATEGIC diagnosed as an OAP_ROLE environment conflict of the CODING process and that passes in the CI oap-harness job at the exact head; ruff check / ruff format --check / mypy (147 files) / manage.py check / makemigrations --check --dry-run / spectacular --validate --fail-on-warn / git diff --check all clean; two privacy-safe Chromium screenshots captured and inspected (<=2 at a time)",
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 065-a — execution report: exact-asset group booking denylist

Implementation head SHA: e29e7f9a07c387c7209154e5c06233f07658aea0
Report publication commit: SELF

## Identity and result

COMPLETE for order 065-a (D0, `Decision: NONE`), issue #135, PR #136
(CREATE_OR_RESUME, `Closes #135`), branch
`codex/135-oap-065-a-group-booking-denylist`, base
`6d4c7184327ec07a6ad12869e62c43dadea99837` (verified equal to local HEAD
and origin/main at start, before the first edit). The order file at
`oap/orders/065-a-group-booking-denylist.md` (state FINAL, SHA-256
`1060b7ddf69a63996cc5b8100772f22e75116fd239f2c8fabd3084db98e61cc6`) and
the `oap/active` pointer (`065-a` + LF) were committed with the single
implementation commit
`e29e7f9a07c387c7209154e5c06233f07658aea0`. All 13 order `source_hashes`
were verified against the checkout before editing (all matched). Remote
reconciliation: no remote branch `codex/135-*` and no open PR for issue
#135 existed before this round; PR #136 was created fresh.

## Numbered acceptance evidence

### 1. Model, upgrade, Admin

- `Asset.excluded_booking_groups`: M2M to the EXISTING `auth.Group`,
  `blank=True`, default-empty; forward-only migration
  `src/slaif_reservation/assets/migrations/0004_asset_excluded_booking_groups.py`
  (one `AddField` only; no data backfill, no other schema change).
- Migration/default-empty on real PostgreSQL 17:
  `tests/test_migrations.py::test_booking_denylist_migration_preserves_existing_rows`
  migrates a populated pre-upgrade database (raw-SQL user/group/asset/
  allow-list/accepted reservation) through assets 0003 -> 0004 and asserts
  every existing row preserved, the new M2M empty, and the denylist
  immediately effective for a dual member while the plain allowed member
  stays eligible. PASSED.
- `makemigrations --check --dry-run`: "No changes detected" (model and
  migration agree). PASSED.
- Admin: field added to `AssetAdminForm`, the "Booking access" fieldset
  (independently of `booking_restricted`), `filter_horizontal`, and the
  `_wire` rendered help ("exclusion wins over the allowed list", exact
  asset checked, grants no other access, changes no existing booking).
  `tests/test_assets_admin.py::test_asset_admin_excluded_groups_field_is_independent_and_wired`
  (field/fieldset/widget wiring) and
  `test_asset_admin_save_sets_exclusions_independently_of_restriction`
  (real change-URL POST on an UNRESTRICTED asset keeps
  `booking_restricted=False`, preserves the allow-list, stores the
  exclusion). PASSED. Server-side validation/CSRF/model permissions
  unchanged (no permission/CSRF/validator code touched).
- Architecture/PLAN/projection: ARCHITECTURE.md appends A-18 (selected
  2026-11-20, issue #135) with its controlled-evolution paragraph
  (supersedes ONLY A-16's "no explicit deny rules" for this one asset
  booking gate) and SAR-057 in the A-14 map; PLAN.md P-08 records the
  human-selected amendment; ARCHITECTURE-for-agents.md adds the SAR-049
  A-18 note, the SAR-057 row, the A-18 executor section and the updated
  source digest (new root ARCHITECTURE.md full-source SHA-256
  `69e3b5a5deb8ffd030974878ee6ad690bdc0e5507bdd71989ffeda969f34dcd9`,
  prior digests retained as historical provenance). SAR-049 and A-16
  history preserved (append-only).

### 2. One authoritative predicate

- `assets/authorization.py`: `user_can_book_asset` checks global
  capability, then the exact-asset deny-list (deny before the allowed pass,
  on restricted OR unrestricted assets), then the restricted allow-list;
  new `STATE_EXCLUDED_GROUP`; `batch_asset_booking_states` emits the
  distinct state with both M2M sets read from the prefetched caches;
  `web/selectors.py` prefetches `excluded_booking_groups` alongside
  `allowed_booking_groups` (no N+1).
- Predicate semantics (real PG): `test_predicate_semantics` extended with
  unrestricted-excluded deny/allow, dual-membership deny (deny wins),
  allowed-only allow and superuser rows — 22 cases PASSED;
  `test_batch_states_excluded_beats_allow_and_unrestricted` PASSED.
- Service (row-locked `create_reservation`, unchanged):
  `test_service_denies_excluded_on_unrestricted_asset` and
  `test_service_denies_dual_membership_exclusion_wins` (0 reservations,
  0 audit rows) PASSED; positives
  `test_service_allows_non_excluded_bookings_on_excluded_assets`
  (non-excluded member books the same assets) PASSED.
- Churn: `test_service_exclusion_churn_applies_to_next_request_only` —
  exclusion added + membership added => next request denied, existing
  reservation untouched, owner cancel still allowed; exclusion lifted =>
  allowed again; membership removed => allowed again. PASSED.
- No inheritance: existing `test_no_parent_inheritance_either_direction`
  plus the new denylist tests keep the exact-asset-only rule (parent
  machine vs child never inherit each other's settings).
- Bearer preflight: unchanged code path rechecks the shared predicate
  before any cached idempotent replay (see 3).
- Policy/duration/lead/horizon/counters/blackouts/overlap/audit/owner
  lifecycle: no service code changed beyond the shared predicate; the
  regression suites (`test_api_v1_reservations`,
  `test_authorization_upgrade`, `test_bootstrap_assets`,
  `test_booking_authorization` conflict/policy/lifecycle tests) all PASSED.

### 3. Member/API truth and privacy

- List: `You can book` column now renders `yes` / `no` / a distinct
  `Excluded` cell (template `asset_list.html`, state passed per row).
- Detail: `Booking access` line and reserve denial reason
  ("Booking on this asset is excluded for your account.") are distinct
  from the no-permission and no-allowed-group states; the reserve action
  is not offered; assets remain visible.
- Privacy: no group names/IDs or other member data on any member surface —
  asserted in `test_browser_excluded_state_is_distinct_and_privacy_safe`
  (server-side) and
  `tests/browser/test_booking_authorization_browser.py::test_member_excluded_state_is_distinct_and_privacy_safe`
  (real Chromium, 1440 + 390, with a non-excluded positive control on the
  same rows). PASSED.
- Direct requests: `test_browser_denies_excluded_direct_get_and_post`
  (GET redirect + POST form error with the truthful reason, 0 writes)
  PASSED; real-Chromium direct reserve GET denied.
- API: `test_api_denies_excluded_member_403` (unrestricted + restricted,
  stable `403 booking_not_authorized`, no records, no group identity) and
  `test_api_exclusion_added_after_success_denies_new_and_cached_then_replays`
  (exclusion added after a cached success blocks NEW and cached POSTs;
  lifting it replays the ORIGINAL 201, no duplicate reservation/audit).
  PASSED. Owner-only API routes and the existing contract unchanged
  (`spectacular --validate --fail-on-warn` clean; endpoint shape
  unchanged).
- Existing reservations: never deleted/rewritten by the denylist; owners
  keep cancel/release after losing eligibility (covered by the churn test
  and the retained 049-a lifecycle suites). No new cross-user or bearer
  mutation scope added.

### 4. Evidence/docs

- Focused suites (real owned PostgreSQL 17, real Chromium): 221 server
  tests PASSED across test_booking_authorization / test_assets_models /
  test_assets_admin / test_bootstrap_assets / test_migrations /
  test_form_guidance / test_api_v1_reservations / test_authorization_
  upgrade; browser 6/6 booking + 8/8 form-guidance PASSED, including the
  new Admin excluded-select binding assertion in
  `test_form_guidance_browser.py`.
- Bootstrap reapply: `test_repeated_apply_preserves_configured_booking_access`
  extended to preserve the exclusion exactly (importer owns no booking
  fields). PASSED.
- Legacy planner: `test_planner_future_excluded_member_reuses_current_denylist`
  — a FUTURE appointment for an excluded (dual) member reports
  `booking_not_authorized` through the SAME shared predicate; a
  non-excluded allowed member on the same asset still plans as
  would-create; the completed-past historical exception is unchanged.
  PASSED.
- Screenshots: two privacy-safe Chromium captures inspected <=2 at a time
  (`booking-denylist-member-detail-1440.png`: distinct
  "Booking on this asset is excluded for your account." access line +
  warning, no Reserve action, no group names, no framework branding;
  `booking-denylist-member-list-390.png`: distinct `Excluded` list cell,
  no horizontal overflow). No tokens/passwords/CSRF/private data in either
  capture.
- Docs reconciled (now-false prose only): README, INSTALL (two sites),
  docs/authorization.md (enforcement paragraph, current baseline,
  permission matrix + deny-list note, illustrative-role paragraph, asset
  configuration paragraph, exact-asset section, upgrade/backup paragraph),
  docs/human-ui.md, docs/api-contract.md, docs/security-model.md,
  docs/deployment.md, docs/ux/form-guidance-inventory.md (new
  `excluded_booking_groups` row + corrected allow-list/grant rows).
  Product-first, no work-order ledger.
- Static: ruff check / ruff format --check / mypy (147 files) /
  manage.py check / makemigrations --check --dry-run /
  spectacular --validate --fail-on-warn / git diff --check: all clean.
- Exact-head CI (observed): CI run 44659822822 at
  `e29e7f9a07c387c7209154e5c06233f07658aea0` — quality PASS, test PASS,
  security PASS, container PASS; oap run 44659822814 — oap-harness PASS.
  All five exact-head checks terminal and passing. Report-head CI is NOT
  yet observed at authoring and is not claimed.

## Local-only observation (not a product failure)

The full local non-browser run (1404 passed, 9 skipped) showed ONE failure
outside the product: `tests/oap/test_ba38_39_tmux_config.py::
Ba39OperationPrereqs::test_ba39_strategic_same_prerequisites`
("print-only is always allowed"). STRATEGIC independently diagnosed it as
the CODING process exporting `OAP_ROLE=CODING`, which conflicts with the
fixture strategic launcher subprocess; with `env -u OAP_ROLE` the file
passes 12/12 locally, and the CI oap-harness job (run 44659822814)
PASSES at the exact implementation head. No product byte is involved.

## Uncertainty, privacy, dependencies, DHA, limits

- No uncertain product behavior: every acceptance path was executed on
  real PostgreSQL 17 and real Chromium; no mocked boundary stands in for a
  claimed invariant.
- No credentials, verifiers, peppers, passwords, cookies, CSRF values,
  tokens or private data appear in this report, the diff, or the
  screenshots; the test passwords are synthetic fixtures in the repo's
  existing style.
- Dependencies: none added; uv.lock, Docker/Compose, proxy and CI
  configuration untouched.
- DHA: `Decision: NONE` (no CRITICAL append; the register is unchanged).
- Limits: this is development evidence only. The fresh exact-revision
  independent ICA, strategic development merge, human milestone judgment,
  release and any real deployment/exposure (D2) remain separate and are
  not claimed here. The separately selected mass-email objective is NOT
  part of this PR.
