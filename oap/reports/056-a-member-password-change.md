<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "056-a",
  "order_path": "oap/orders/056-a-member-password-change.md",
  "order_sha256": "29dbddf5b80f35121a1ed14206a024de1ceffd7ab32f18f25536657d06e6845a",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 116,
  "pr_number": 117,
  "branch": "codex/116-oap-056-a-member-password-change",
  "implementation_head": "e5f2cb94dcc5f4a10cfe3b832ad18b203abfbf86",
  "base_sha": "bfc6efd2beeeeebe9df794cdbfc0e93b38ddfff0",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "e5f2cb94dcc5f4a10cfe3b832ad18b203abfbf86",
    "runs": [
      {
        "run_id": 42899487881,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "test": "success",
          "security": "success",
          "container": "success"
        }
      },
      {
        "run_id": 42899487414,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1316 passed, 1 warning in 521.61s (0:08:41)",
    "warning": "tests/test_product_entry.py:568 UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unrelated)",
    "oap_harness_summary": "Ran 160 tests in 29.198s - OK"
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 056-a — execution report: logged-in member password change

Implementation head SHA: e5f2cb94dcc5f4a10cfe3b832ad18b203abfbf86
Report publication commit: SELF

## Identity and result

COMPLETE for order 056-a (D0, `Decision: NONE`), a fresh objective round (CREATE_OR_RESUME,
new issue #116 / PR #117 / branch
`codex/116-oap-056-a-member-password-change`), exactly as ordered. Before the first write, all
nine order `source_hashes` were verified SHA-256-byte-identical against base
`bfc6efd2beeeeebe9df794cdbfc0e93b38ddfff0` (which equals `origin/main` at start):
ARCHITECTURE.md `f7b5c988...`, PLAN.md `e15eb06f...`, ARCHITECTURE-for-agents.md
`66d578e9...`, web/forms.py `c90d7590...`, web/views.py `3c184029...`, web/urls.py
`16bfe798...`, accounts/admin.py `ad8e1610...`, docs/human-ui.md `b63b7943...`,
docs/security-model.md `7fcd7abf...`. Governance revision
`14fc20b1ff52788974fd3f282322afc9d71362f9` is in main's history. The single
implementation commit `e5f2cb94dcc5f4a10cfe3b832ad18b203abfbf86` (first parent exactly the
base `bfc6efd2beeeeebe9df794cdbfc0e93b38ddfff0`) changes exactly the fourteen allowed
non-report paths:
`src/slaif_reservation/web/forms.py`, `src/slaif_reservation/web/views.py`,
`src/slaif_reservation/web/urls.py`,
`src/slaif_reservation/web/templates/web/profile.html`,
`src/slaif_reservation/web/templates/web/password_change.html` (new),
`src/slaif_reservation/accounts/admin.py`,
`tests/test_member_password_change.py` (new),
`tests/browser/test_member_password_change_browser.py` (new),
`tests/test_form_guidance.py`, `tests/browser/test_form_guidance_browser.py`,
`docs/human-ui.md`, `docs/security-model.md`, `oap/active`,
`oap/orders/056-a-member-password-change.md`.

The foreign PR113 (`fix/booking-start-grace`, overlapping web/forms.py, web/views.py and
docs/human-ui.md) was inspected read-only before editing and was NOT edited, amended,
merged or reset by this round; the overlapping edits here are in disjoint regions
(password-change vs ten-minute reservation-start grace).

## Numbered acceptance evidence

1. **Route and admission.** `GET+POST /profile/password/` registered as
   `web:password-change` (web/urls.py), guarded by the existing
   `@active_human_required` decorator; the Profile page renders an obvious
   "Change your password" action. Focused tests: anonymous GET and POST are 302-denied to
   login; an already-authenticated inactive user and a service account are denied and their
   sessions terminated (session cleared, no loop); a Bearer-token-only request (valid
   `reservations:read` scope, no session) is 302-denied to login on both GET and POST with no
   DB change. PASSED (Django test client, real PostgreSQL17 test DB).
2. **Standard validation, CSRF, no weakened path.** The view uses
   `MemberPasswordChangeForm(PasswordChangeForm)` — Django's stock current-password check,
   normal validator set and hashing; the page renders the site validator list (including the
   existing minimum length) as nearby help. Tests: wrong current password, mismatched new
   passwords, missing fields, and weak new passwords (too-short, common, entirely numeric)
   all re-render with 200 and leave the stored hash byte-identical; a forged POST without a
   CSRF token under `enforce_csrf_checks` is 403 with no DB change. The view carries
   `@sensitive_variables("form")`; no audit event is created (no signals; audit module
   unchanged); the success message is the nonsecret "Password changed." PASSED.
3. **Session semantics and self-only mutation.** On success `form.save()` +
   `update_session_auth_hash(request, form.user)` then redirect to `/profile/`. Tests: the
   stored hash updates, `authenticate()` with the old password returns None and with the new
   one returns the user, the acting session still reaches `/profile/` (200) with the
   nonsecret notice, and a second independent session for the same account is 302-denied to
   login afterwards. A different account's hash and credential are untouched. The form is
   always bound to `request.user` (no user parameter), so no other account can be targeted.
   PASSED.
4. **Admin help and docs truth.** Only the now-false Administrator add-form password1 claim
   was replaced ("The member can later change their own password from the profile page; an
   administrator can also set or change it from this user page"); the admin per-user
   set/change action, `SlaifAdminPasswordChangeForm` and the appended validator help are
   unchanged. `docs/human-ui.md` (sign-in section + members table row) and
   `docs/security-model.md` (human sessions section) now describe the self-service change
   while keeping public forgotten-password reset, email onboarding and OIDC explicitly
   deferred. No model/migration/settings/proxy/dependency/API change:
   `manage.py makemigrations --check --dry-run` reports "No changes detected", and the
   generated OpenAPI schema is byte-identical to main's (spectacular
   `--validate --fail-on-warn` clean on both trees). PASSED.
5. **Focused Django + Chromium evidence and CI.** 14 focused Django tests
   (`tests/test_member_password_change.py`) PASSED; the real
   Chromium/HTTP/PostgreSQL browser test
   (`tests/browser/test_member_password_change_browser.py`) at desktop 1440 and mobile 390
   PASSED: Profile link, labeled guided fields with bound `aria-describedby` help,
   wrong-old-password validation, successful change with current-session continuity
   (member route reachable without re-login), no horizontal overflow, no framework branding,
   no credential value or hash material anywhere in the pages; three privacy-safe screenshots
   (`member-password-change-1440`, `member-password-change-error-1440`,
   `member-password-change-390`) were captured and inspected — no tokens, passwords, CSRF,
   cookies or private data present. Existing member/login/profile/admin/browser suites and
   the two form-guidance assertions updated only where the old add-form text became false.
   Normal five CI checks at the exact implementation head
   `e5f2cb94dcc5f4a10cfe3b832ad18b203abfbf86`: quality success (18s), test success
   (9m38s; "1316 passed, 1 warning in 521.61s (0:08:41)"; the warning is the pre-existing
   intentional DATABASES-override negative in test_product_entry.py), security success
   (15s), container success (27s; UID:GID 10001:10001, static/bootstrap files present),
   oap-harness success (35s; "Ran 160 tests in 29.198s - OK") — runs 42899487881 (CI) and
   42899487414 (oap). Report-head CI is NOT YET OBSERVED AT AUTHORING and is reported
   separately when observed. No code publication to real deployment; no D2 crossing.

## Local exact-head runs (evidence index, not CI)

- `uv sync --locked --all-groups` PASSED; `uv run ruff check .` PASSED;
  `uv run ruff format --check .` PASSED; `uv run mypy src` PASSED;
  `git diff --check` PASSED.
- `uv run --env-file .env python manage.py check` PASSED (0 issues);
  `uv run --env-file .env python manage.py makemigrations --check --dry-run` PASSED
  (no changes).
- `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test
  tests/test_member_password_change.py` → 14 passed (real PostgreSQL17 test DB).
- `uv run --env-file .env pytest --ds=... tests/browser/test_member_password_change_browser.py --browser chromium`
  → 1 passed (real Chromium/HTTP/PostgreSQL).
- Full local `uv run --env-file .env pytest` at the implementation head: 1306 passed,
  9 skipped, 1 failed in 706.82s. The single failure is
  `tests/oap/test_ba38_39_tmux_config.py::Ba39OperationPrereqs::test_ba39_strategic_same_prerequisites`
  — a pre-existing local-environment failure: an unmodified archive of `main`
  (`bfc6efd2...`) fails it identically on this host, the test and all oap/bin machinery are
  untouched by this diff, and the GitHub oap-harness job at the implementation head is
  success (160/160 OK).
- `uv run pip-audit` → "No known vulnerabilities found"; production-settings import
  fail-closed negative confirmed (nonzero exit, as CI expects).
- `docker compose config` PASSED; `deploy/rehearse_internal_alpha_deployment.sh --config-only`
  PASSED; `docker build` PASSED with image user `10001:10001` and all five CI static/data
  file existence checks PASSED.
- OpenAPI: `manage.py spectacular --file build/openapi/schema.yaml --validate --fail-on-warn`
  PASSED on both the implementation tree and a pristine main archive; generated schemas are
  byte-identical (no API surface change).

## Uncertainty, limits and notes

- Report-head CI (the publication commit) was not yet observable at authoring; it is tracked
  separately and never folded into the implementation-head CI above.
- `docs/ux/form-guidance-inventory.md` line 101 still describes the old add-form help wording
  ("members have no self-service password change"); that file is NOT in this order's
  allowed_paths, so it was intentionally not modified and is reported here for strategy.
- No DHA: the order declares `Decision: NONE`; no CRITICAL entry was appended or needed.
- This round does not merge, self-approve, enable auto-merge, or claim strategic acceptance;
  merge remains with strategy after review of this report head.
