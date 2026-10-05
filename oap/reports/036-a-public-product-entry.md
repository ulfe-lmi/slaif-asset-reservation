<!-- OAP-META
{
 "kind": "report",
 "id": "036-a",
 "order_path": "oap/orders/036-a-public-product-entry.md",
 "order_sha256": "f20d77a1d582f056804305a354d0ef127a46c945cbe88709ffab4d506ac35b20",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 71,
 "pr_number": 72,
 "branch": "codex/71-oap-036-a-public-product-entry",
 "implementation_head": "0e2d45d6d62f50f2c5e930efe9fa4b5557f551ae",
 "previous_implementation_head": null,
 "base_sha": "e87497a1169bf4745489f699c28377bfbd2df717",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "0e2d45d6d62f50f2c5e930efe9fa4b5557f551ae",
  "runs": [
   {
    "run_id": 37250278796,
    "workflow": "CI",
    "jobs": {
     "quality": "success",
     "test": "success",
     "security": "success",
     "container": "success"
    }
   },
   {
    "run_id": 37250278795,
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

# 036-a — Public product entry and browser identity

Implementation head SHA: 0e2d45d6d62f50f2c5e930efe9fa4b5557f551ae
Report publication commit: SELF

Result: COMPLETE for all nine 036-a acceptance criteria. Development only
(M-INTERNET-UX-PILOT); no deployment, no real exposure, no merge. PR #72
(issue #71), CREATE_OR_RESUME mode, base e87497a1169bf4745489f699c28377bfbd2df717
(origin/main at activation). One bounded purpose: public entry and structural
product identity; full form help (037) and theme/override mechanism (038)
deliberately not implemented.

Environment (all product pytest/management qualification): owned disposable
source copies in unique tmp checkouts (one `git archive` copy, one local
clone of the committed head), owned PG17 loopback cluster (port 34421, 033-b
receipt), unique owned test databases per run, Chromium; product-test child
envs with `OAP_ROLE` cleared and explicit PYTHONPATH/settings/DB URLs. No
product pytest or management command ran from the valuable checkout
(lint/types/git publication only).

## Acceptance evidence

1. Anonymous public landing — `GET /` for anonymous renders
   `web/landing.html`: packaged SLAIF logo, "SLAIF Asset Reservation" title
   and heading, one-paragraph shared-lab purpose, and two exact actions,
   `Log in` (href `/login/`) and `Administration` (href `/admin/`), present
   in both the primary navigation and the hero CTA row; keyboard reachability
   asserted by Tab walk. No member workflow menu for anonymous (no
   "My reservations"/"API tokens"/`/assets/`). Private synthetic canaries
   seeded (distinct user email+name, asset name, tag, purpose, token name,
   user UUID) are asserted absent from the rendered output
   (`test_anonymous_landing_shows_product_identity_and_ctas`,
   `test_anonymous_landing_discloses_no_private_canaries`,
   `test_browser_anonymous_landing_identity_and_ctas`,
   `test_browser_public_surfaces_disclose_no_private_canaries`). PASSED.
2. Authenticated navigation — `web.views.root` keeps the `/` route name
   `dashboard` stable; anonymous goes to the landing, authenticated or
   session-bearing requests go to the existing `dashboard()` with its
   unchanged `active_human_required` boundary, so inactive/service-account
   sessions are still rejected/terminated on `/` (no redirect loop; asserted
   with `follow=True` chains). Member nav shows the member menu only; staff
   additionally sees Management and Administration; anonymous nav shows the
   public actions only. Administration login rejects inactive and
   service-account identities with the same human boundary and generic
   denial (`SlaifAdminAuthenticationForm`), while normal active staff
   permissions are exactly intact (admin index changelist permissions
   unchanged; protected models remain read-only). PASSED
   (`test_root_dispatches_by_role_without_redirect_loops`,
   `test_disallowed_sessions_still_terminate_on_root`,
   `test_admin_login_rejects_non_human_identities`,
   `test_browser_staff_navigation_management_and_admin_index`,
   `test_browser_admin_login_rejects_service_accounts`,
   `test_browser_member_is_denied_administration_content`).
3. Custom AdminSite/configuration — `config/admin_site.py`
   (`SlaifAdminSite`: site_title/site_header "SLAIF Asset Reservation
   administration", index_title "SLAIF Asset Reservation site administration")
   wired via `config/apps.AdminConfig` `default_site`; structural branding
   block (logo, site name), product breadcrumbs ("Administration") in six
   overridden admin templates, footer identity, favicon; no CSS hiding, no
   weakened editing (model registrations, permission checks,
   protected/read-only mutation boundaries and `accounts/admin.py`
   untouched; browser test asserts the Api-token model stays read-only in
   the admin index). The Administration CTA is visible from the landing
   without URL guessing. PASSED (unit + browser evidence above;
   `test_browser_admin_index_lists_protected_token_model_readonly`).
4. No framework branding — "Django"/"Django administration"/"Django site
   admin"/"Django REST framework"/"Powered by Django" asserted absent in
   titles and body of `/`, `/login/`, `/admin/login/`, member pages,
   `/manage/`, `/admin/` and the Browsable API, in unit and real-browser
   forms. The existing DRF Browsable API is customized structurally:
   `SlaifBrowsableAPIRenderer` (template `web/browsable_api.html`, title
   "SLAIF Asset Reservation API") appended after the unchanged
   JSON-first renderer list; JSON contract, controls, actions, auth and
   permissions retained (asserted: `renderers[0]` is JSONRenderer,
   `renderers[-1]` is the custom renderer, JSON root body unchanged, HTML
   root shows the product title and working format controls; no HTML
   disabling, no new anonymous API/docs). PASSED
   (`test_no_framework_branding_on_browser_surfaces`,
   `test_browsable_api_identity_and_json_compatibility`,
   `test_browser_browsable_api_html_and_json_controls`,
   `tests/test_api_schema.py` browser-identity test).
5. Branded error surfaces — handler400/403/404/500 and `csrf_failure`
   render one shared data-free template `web/error.html` (no user/message/
   session access; fixed safe copy; no traceback/reason/query text); a real
   missing route serves the branded 404 and CSRF rejection shows the branded
   403 without the word "CSRF". Rendering stays correct when the database is
   unreachable (unreachable-DB override + fresh client, asserted). The
   existing login 429/503 pages now render the same branded template
   (allowed path, identity/template only): status, `Retry-After`,
   `Cache-Control: no-store` and all counter behavior are byte-identical
   (atomic multi-connection budget test and header assertions pass
   unchanged); API 429/503 problem-JSON contract unchanged. Health endpoints
   untouched. PASSED (`test_branded_generic_error_handlers`,
   `test_csrf_failure_is_branded_without_reason`,
   `test_error_rendering_is_safe_when_db_is_unavailable`,
   `test_browser_csrf_failure_is_branded`, `test_abuse_controls.py`
   login-budget/budget-unavailable tests).
6. Token-template stale claims — the three token templates no longer carry
   the stale Work Order 0006/API-not-enabled prose; they now point to the
   current scoped bearer API under `/api/v1/`. One-time secrecy, no-store/
   private/no-referrer, history scrubbing, validation, scope semantics,
   expiry and revocation logic are untouched (asserted in
   `test_token_pages_carry_current_scoped_api_guidance`; the pre-existing
   token-security suites pass unchanged in the full suite). PASSED.
7. Entry/admin identity layout — modest coherent layout from existing
   server rendering: brand header + role-aware nav, landing hero with clear
   CTA hierarchy (primary Log in / secondary Administration), value cards,
   branded admin login/index; the official SLAIF logo is packaged locally
   (`web/brand/slaif-logo.svg`, SHA-256
   `3f810f1ef7fb327daf938a5302fe432e88be6a9df3d29c1b53da063cbd4d9b29`,
   fetched 2026-10-05 from https://www.slaif.si/assets/slaif-logo.svg,
   inspected: no scripts or remote references) and documented in
   `docs/branding.md` without rights/funding claims; no hotlinked
   runtime-critical assets, no new frontend or dependencies
   (pyproject/uv.lock/Dockerfile/compose unchanged). Responsive at 1440/390
   with no unintended horizontal overflow (asserted on every browser
   surface) and visible focus outlines. During the screenshot review one
   pre-existing header spacing defect (timezone banner unaligned with the
   new header container) was found and corrected with a scoped
   `.timezone-banner` rule in `site.css`; screenshots were re-captured and
   re-viewed at the implementation head. PASSED (evidence 8 + docs).
8. Playwright route/role matrix and screenshots — 10 real-app Chromium
   tests: anonymous landing identity/CTAs/keyboard, member login to
   dashboard, Administration action to admin login, staff Management +
   admin index, member denial of administration content, admin login
   service-account denial, Browsable API HTML+JSON controls, branded CSRF
   failure, no-private-canary on public surfaces, admin index protected
   token model read-only. 10 passed at the implementation head (15.01 s).
   Nine privacy-safe screenshots (landing 1440/390, member login 1440,
   member dashboard 1440/390, admin login 1440/390, admin index 1440/390)
   were actually viewed by coding and iterated (criterion 7 fix) before the
   final head; no screenshots of one-time secrets, password verifiers, raw
   HTML/HAR/cookies/traces; synthetic fixtures only. Private artifact paths
   for STRATEGIC review:
   `/home/ubuntu/codex-supervision/slaif-asset-reservation/workorders/036a-screenshots/{landing-1440,landing-390,member-login-1440,member-dashboard-1440,member-dashboard-390,admin-login-1440,admin-login-390,admin-index-1440,admin-index-390}.png`.
   PASSED.
9. Docs, exact-head CI, report — QUICKSTART step 6 now documents the public
   landing and its two actions; docs/human-ui.md gains a short Public entry
   subsection; docs/api-contract.md gains a one-line browser-identity note
   for `GET /api/v1/`; new docs/branding.md documents the packaged logo
   source/identity; TESTING.md records this round's evidence. Changed
   Markdown links and image paths checked (logo path exists under
   `web/static/web/brand/`). No product-readiness claim, no OAP ledger, no
   canonical governance change. Exact implementation-head CI: all five
   required checks SUCCESS at 0e2d45d (below). Report-head CI: not yet
   observed at authoring (see below). PASSED.

## Commands and results

- Focused (owned env): `pytest tests/test_product_entry.py
  tests/test_abuse_controls.py tests/test_web_human_mvp.py` — 61 passed
  (11.94 s); browser `pytest --browser chromium
  tests/browser/test_product_entry_browser.py` — 10 passed pre-head and 10
  passed (15.01 s) at the implementation head.
- Full local suite, pre-commit working tree (owned clone, owned DB):
  822 passed, 6 failed — the six failures were all in
  `tests/test_https_boundary.py`, which by design builds its image from a
  tracked-file snapshot; with the new files still uncommitted the snapshot
  lacked them (the order requires committing implementation before
  Docker tracked-snapshot qualification). Not a code regression.
- Rehearsal family at the committed implementation head (owned clone reset
  to 0e2d45d, owned DB): `pytest tests/test_https_boundary.py
  tests/test_operational_hardening.py` — 43 passed, 1 skipped (407.55 s);
  the single skip (`test_rehearsal_snapshot_excludes_ignored_sentinels`)
  was triggered by leftover synthetic fixture residue from a killed
  in-progress run in the same owned checkout; after removing that owned
  residue the test passed on rerun (5.27 s). Equivalent: 44 passed, 0
  failed at the implementation head locally.
- Gates: `ruff check .` and `ruff format --check .` clean; `mypy src` clean
  (130 files); `manage.py check` 0 issues; `makemigrations --check
  --dry-run` clean; `spectacular --validate --fail-on-warn` clean (owned
  copies); `git diff --check` clean.
- CI at implementation head 0e2d45d6d62f50f2c5e930efe9fa4b5557f551ae
  (observed before authoring): CI run 37250278796 — quality success,
  test success (full suite: 828 passed, 1 warning in 469.04 s), security
  success, container success; oap run 37250278795 — oap-harness success.
  No missing/skipped/cancelled check. Report-head CI: NOT YET OBSERVED AT
  AUTHORING; it is required and its outcome goes to the private execution
  receipt, never to this immutable report.

## Failures, uncertainties, limits

- No open failures at the implementation head. The only local failures were
  the by-design tracked-snapshot artifact above (resolved at the committed
  head) and the residue-induced skip (removed and re-passed).
- The admin login header wraps to two lines at 1440 (logo + full site
  header in the standard admin login box); readable, no overflow; left as
  structural customization rather than shortening the site header.
- Visual quality is a STRATEGIC review gate: the nine private screenshots
  are provided for that review; coding does not claim release or visual
  acceptance.
- No DHA candidates arose; the order's Decision: NONE stands. No
  credentials, verifiers, peppers, cookies, CSRF values, tokens or private
  data appear in this report, the screenshots, or any captured output
  (sentinel checks included in the rehearsal runs).
