<!-- OAP-META
{
 "kind": "report",
 "id": "036-b",
 "order_path": "oap/orders/036-b-admission-visual-closure.md",
 "order_sha256": "8e779eabdee8dbb6c09e00121bea4955f50fe3b0cca5af8f3a8ead7853eac38d",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 71,
 "pr_number": 72,
 "branch": "codex/71-oap-036-a-public-product-entry",
 "implementation_head": "69e26338c921d96f45f3037bbc142cb4cce12643",
 "previous_implementation_head": "0e2d45d6d62f50f2c5e930efe9fa4b5557f551ae",
 "base_sha": "e87497a1169bf4745489f699c28377bfbd2df717",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "69e26338c921d96f45f3037bbc142cb4cce12643",
  "runs": [
   {
    "run_id": 37253929687,
    "workflow": "CI",
    "jobs": {
     "quality": "success",
     "test": "success",
     "security": "success",
     "container": "success"
    }
   },
   {
    "run_id": 37253929675,
    "workflow": "oap",
    "jobs": {
     "oap-harness": "success"
    }
   }
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 036-b — Administration admission and visual-evidence closure

Implementation head SHA: 69e26338c921d96f45f3037bbc142cb4cce12643
Report publication commit: SELF

Result: COMPLETE for all seven 036-b acceptance items. Development only
(M-INTERNET-UX-PILOT); no deployment, no real exposure, no merge. PR #72
(issue #71), AMEND mode on the 036-a objective, same base
e87497a1169bf4745489f699c28377bfbd2df717. All 036-a acceptance is retained;
the 036-a immutable report is preserved unchanged.

Environment (all product pytest/management qualification): owned disposable
source copy in a unique tmp clone of the committed 036-a head with only the
explicit in-scope files copied in, owned PG17 loopback cluster (port 34421,
cluster receipt 033-b) with a fresh owned role/round database, Chromium;
product-test child envs with `OAP_ROLE` cleared and explicit
PYTHONPATH/settings/DB URL from a private round env file read as a Python
dict (never printed). No product pytest or management command ran from the
valuable checkout (lint/types/git publication only).

## Acceptance evidence

1. Staff-only administration credential admission restored.
   `SlaifAdminAuthenticationForm.confirm_login_allowed` again requires the
   Django staff guard in addition to the shared active-human rule, so a
   valid NON-STAFF member POST /admin/login/ is denied generically
   ("Enter a valid email address and password") with no session created, no
   credential-class wording, and normal member-login access preserved.
   PASSED (unit: `test_admin_login_rejects_non_staff_members`, plus the
   unchanged service-account/inactive denials and staff/superuser positive
   admissions in `test_admin_login_rejects_non_human_identities`; real
   browser: `test_browser_admin_login_rejects_non_staff_members`,
   `test_browser_admin_login_rejects_service_accounts`; real TLS shared
   login budget with staff positive recovery:
   `tests/test_abuse_http.py::test_member_and_admin_login_share_budget_and_valid_accounts_recover`).
2. Active-human rule on EVERY admin route, not just login.
   `SlaifAdminSite.has_permission` now requires an active staff HUMAN, so
   the admin_view gate (which wraps index, changelist, change, delete,
   history, autocomplete, password-change, logout and shortcut routes)
   denies service/inactive sessions on every admin URL, and the existing
   login-view termination ends those sessions. A session created for a
   valid human loses all admin routes the moment the operator flips
   is_service_account or is_active (flags are read per request). No
   blanket permission bypass, no session impersonation privilege, and no
   per-model permission change. PASSED (unit:
   `test_admin_routes_deny_and_terminate_service_account_session` across
   index/users/assets/reservations routes with session-termination
   assertion, `test_admin_access_denied_after_account_flags_change`
   (service-account flip on the index, inactive flip on a model changelist,
   both terminating the session), `test_non_staff_member_denied_administration_without_session_loss`
   (valid member session denied, not terminated),
   `test_valid_staff_admin_matrix_preserved` (superuser: all four app
   groups and changelists 200; plain staff: site admitted, protected model
   content still permission-gated with 403; ApiToken/AuditEvent/
   Reservation/MaintenanceBlackout add/change/delete all False); real
   browser: `test_browser_admin_flag_transition_denies_and_terminates`
   (real HTTP: staff human admin index 200 -> flag flip -> /admin/ lands on
   the administration login with the session terminated, and / no longer
   reaches the member dashboard), `test_browser_admin_index_lists_protected_token_model_readonly`).
3. Complete 10-image matrix at the implementation head. 12 real-app
   Chromium tests passed (17.76 s) producing exactly the required 10
   privacy-safe screenshots at 1440/390: landing, member login (390 added
   this round), member Dashboard, admin login, admin index. The member
   Dashboard is populated with a representative synthetic asset, an
   effective asset policy and own reservations: the upcoming reservation is
   created through the existing `create_reservation` domain service
   (policy enforcement, exclusivity, audit), and the in-progress record is
   seeded synthetically because the domain service by design rejects new
   bookings with past starts; the rendered Dashboard exercises layout,
   member navigation, the Europe/Ljubljana timezone banner and display, and
   purpose-string privacy (absent from HTML). Empty-state behavior tests
   (no-framework/branding, canary, overflow) all still run and pass. No
   one-time token, password verifier, cookie, CSRF, raw HTML, HAR, trace or
   real private data appears in any capture (synthetic fixtures only).
   PASSED.
4. Scoped administration identity readability. The administration header
   wordmark is now white (replacing the low-contrast yellow accent), the
   official multi-color logo sits on a modest white chip on the default
   blue header, and a <=480px rule keeps the branding compact at 390.
   The admin index uses the concise "Administration" heading instead of
   the repeated long "site administration" copy; site_header/site_title
   identity is unchanged. Only identity/header/footer/logo CSS and the
   index title changed — controls, focus outlines, layout, permissions and
   model registrations are untouched (1440/390 screenshots re-captured and
   re-viewed afterwards). PASSED.
5. Screenshots actually viewed with an image-capable viewing tool. All 10
   PNGs were opened and inspected with the agent's image viewing tool
   (PNG decoded and rendered for visual inspection), not by CSS/dimension/
   text inspection; one visual correction (compact <=480px administration
   header) was found at 390 and iterated, then re-captured and re-viewed.
   This supersedes the unsupported "all 9 look good" visual-complete claim
   of the 036-a report; the 036-a report remains immutable and is not
   rewritten. STRATEGIC receives the final 10 images for its own actual
   viewing at frozen review. PASSED.
6. TESTING.md kept task-oriented. The appended "036-a ... (evidence)"
   execution ledger (private port, receipt label, precommit counts) is
   replaced by a short "Public entry, administration admission, browser
   identity (task guidance)" section: the focused pytest commands and the
   owned-disposable-source/DB warning. Round chronology and results remain
   in the immutable OAP reports. PASSED.
7. Focused repaired cases first, then exact-head CI. Focused unit/browser
   suites ran first (below); the full required five-check CI ran at the
   exact implementation head (below), with the normal report-head CI
   following publication. No unchanged broad local suite was repeated.
   PASSED (report-head CI outcome goes to the private receipt, not here).

## Commands and results

All from the owned clone against the owned PG17 round database
(product-test child envs, `OAP_ROLE` cleared):

- `pytest --ds=slaif_reservation.config.settings.test
  tests/test_product_entry.py` — 17 passed (5.58 s), including 5 new
  admission tests.
- `pytest --ds=slaif_reservation.config.settings.test
  tests/test_assets_admin.py tests/test_abuse_controls.py
  tests/test_web_human_mvp.py tests/test_api_schema.py` — 63 passed
  (12.19 s).
- `pytest --ds=slaif_reservation.config.settings.test
  tests/test_abuse_http.py` — 5 passed (30.29 s; real Gunicorn + TLS,
  shared member/admin login budget).
- `pytest --ds=slaif_reservation.config.settings.test --browser chromium
  tests/browser/test_product_entry_browser.py` — 12 passed (17.76 s) at
  the implementation head, final run after the visual iteration; 10
  privacy-safe screenshots captured and all 10 actually viewed.
- Gates: `ruff check .` clean; `ruff format --check .` clean (205 files);
  `mypy src` clean (130 files) (valuable checkout); `manage.py check` 0
  issues; `manage.py makemigrations --check --dry-run` no changes;
  `manage.py spectacular --file build/openapi/schema.yaml --validate
  --fail-on-warn` clean (owned copy); `git diff --check` clean.
- CI at implementation head
  69e26338c921d96f45f3037bbc142cb4cce12643 (observed before authoring):
  CI run 37253929687 — quality success, test success (full
  suite: 835 passed, 1 warning in 452.72 s), security success,
  container success; oap run 37253929675 — oap-harness success.
  No missing/skipped/cancelled check. Report-head CI: NOT YET OBSERVED AT
  AUTHORING; its outcome goes to the private execution receipt, never to
  this immutable report.

## Failures, uncertainties, limits

- The only local failure during this round was a first-attempt dashboard
  seed that used a past start through `create_reservation`; the domain
  service correctly rejected it (RESERVATION_IN_PAST), and the test was
  corrected to seed the in-progress record synthetically (established
  fixture pattern in this repository) while upcoming reservations still go
  through the domain service. No product behavior changed as a result.
- Visual quality remains a STRATEGIC review gate: the final 10 screenshots
  are provided for that review at
  `/home/ubuntu/codex-supervision/slaif-asset-reservation/workorders/036b-screenshots/{landing-1440,landing-390,member-login-1440,member-login-390,member-dashboard-1440,member-dashboard-390,admin-login-1440,admin-login-390,admin-index-1440,admin-index-390}.png`;
  coding does not claim release or visual acceptance.
- No DHA candidates arose; the order's Decision: NONE stands. No
  credentials, verifiers, peppers, cookies, CSRF values, tokens or private
  data appear in this report, the screenshots, or any captured output.
