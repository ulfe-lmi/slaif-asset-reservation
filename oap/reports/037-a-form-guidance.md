<!-- OAP-META
{
 "kind": "report",
 "id": "037-a",
 "order_path": "oap/orders/037-a-form-guidance.md",
 "order_sha256": "7ad45a113655e847ab1b4027c5b609d710b8341aa490eb854c03358f80065492",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 73,
 "pr_number": 74,
 "branch": "codex/73-oap-037-a-form-guidance",
 "implementation_head": "cc8dbbbd6c2d9f5784198670ea78e5247eb09caf",
 "previous_implementation_head": "dca50cb87b3b53aebc7b903364ce4354f3fb63e3",
 "base_sha": "c4703beacf9c887d7ccfb59c89af4f389bdb57ed",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "cc8dbbbd6c2d9f5784198670ea78e5247eb09caf",
  "runs": [
   {
    "run_id": 37266125105,
    "workflow": "CI",
    "jobs": {
     "quality": "success",
     "test": "success",
     "security": "success",
     "container": "success"
    }
   },
   {
    "run_id": 37266125111,
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

# 037-a — Understandable forms and choices

Implementation head SHA: cc8dbbbd6c2d9f5784198670ea78e5247eb09caf
Report publication commit: SELF

Result: COMPLETE for all eight 037-a acceptance items. PR #74 (issue #73),
CREATE_OR_RESUME created the PR, branch
codex/73-oap-037-a-form-guidance, base
c4703beacf9c887d7ccfb59c89af4f389bdb57ed (= origin/main at order start).
Presentation-only change set: 37 files vs base, every one inside the order
allowed_paths; zero changes under models/, migrations/, services, policy
evaluator, parsers, validators, admission, crypto, API/wire contracts,
inventory or dependencies. One presentation defect found by actual
screenshot viewing (policy-detail duration spacing) was fixed in the final
commit cc8dbbbd6c2d9f5784198670ea78e5247eb09caf after the first
implementation head dca50cb87b3b53aebc7b903364ce4354f3fb63e3 had already
passed all five CI checks; the final head was re-verified locally (focused +
browser) and by the full five-check CI run before this report was authored.
Coding never merged; the PR stays open for strategic/human acceptance.

## 1. Field/control inventory and coverage map (acceptance 1)

- docs/ux/form-guidance-inventory.md (new, committed) enumerates the ACTUAL
  runtime bound forms: member web forms (login, profile, reserve, token
  create/list, asset list filters + availability), management forms (policy
  add/update, blackout add/update, reservation list/detail filters and
  actions, audit list filters + export) and inherited/admin-generated
  controls (User add/change, per-user change password, Group add/change,
  Asset add/change, AssetTag, plus read-only Reservation/Policy/Blackout/
  Audit/Token admin views and raw template filters/actions).
- Each editable control records its rendered label, nearby help text and
  association mechanism, or an explicit self-evidence reason (no filler
  "Enter name"). Protected/read-only admin models record contextual
  explanation and the supported service-backed mutation path.
- The earlier 39-declared-field AST baseline is superseded as coverage proof
  by this runtime inventory; coverage is asserted by rendered tests (item 6),
  not by help constants.

## 2. Member surfaces (acceptance 2)

- Login: email/password with help stating accounts are created by an
  administrator and self-registration is not available.
- Profile: display name and REQUIRED IANA timezone with concrete example;
  no blank-fallback behavior (unchanged validation, unchanged negatives).
- Reservation: start/end/purpose labels with DST start/end occurrence
  guidance shown only where relevant to ambiguous local clock times.
- Cancel/release actions carry their real effects; token name/lifetime/
  scope choices carry human labels and per-scope effect text (item 5).
- Raw asset search/kind/parent/tag/reservable filters and availability
  controls each render nearby help with matching help IDs.
- Association is rendered and tested: the custom {% field_guidance %} tag
  wires label + help with id_<name>-help / aria-describedby on member and
  management surfaces; admin surfaces use the inherited
  id_<name>_helptext wiring (Django 5.2 fieldset.html +
  BoundField.build_widget_attrs auto aria-describedby). Error POSTs re-render
  guidance (tested); group-checkbox choices carry explanations.

## 3. Staff surfaces (acceptance 3)

- Every policy field explains its semantics from source: units and horizon
  (how far future START is allowed), duration as elapsed minutes with
  max 2880 = 48 hours = 2 days, lead and cancellation cutoff effects,
  global-fallback vs exact/parent priority, optional purpose, and upcoming/
  account limits across assets/tokens. The overlap cap 8 is explained as
  REJECT when 8 existing records intersect the proposed interval (not a
  simultaneous occupancy sweep).
- Default policy is displayed in understandable units: 30 to 2880 minutes
  (30 minutes - 2 days), 7 days horizon, no lead, no cutoff, 50 upcoming /
  8 overlapping per principal. Stored units and the evaluator are unchanged.
- Blackout: exact-asset behavior, overlap confirmation, and the fact that
  existing reservations are not automatically canceled are stated; the
  deactivation choices (policy and blackout) show warnings of their actual
  effects.
- Raw policy asset filter, reservation filters (asset/q/status/lifecycle/
  from/to) and audit filters (action/target type/actor/source/correlation/
  occurred from/to) each carry selector-accurate help; the Export CSV link
  states that it downloads the current filtered view (unfiltered: last 7
  days, bounded row count).

## 4. Administration (acceptance 4)

- User add/change: email, password (+ confirmation), is_active, is_staff,
  is_superuser, is_service_account, timezone, groups and user permissions
  all carry precise effect text; flags are described by their ACTUAL effects
  (no implied notifications/OIDC/reset). The per-user change-password page
  keeps Django's built-in validator list and confirmation help with the
  real permitted action (change_password form); no dead password_change_form
  attribute; validation/hashing/account permissions preserved and tested.
- The inherited password-hash summary is replaced by a safe password status
  (enabled/disabled of password-based authentication) with no
  password/verifier fragments exposed (safe_password_status.html template +
  read-only presentation in accounts/admin.py).
- Group permissions, AssetTag and Asset add/change (parent/slug/name/kind/
  booking mode/description/location/timezone/state/verification/
  capabilities/tags/internal locator) carry per-field help; booking mode
  states only 'Exclusive' is supported and what that means.
- Groups are explicitly NOT project/membership authorization: site
  permission groups only, and they do not change who can reserve assets.
- Protected policies/reservations/blackouts/audit/tokens remain read-only
  with clear service-backed routes; no model/schema changes were made to add
  help text (verified by the 37-file diff against base).

## 5. Token scope labels (acceptance 5)

- Machine-strings-only choices/displays are replaced by human-readable
  labels and useful per-scope effect text (SCOPE_LABELS / SCOPE_EFFECTS in
  web/templatetags/form_guidance.py) while exact stored/wire values stay
  intact.
- assets:read is labeled RESERVED and does NOT grant bearer inventory
  discovery; availability:read and reservation read/create/cancel/release
  each explain their separate effect.
- No auto-added scopes, no new rights, no lifetime rule changes; one-time
  plaintext display, no-store/private/no-referrer and history scrubbing are
  preserved (unchanged negative tests pass). No Django or work-order text in
  user-visible guidance.

## 6. Rendered tests (acceptance 6)

All product pytest/management qualification ran on owned disposable source
copies (scratch checkout; owned PG17 container per the 033-b receipt;
private env parsed into the child environment, never printed; OAP_ROLE
cleared; unique owned DB name per run; PYTHONPATH from the scratch copy).
Nothing was run from the valuable repo root.

- New server suite `uv run pytest tests/test_form_guidance.py`: 22 passed at
  dca50cb (tags sar037a-foc1 set) and 22 passed at cc8dbbb (tags
  sar037a-fix1/fix2). It asserts actually rendered help/labels/associations
  on GET and invalid POST across member/management/admin/raw filters,
  including the unchanged negatives (timezone/DST/duration/policy
  validation, staff/SA/nonstaff/owner/CSRF/scopes/protected admin, token
  secret behavior, min>max rejection with guidance kept).
- Focused operational neighbors
  (`tests/test_form_guidance.py tests/test_web_human_mvp.py
  tests/test_management_ui.py tests/test_assets_admin.py
  tests/test_product_entry.py tests/test_proxy_security.py
  tests/test_reservations_concurrency.py`): 159 passed, 1 warning
  (pre-existing intentional `override_settings(DATABASES)` UserWarning in
  tests/test_product_entry.py) at dca50cb (tag sar037a-foc1) and 159 passed
  in 14.98s with the same single warning at cc8dbbb (tag sar037a-fix3).
- New browser suite `tests/browser/test_form_guidance_browser.py`
  (--browser chromium): 7 passed at dca50cb (tag sar037a-shots1) and 7
  passed at cc8dbbb (tag sar037a-shots2). Representative seeded forms at
  1440 and 390 assert no horizontal overflow, keyboard access and nearby
  help; original assertions preserved, selectors adjusted semantically only.
- Existing browser suites `tests/browser/test_human_mvp_browser.py` (6) and
  `tests/browser/test_product_entry_browser.py` (12): 18 passed at dca50cb
  within the full run (human scope-label expectations updated
  semantically).
- Full suite at dca50cb (exact commit, scratch hard-reset): 864 passed,
  0 failed, 741.6s (tag sar037a-full1). The final head cc8dbbb's full-suite
  coverage comes from the exact-head CI `test` job (item 8); per the order,
  the unchanged local full suite was NOT repeated.
- ruff check, ruff format --check and mypy (strict, 131 source files) are
  clean at cc8dbbb; `manage.py check`, `makemigrations --check` and
  `git diff --check` were clean at dca50cb.
- No screenshot of one-time tokens or password/verifier/CSRF/cookie/raw
  HTML/HAR/trace/real data; safe fixtures only (item 7).

## 7. Screenshot review with view_image (acceptance 7)

Method: the coding agent actually opened and visually inspected every
capture with the view_image tool — 26/26 (16 viewed in the first pass at
dca50cb, 10 in the second pass, and 3 re-viewed after the fix
re-capture). No CSS-only or dimension-based inference is claimed. Root will
open the final images separately. No forced pixel-perfect CI snapshots.

Iteration: the first-pass view of policy-detail-1440 showed the Duration
row as "30-to 2880 minutes" (missing space: template
`{{ min }}-{% trans "to" %}`). This was fixed in cc8dbbb
(one-line template spacing change in
src/slaif_reservation/management_ui/templates/management_ui/policy_detail.html),
the browser suite was re-run (7 passed, tag sar037a-shots2) and all 26 PNGs
re-captured and re-viewed. The re-captured policy-detail-1440 renders
"30 to 2880 minutes (30 minutes - 2 days)". No further defects found in the
26 captures (labels, nearby help, no horizontal overflow at 1440/390,
readable long help text, admin copy free of forbidden substrings).

Artifacts (private root home, NOT copied to Git):
/home/ubuntu/codex-supervision/slaif-asset-reservation/workorders/037a-screenshots/
with sha256.txt alongside. Final hashes (post-fix round):

| File | SHA-256 |
|---|---|
| reserve-1440.png | f8415925bba45ab592f4420f06bbc8510d2dbc7fc8a6fb17bbe20bfe97fb0040 |
| reserve-390.png | 0065975699854e0bcf0282000d4628cbf201c61947ecdcbdec22c2e843c4a0ff |
| profile-1440.png | 43fa5079223a2e549273a33351717ad97b020ad91741bdd7bc1b663e63084ab9 |
| profile-390.png | 3e24ae9b83118ff5b2638332c435f8b2b5b74103ae347c3897c8d9a5ea0c6f30 |
| token-create-1440.png | 96987dd73f802ec513e356d7c71a656123d8ba97be92bd1eccd552f76d599cdf |
| token-create-390.png | 29bd60ff22d19c6ffdb2537d9153c8530cd9356b6c6f5beff18b50ce1c9ef6c1 |
| asset-filters-1440.png | 9867752dd6e856e4a8da540c5d9b5cbbc6cf2c93a1b02b87524badbb94325680 |
| asset-filters-390.png | 5e76710c54f51abefbfd3e63e4e208fbabfbfe9a1c00373900ef303e6384464c |
| asset-availability-1440.png | 524746360b75a5545172c532914a437df2b341f327d4a5561ff9531f39b1037c |
| asset-availability-390.png | a3be8007c5451dc0ab9f74e8a8082451a5cb19059936c985073e6e9ccdb1c32b |
| policy-form-1440.png | 25f73c73b3b3a857780795f746c1759a106aec61ac810c41384d3ed034418c0e |
| policy-form-390.png | b194bde03ceb18d9b2c9feb4193c4447fb937f27c46dc5098224a3dfc5d3a07b |
| policy-detail-1440.png | 27b965316b58a7394eb0c238af9bbc8658db6122519e16a8e025bb39e224c953 |
| blackout-form-1440.png | 926c73a1f69638690b2ea89a13dec37a036a6f82d164f67257faac95b9b57849 |
| blackout-form-390.png | 9a0280107d0c5a9fe1d0104e7b609f21ae8e8c43856ec2d711875b1a82dc7041 |
| reservation-filters-1440.png | e23fbc4e5cfa83e33ef55836a26e2735edfefcb6d28565805802e50b098462ca |
| reservation-filters-390.png | 9a04b6d0f12e75eb2e35bf1f7035f1a79629849cacea77c9663049e843c2a18f |
| audit-filters-1440.png | b7a012b2fce32ee8463693ce73b30ef12e19406b25b35905f0d3b065e805ebef |
| audit-filters-390.png | 6e6a5e93a5e6403cb1338ffa469cce443567fd060f6664056b72ab67cee0b703 |
| admin-login-1440.png | 3a3ebdeec32f7ecd2976c332228c7c7909360ff6c98112b73bc910b82263895a |
| admin-user-add-1440.png | 66962279fac812459f88a8755ce516b7257dc60f33753bad6f1cbbcb32fb3bf8 |
| admin-user-change-1440.png | f444f4932e35f537a236809a1d58e7a8a2c29adff1e36e1435affe7c48c97d88 |
| admin-password-change-1440.png | 554f2d9876a53c50f175f124d327e331046d831663321d5070c21e9de33502f6 |
| admin-group-add-1440.png | 213bc6ee997a43662694532db36e655c66ca8cfaa24c4337cbf68de2f019fdf5 |
| admin-asset-add-1440.png | fed71cf3f721d00b66182ca5abacce15ddd6cd1965267ad6c4b9a581dfd8aa89 |
| admin-asset-change-1440.png | fa674decba12a1a45ea4d5b370c4c7d5230e2676fc3d7d2d87b72da4dd088a49 |

Re-capture hash deltas vs the first round: policy-detail-1440 (the fix),
reservation-filters-1440 (per-run seeded synthetic reservation UUID/start
time in the fixture table) and admin-asset-add-1440 (rendering variance,
visually identical). All three were re-viewed; synthetic fixtures only —
no token, password, verifier, CSRF, cookie, raw HTML, trace or private data
in any capture.

## 8. Docs, CI and publication (acceptance 8)

- Task-oriented docs updated without execution ledgers, private fixture
  ports or receipt paths in developer/operator guides: TESTING.md (new-suite
  guidance), docs/human-ui.md, docs/api-contract.md (display labels vs
  unchanged wire values), docs/ux/form-guidance-inventory.md.
- CI at first implementation head dca50cb: CI run 37264782617 — quality
  success (20s), security success (14s), container success (30s), test
  success (8m59s); oap run 37264782600 — oap-harness success (37s). All five
  checks passed.
- CI at exact implementation head cc8dbbb: CI run 37266125105 — quality
  success (15s), security success (18s), container success (35s), test
  success (9m14s); oap run 37266125111 — oap-harness success
  (39s). All five checks passed; no missing/skipped/cancelled check. The
  exact-head `test` job is the full-suite coverage for cc8dbbb.
- Report-head CI: NOT YET OBSERVED AT AUTHORING; its outcome goes to the
  private execution receipt, never to this immutable report.
- PR #74 for issue #73 (body ends `Closes #73`); coding never merges.

## Failures, uncertainties, limits

- No test failures at either head. One presentation defect was found by
  actual screenshot viewing (policy-detail Duration row rendered
  "30-to 2880 minutes") and fixed before the implementation head was
  finalized; the fix is a one-line template spacing change with no
  behavioral effect (all pre-existing assertions, including "2880 minutes"
  and "2 days", stayed green).
- Local full-suite evidence (864 passed, 741.6s) is at dca50cb; the
  single-line presentation fix in cc8dbbb is covered locally by the focused
  (159), new server (22) and new browser (7) runs plus the exact-head CI
  full `test` job.
- Two of the 26 re-captured screenshots differ from the first round only by
  per-run seeded fixture data or rendering variance and were re-viewed as
  visually identical.
- This report claims no strategic acceptance, no production/exposure
  change, no DHA candidates. No credentials, verifiers, peppers, cookies,
  CSRF values, tokens or private data appear in this report or in any
  captured artifact. Decision: NONE stands.
