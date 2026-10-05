<!-- OAP-META
{
 "kind": "report",
 "id": "037-b",
 "order_path": "oap/orders/037-b-guidance-accuracy-closure.md",
 "order_sha256": "1278c4e8f42adaf2b6880e1b0f39056801f60487fb92f91471364be228b8fee8",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 73,
 "pr_number": 74,
 "branch": "codex/73-oap-037-a-form-guidance",
 "implementation_head": "6bd5e1960ae4702e9996e0fd383548d218d2b744",
 "previous_implementation_head": "2d50e3627e4bf04f4a5e8a595d883602b55297e7",
 "base_sha": "c4703beacf9c887d7ccfb59c89af4f389bdb57ed",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "6bd5e1960ae4702e9996e0fd383548d218d2b744",
  "runs": [
   {
    "run_id": 37292761571,
    "workflow": "CI",
    "jobs": {
     "quality": "success",
     "test": "success",
     "security": "success",
     "container": "success"
    }
   },
   {
    "run_id": 37292761690,
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

# 037-b — Guidance accuracy and required browser coverage

Implementation head SHA: 6bd5e1960ae4702e9996e0fd383548d218d2b744
Report publication commit: SELF

Result: COMPLETE for all eight 037-b acceptance items. Same objective,
round, branch codex/73-oap-037-a-form-guidance, issue #73 and PR #74
(AMEND); base c4703beacf9c887d7ccfb59c89af4f389bdb57ed unchanged.
Recovery note: the first 037-b client was interrupted by a provider
image-count rejection (16-image prompt limit) after committing
2d50e3627e4bf04f4a5e8a595d883602b55297e7; that commit and the working
tree were preserved, no reset/renumber/order rewrite. The 037-b change
set vs the 037-a report head is 13 files, every one inside the order
allowed_paths; zero changes under models/, migrations/, services,
policy evaluator, parsers, validators, admission, crypto, API/wire
contracts, inventory or dependencies. Coding never merged; the PR stays
open for strategic/human acceptance.

## 1. DST occurrence help (acceptance 1)

- web/forms.py (member reservation) and management_ui/forms.py (staff
  blackout) now state the real rule on both start and end occurrence
  pickers: on a fall-back day the clock time repeats and Automatic is
  rejected — choose First (earlier) or Second (later); a spring-forward
  gap time does not exist and is always rejected. The previous "Automatic
  uses the system default" wording (inaccurate: interpret_local_wall_time
  rejects ambiguous times with omitted fold; Automatic has no
  ambiguous-time default) is removed from both forms and from
  docs/human-ui.md and the inventory.
- Parser, choice wire values and validation are untouched.
- Rendered tests: an invalid ambiguous-Automatic POST on BOTH forms keeps
  the corrected help on the re-rendered page (reservation and blackout);
  form-level tests prove the explicit choices pick the two real instants
  (2025-10-26T02:30 Europe/Ljubljana fold 0 = 00:30Z, fold 1 = 01:30Z)
  and that a nonexistent spring-forward time (2025-03-30T02:30) is
  rejected for no fold, fold 0 and fold 1.

## 2. Asset/admin help corrected against source (acceptance 2)

- AssetAdminForm: parent help states only a machine can be a child's
  parent and a machine itself never has a parent (validation
  "A child asset parent must be a machine" preserved and probed); slug
  help no longer claims URL breakage (current detail/API routes use
  UUIDs; the slug is a unique display/search label); kind help states
  only machines take children; timezone help states it is stored display
  metadata while availability uses each member's profile timezone.
- ReservationPolicyForm.name help no longer invents name uniqueness:
  names are not unique; only the active-target constraints hold (one
  active policy per exact asset, one active global).
- Inventory and docs reconciled; the legacy read-only field help
  constants removed from AssetAdminForm because those fields are
  excluded from the form (the inventory now says no field help renders,
  readonly context explained) — no model/help-field additions.

## 3. Admin user help (acceptance 3)

- password1 add-form help: members cannot change their own password;
  /profile/ edits display name and timezone only; the administrator sets
  or changes passwords from the user page (no self-service route exists).
- is_staff/is_superuser/groups/user_permissions help state the real
  effects: entry follows the active staff flag with an active,
  non-service-account session (not arbitrary permission selections);
  individual/group permissions control per-model administration only;
  superuser does not bypass the active-human/staff admission gate.
  No authorization changes (unchanged role/admission negative suites
  pass).

## 4. Inherited admin inventory and password form (acceptance 4)

- last_login and date_joined are editable (as in Django 5.2) and now
  carry real help (UTC meaning, sign-in-update semantics, correction
  impact; created_at stays the immutable product record). Because
  Django's admin template gives a MultiWidget help div no id, the
  rendered help was dangling; the WIP adds a presentation-only
  _BoundHelpSplitDateTime widget so the help div gets id_<name>_0_helptext
  and the sub-input's own aria-describedby binds it (no rendering,
  format or behavior change; POST shape last_login_0/_1 unchanged).
- SlaifAdminPasswordChangeForm is now actually wired through the correct
  Django class attribute (change_password_form; the 2d50e36 draft set
  the unused password_change_form, so the first implementation commit
  did not apply the custom help — caught by the focused run and fixed in
  6bd5e19). usable_password help states the product truth: disabling
  loses the current password and blocks password sign-in; this
  deployment provides no other human login backend; the built-in warning
  is preserved verbatim. The RadioSelect help div gets no id from
  Django's template, so it is documented as visible-adjacent-unbound
  instead of claiming a binding.
- New behavior tests: GET help wording + invalid (mismatched) POST
  rejected with hash intact; enable path sets a real password through
  the unchanged validators; disable (unset-password action) removes the
  password; safe disabled status re-renders.

## 5. human_duration and default-policy presentation (acceptance 5)

- form_guidance.human_duration preserves remainder minutes for every
  nonzero remainder including days (1441 -> "1 day, 1 minute", 1501 ->
  "1 day, 1 hour, 1 minute", 2890 -> "2 days, 10 minutes"); boundary
  test covers 0/1/59/60/90/1440/1441/1501/2880/2881/2890 plus
  non-numeric/negative no-ops. Stored units and evaluator unchanged.
- Policy detail with non-round minutes renders
  "1441 to 2890 minutes (1 day, 1 minute - 2 days, 10 minutes)" and
  humanized lead/cutoff.
- The fresh-install default minimum is 1 minute (source constant), not
  30: a new test calls the REAL initializer
  (reservations.initialization.initialize_default_policy) and asserts the
  policy detail renders "1 to 2880 minutes (1 minute - 2 days)". The
  30-minute browser fixture is renamed guidance-custom so the captured
  evidence is identifiable as custom, never the fresh default.

## 6. Required browser coverage (acceptance 6)

- tests/browser/test_form_guidance_browser.py now covers every admin
  surface at BOTH 1440 and 390: login, user add (full-page), user
  change (full-page), password change, group add (full-page), asset add
  (full-page), asset change (full-page), tag add — 35 captures total.
- The nearby-help helper is substantive: visible control, visible help,
  the control's OWN aria-describedby binding, same real field container.
  For the two documented unbound cases (RadioSelect help div without id;
  select-filter lists replaced by the admin JS) an unbound variant
  asserts visible adjacent help inside the same container.
- Long admin forms are captured full-page so below-fold guidance and
  actions are in the evidence. Fixtures are safe synthetic values;
  no credential/verifier/token/CSRF/cookie/HAR/trace material is
  captured (the one-time token page is never screenshotted).
- Actual visual inspection of the final captures: 22 new/changed images
  plus admin-login-1440 (byte-identical to 037-a, re-viewed for surface
  completeness) were ACTUALLY viewed in three fresh independent
  read-only CODING visual contexts (8/8/7 images, at or under the
  16-image provider prompt limit; each a separate CLI context, no
  accumulated images), all reporting NO ISSUES (labels, nearby help,
  readability, no horizontal overflow, no misleading guidance, no
  framework text). The remaining 12 captures are sha256-identical to
  the final 037-a capture set that STRATEGIC reviewed, so their prior
  visual validity is preserved by hash match. Paths and sha256:
  workorders/037b-screenshots-final/ (private root home, not in Git).

## 7. Inventory/docs reconciliation (acceptance 7)

- docs/ux/form-guidance-inventory.md: unreachable legacy controls
  (assets app staff views/templates/staff REST endpoints not included by
  config.urls) classified as UNREACHABLE — no current field coverage
  claimed, no routes added; the two documented unbound cases are stated;
  legacy read-only help constants described as skipped by design.
- docs/api-contract.md: scope effect lines exist only on the token
  creation form; the token list and one-time display show labels only
  (matches the templates).
- docs/human-ui.md and TESTING.md updated to the corrected semantics;
  task-oriented, no execution ledgers or private paths in developer
  guides. Changed-doc relative links checked (one existing link to
  decisions/0016 in api-contract.md, target present).

## 8. Tests, CI and publication (acceptance 8)

All product pytest/management qualification ran on the owned disposable
source clone (scratch checkout at the exact final bytes; owned PG17
container per the 033-b receipt, validated by exact container ID and
nonce; private env parsed into the child process dict, never printed;
OAP_ROLE cleared; owned DB name; PYTHONPATH from the clone). Nothing was run from
the valuable repo root.

- Server suite `pytest tests/test_form_guidance.py`: 30 passed in 3.24s
  at the final bytes (was 22 in 037-a).
- Focused operational neighbors (test_form_guidance,
  test_web_human_mvp, test_management_ui, test_assets_admin,
  test_product_entry, test_proxy_security,
  test_reservations_concurrency): 167 passed, 1 warning (the
  pre-existing intentional override_settings UserWarning in
  test_product_entry.py) in 15.92s.
- Browser suite `--browser chromium tests/browser/test_form_guidance_browser.py`:
  7 passed in 15.47s; 35 captures regenerated from the final bytes.
- ruff check, ruff format --check and mypy strict (131 source files)
  clean; manage.py check (0 issues) and makemigrations --check (no
  changes) clean on the owned clone; git diff --check clean.
- Full-suite coverage for the implementation head comes from the
  exact-head CI `test` job; the unchanged local full suite was NOT
  repeated.
- CI at implementation head 6bd5e19: - CI at implementation head 6bd5e1960ae4702e9996e0fd383548d218d2b744:
  CI run 37292761571 — quality success (20s), security success (18s),
  container success (43s), test success (9m05s); oap run 37292761690 —
  oap-harness success (40s). All five checks passed at the exact head;
  no missing/skipped/cancelled check. The exact-head `test` job is the
  full-suite coverage for 6bd5e19..
- Report-head CI: NOT YET OBSERVED AT AUTHORING; its outcome goes to the
  private execution receipt, never to this immutable report.
- PR #74 for issue #73 (body ends `Closes #73`); coding never merges.

Precise head-versus-development results (superseding 037-a's overbroad
"No test failures at either head" wording for this round): the first
037-b implementation commit 2d50e36 was NOT green — the focused server
run at that commit failed on the admin help bindings (dangling
aria-describedby on last_login/date_joined and usable_password) and on
the password form not being wired (wrong class attribute); those
failures were repaired in 6bd5e19, at which head every suite above
passes. No failures remain at the final head.

## Failures, uncertainties, limits

- No test failures at the final implementation head. Two minor
  out-of-scope observations were noted during actual image viewing and
  are reported, not fixed (038 theme scope; not guidance defects):
  (1) the per-user password-change page breadcrumb root renders Django's
  default "Home" while every other admin page renders the custom
  "Administration" (the project overrides breadcrumbs per template and
  has no admin/password_change_form.html override — reproduced
  server-side); (2) the admin login button renders uppercased "LOG IN"
  at 390px vs "Log in" at 1440px (CSS text-transform).
- 12 of 35 captures are byte-identical to the 037-a reviewed set and
  were not re-viewed; their validity is the 037-a review plus hash
  match. reservation-filters-1440 and the reserve captures differ from
  037-a also by per-run seeded synthetic fixture data (UUIDs/times);
  they were re-viewed.
- Local full-suite evidence is not repeated by order design; the
  exact-head CI `test` job is the full-suite coverage for 6bd5e19.
- This report claims no strategic acceptance, no production/exposure
  change, no DHA candidates. No credentials, verifiers, peppers,
  cookies, CSRF values, tokens or private data appear in this report or
  in any captured artifact. Decision: NONE stands.
