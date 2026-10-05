<!-- OAP-META
{
 "kind": "report",
 "id": "037-c",
 "order_path": "oap/orders/037-c-admin-guidance-closure.md",
 "order_sha256": "50a56ae8ccdffae656b14ef37363a099128587ca6b88d1685671749225692e70",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 73,
 "pr_number": 74,
 "branch": "codex/73-oap-037-a-form-guidance",
 "implementation_head": "8aa66f66d820c33c5a9fe8200a18242592006d19",
 "previous_implementation_head": "6bd5e1960ae4702e9996e0fd383548d218d2b744",
 "base_sha": "c4703beacf9c887d7ccfb59c89af4f389bdb57ed",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "8aa66f66d820c33c5a9fe8200a18242592006d19",
  "runs": [
   {
    "run_id": 37300284317,
    "workflow": "CI",
    "jobs": {
     "quality": "success",
     "security": "success",
     "test": "success",
     "container": "success"
    }
   },
   {
    "run_id": 37300284357,
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

# 037-c — Final administration guidance closure

Implementation head SHA: 8aa66f66d820c33c5a9fe8200a18242592006d19
Report publication commit: SELF

Result: COMPLETE for all four 037-c acceptance items. Same objective,
round c, branch codex/73-oap-037-a-form-guidance, issue #73 and PR #74
(AMEND); base c4703beacf9c887d7ccfb59c89af4f389bdb57ed unchanged. The
037-c change set versus the 037-b report head (dbb24c77b6a9dd2b6d12dd25e291531fe40d7931)
is 9 files, every one inside the order allowed_paths; zero changes under
models/, migrations/, services, the policy evaluator, parsers, validators,
admission, crypto, API/wire contracts, inventory data or dependencies.
Coding never merged; the PR stays open for strategic/human acceptance.

Supersession: the 037-b report's classification of the staff
assets/api.py REST endpoints as UNREACHABLE was an error. config.urls
includes api.urls, which expands *asset_api_urls.urlpatterns, so
/api/v1/assets/ and /api/v1/assets/<uuid>/ ARE live staff-session
endpoints. Only the legacy assets/views.py HTML views/templates are
unrouted. The immutable 037-b report is preserved; this report supersedes
that one claim (acceptance 2).

## 1. Permission help corrected against real authorization (acceptance 1)

- _USER_FIELD_HELP["user_permissions"] no longer says "per-model
  administration and management access only". It now states: individual
  site permissions govern per-model administration operations in this
  administration only and do NOT grant management access, which follows
  the active staff flag; they do not affect reservable-asset policy and
  do not admit a session by themselves.
- _USER_FIELD_HELP["is_staff"] now clarifies that the matching model
  permissions are additionally required for per-model ADMINISTRATION
  operations in this administration only; management itself needs none
  of them (entry still follows the flag with an active,
  non-service-account session, never individual permission selections).
- GroupAdmin.permissions help no longer says "(administration and
  management access)". It now states the group's site permissions govern
  per-model administration operations in the administration only, not
  management access, which follows the active human staff status; not
  project/membership authorization.
- No permission/guard/feature changes: management_ui/auth.py is
  unchanged (is_management_user = authenticated + active + is_staff +
  not a service account; no model permission is consulted there), and
  the round diff contains no authorization code.
- Pinned: the rendered wording is asserted on the user change page and
  the group add page (server + browser inner_text), and
  tests/test_form_guidance.py::test_admin_permission_help_matches_authorization
  proves the behavior against the real rules: a real staff user WITHOUT
  individual/group permissions gets 200 on /manage/ and
  /manage/reservations/ (management reachable by staff status alone)
  while the same user gets 403 on the administration model operation
  /admin/reservations/reservationpolicy/ (model-permission enforcement
  retained); a superuser still gets 403 on /admin/accounts/apitoken/add/
  (protected models stay protected).

## 2. Inventory routing contradiction corrected (acceptance 2)

- docs/ux/form-guidance-inventory.md section 4 now classifies ONLY the
  legacy assets/views.py HTML views/templates as unrouted, and states
  that the staff REST endpoints of assets/api.py ARE routed (config.urls
  -> api.urls -> *asset_api_urls.urlpatterns) as live staff-session
  endpoints; the bearer assets:read reserved limitation is preserved
  (assets/api.py unchanged: SessionAuthentication + IsAdminUser, no
  token authentication offered there).
- New rendered-suite test
  tests/test_form_guidance.py::test_staff_asset_api_routes_are_live pins
  the real resolver AND live HTTP against the current source:
  reverse("api-v1:asset-list") == /api/v1/assets/ resolving to
  AssetListAPIView and reverse("api-v1:asset-detail", ...) resolving to
  AssetDetailAPIView; no view of the assets.views module appears in any
  URL-conf callback (the legacy HTML views are the only unrouted
  assets-app surface); anonymous and non-staff members get 403, a staff
  session gets the inventory JSON (count 2, both fixture slugs) and the
  UUID detail. No routes were added or removed.

## 3. Required accessible associations, no waivers (acceptance 3)

- usable_password RadioSelect: a presentation-only
  _BoundHelpRadioSelect (accounts/admin.py) reports the first choice's
  id at field level, so the template renders the help div with the
  stable id id_usable_password_0_helptext; the widget attrs set
  aria-describedby on BOTH rendered choices (id_usable_password_0 and
  _1). Choice ids, values, labels, keyboard and submit behavior are
  unchanged; the field label now carries for=id_usable_password_0
  (standard HTML label semantics; previously no for attribute).
- JS-generated select-filter lists: new narrow local helper
  web/admin-form-guidance.js (53 lines, no dependencies, no framework
  monkeypatch; loaded via UserAdmin/GroupAdmin media) binds BOTH
  generated list boxes (id_<name>_from and id_<name>_to) of every
  permission/group selector (groups, user_permissions, permissions) to
  the rendered field help (id_<name>_helptext) after the admin
  SelectFilter2 initialization (window-load plus follow-up macrotask;
  idempotent; no-op without select filters). No validation, submission,
  filtering, movement or icon behavior is touched.
- All existing warning/validators/actions/fieldnames/media/keyboard
  behavior, password enable-disable and the safe password status are
  preserved: the 037-b behavior tests (invalid mismatched POST rejected
  with hash intact, enable sets a real password, disable removes it,
  safe disabled status re-renders, safe status instead of hash summary)
  pass unchanged.
- The unbound bypass assertions are removed from both suites. Server:
  GET and invalid-POST re-render of the password page assert the help id
  exists and BOTH choices bind it, with no dangling aria-describedby on
  the page. Browser: at 1440/390 the suite asserts, after widget
  initialization, that both from/to list boxes of each
  permission/group selector are visible and bind the rendered, visible
  field help in the same field container; that both radio choices are
  visible and bind the rendered help (field label binds the first
  choice, second choice keyboard-focusable); and that the invalid
  (mismatched) password POST keeps the rendered, bound help.
- docs/ux/form-guidance-inventory.md, docs/human-ui.md and TESTING.md
  state the final wiring: no control renders help without an accessible
  association; the documented mechanism is the bindable help ids plus
  aria-describedby (widget subclass + narrow local helper), with no
  DOM-coverage overclaim (the JS-generated boxes are asserted in a real
  browser after initialization).

## 4. Owned-disposable verification, visual review, CI (acceptance 4)

All product pytest/management qualification ran on the owned disposable
scratch clone (/tmp/sar037c-325b14b1/source, byte-identical to the
committed implementation) against the owned PostgreSQL17 container from
the 033-b receipt (container 4e8ae3b97a8a4f052a55bac4da018d67e36826ef15b2daac568ec7c36fa285f4,
nonce e83852824963cfd98de8102d, port 34421; validated against docker ps
by exact ID/name). The private tests.env was parsed into the child
process env dict only (never printed); OAP_ROLE cleared; PYTHONPATH from
the clone; explicit test settings module. Nothing was run from the
valuable repo root. One environment note: the production docs-probe in
test_proxy_security.py requires a collected staticfiles manifest
(gitignored build artifact; in the full suite the
tests/test_proxy_gunicorn.py module fixture collects it). A single
collectstatic was run in the scratch clone to mirror that documented
full-suite dependency; no product change.

- Server suite tests/test_form_guidance.py: 32 passed in 3.70s (30 in
  037-b; +test_admin_permission_help_matches_authorization,
  +test_staff_asset_api_routes_are_live).
- Focused neighbors (test_web_human_mvp, test_management_ui,
  test_assets_admin, test_product_entry, test_proxy_security,
  test_reservations_concurrency): 137 passed, 1 warning (the
  pre-existing intentional override_settings UserWarning in
  test_product_entry.py) in 16.00s.
- Browser suite --browser chromium
  tests/browser/test_form_guidance_browser.py: 7 passed in 18.33s;
  35 captures regenerated from the final bytes.
- ruff check and ruff format --check: clean (208 files); mypy strict:
  131 source files, no issues; manage.py check: 0 issues;
  makemigrations --check --dry-run: no changes; git diff --check: clean.
- Full-suite coverage for the implementation head comes from the
  exact-head CI test job; the unchanged local full suite was NOT
  repeated.

Implementation CI at exact head 8aa66f66d820c33c5a9fe8200a18242592006d19
(observed): CI run 37300284317 — quality, security, test and container
all success; oap run 37300284357 — oap-harness success. All five checks
pass; no missing/skipped/cancelled check. Report-head CI: NOT YET
OBSERVED AT AUTHORING; its outcome goes to the private execution
receipt, never to this immutable report.

Visual review of the final captures (fresh independent read-only CODING
contexts, codex-cli 0.160.0, profile qwen-neumann, sandbox read-only,
owned scratch cwd, OAP_ROLE=CODING; <=8 PNGs per context; both
subprocesses rc 0): 23 of 35 captures are sha256-identical to the 037-b
final reviewed set, so their visual validity persists by hash match.
The 12 changed captures: 8 changed surfaces (admin-user-change 1440/390,
admin-user-add 1440/390 [corrected is_staff wording],
admin-password-change 1440/390 [new radio binding], admin-group-add
1440/390 [new select-filter binding + corrected wording]) reviewed in
one fresh context (batch A): NO ISSUES. The other 4 differ only by
per-run synthetic fixture data (reserve-1440: 1 sampled pixel;
reservation-filters-1440: seeded reservation row; admin-asset-change
1440/390: created_at/updated_at timestamps — sampled-pixel diff shows no
other region changed) and were reviewed in a second fresh context
(batch B): only fixture data, no layout/guidance change. Batch B noted
one pre-existing minor observation (admin asset change Parent select
renders its selected value truncated, "GUIDA", at 1440; that region is
pixel-identical to the 037-b final capture already reviewed NO ISSUES in
037-b; stock admin select width, appearance-only, outside 037-c scope).
Paths and per-image sha256: workorders/037c-screenshots-final/ and
workorders/037c-visual-review/A.log B.log (private root home, not in
Git).

PR #74 for issue #73 (body ends Closes #73); coding never merges.

## Failures, uncertainties, limits

- No test failures at the final implementation head.
- Implementation CI observed at authoring (5/5 success); report-head CI
  not observed at authoring (private receipt).
- 23 of 35 captures not re-viewed (byte-identical to the 037-b final
  reviewed set); validity = 037-b review plus hash match.
- The pre-existing asset-change Parent-select truncation at 1440 is
  reported, not fixed (appearance-only, previously reviewed, outside
  037-c allowed scope).
- This report claims no strategic acceptance, no production/exposure
  change, no DHA candidates. No credentials, verifiers, peppers,
  cookies, CSRF values, tokens or private data appear in this report or
  in any captured artifact. Decision: NONE stands.
