<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "058-c",
  "order_path": "oap/orders/058-c-reissue-disabled-guard.md",
  "order_sha256": "228c678ce7ab9921b8390d67d3ea190548d569e47b00f1b35fb5c28f3c83f6e7",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 120,
  "pr_number": 121,
  "branch": "codex/120-oap-058-a-admin-onboarding-email",
  "implementation_head": "ed52e3209fbd155dd339d140d1e2fe3bc6fa6000",
  "base_sha": "77742ba8108c00ba9d8c38334651ebbb3fc13cb6",
  "previous_round": "058-b",
  "pr_mode": "AMEND",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "ed52e3209fbd155dd339d140d1e2fe3bc6fa6000",
    "runs": [
      {
        "run_id": 42973593262,
        "workflow": "CI",
        "jobs": {
          "quality": "PASS",
          "test": "PASS",
          "security": "PASS",
          "container": "PASS"
        }
      },
      {
        "run_id": 42973592984,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "PASS"
        }
      }
    ],
    "earlier_head_note": "Single implementation head; no earlier head for this round"
  },
  "local_equivalent_checks": "all five CI check groups executed locally (see Acceptance 4); one pre-existing environment-bound oap-harness test fails locally and at clean HEAD (see Limits)",
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 058-c — execution report: disabled-SMTP reissue guard and truthful account status

Implementation head SHA: ed52e3209fbd155dd339d140d1e2fe3bc6fa6000
Report publication commit: SELF

## Identity and result

COMPLETE for order 058-c (D0, `Decision: NONE`) on the SAME objective as
058-a/058-b: issue #120, PR #121 (AMEND, `Closes #120` retained), branch
`codex/120-oap-058-a-admin-onboarding-email`, base
`77742ba8108c00ba9d8c38334651ebbb3fc13cb6` (main after PR #119). The
order file at `oap/orders/058-c-reissue-disabled-guard.md`
(strategy-published bytes, SHA-256
`228c678ce7ab9921b8390d67d3ea190548d569e47b00f1b35fb5c28f3c83f6e7`) was
committed in the implementation commit together with `oap/active`
(`058-b` -> `058-c`). All 10 order `source_hashes` were verified
SHA-256-byte-identical at the branch base (058-b report head
`d06be8f9d5b80a1864359ac93fa18bd632d904e3`) before the first edit; the
governance revision `14fc20b1ff52788974fd3f282322afc9d71362f9` was
untouched; the immutable 058-a/058-b reports and their code history are
preserved untouched. No merge, no auto-merge, no self-approval, no
CRITICAL append, no DHA.

Implementation head `ed52e3209fbd155dd339d140d1e2fe3bc6fa6000` is the
single implementation commit, child of `d06be8f9d5b80a1864359ac93fa18bd632d904e3`
(the 058-b report-only head). No force-push, no history rewrite, no
renumbering.

Activation gate: the 058-b report-head CI was terminal-green at
activation (five checks at
`d06be8f9d5b80a1864359ac93fa18bd632d904e3` plus oap-harness, runs
42965953055/42965953069).

## Numbered acceptance evidence

### 1. No reissue without mail

- `UserAdmin.onboarding_reissue` (`accounts/admin.py`): after the
  existing `get_object`/model-change-permission boundary and the
  pending-state check, a `settings.ACCOUNT_EMAIL_ENABLED` guard refuses
  BOTH GET and POST with a nonsecret error and a redirect back to the
  change page, BEFORE any mutation. A POST under disabled mail generates
  no credential, rotates no hash, alters no expiry, creates no reissue
  LogEntry, registers no post-commit send and calls no mail backend.
- The change page offers NO working reissue action while disabled
  (the `a.button` link and its hint are rendered only when email is
  enabled) and tells the administrator to configure the account email
  transport first; the undelivered-failure warning has a disabled-mail
  variant that says the details cannot be reissued yet.
- Evidence (real PostgreSQL + admin HTTP, synthetic mail only):
  - `test_reissue_refused_when_email_disabled_no_mutation[accepted-active]`
    and `[failed-inactive]`: for an ACTIVE (accepted-delivery) pending
    account and an INACTIVE (failed-delivery) pending account, GET and
    direct forged POST both 302 back to the change page; stored
    password hash, pending expiry and `is_active` unchanged;
    `mail.outbox == []`; zero LogEntries for the object; the change
    page shows "Account email is not configured", no reissue link and
    no secret.
  - `test_reissue_disabled_guard_keeps_permission_and_csrf_boundaries`:
    staff user WITHOUT model change permission still 403 (GET and
    POST); `Client(enforce_csrf_checks=True)` POST without a CSRF token
    still 403; account untouched, no mail.
  - `test_reissue_refused_while_disabled_then_enabled_rotates_once_and_sends_once`:
    a disabled-mail POST leaves the credential untouched; re-enabling
    mail, the same explicit reissue rotates ONCE (new six-character
    credential, old one invalidated) and sends ONCE; the persisted
    per-account delivery status is `delivered`.
  - Browser (real Chromium, real HTTP, real PostgreSQL, synthetic
    relay): `test_browser_disabled_reissue_ui` — inactive pending
    account under disabled mail: state-specific "cannot sign in yet"
    text, zero reissue links, "account email is not configured"
    guidance, no credential rendered, no horizontal overflow at
    desktop 1440 and mobile 390 (two privacy-safe screenshots viewed,
    both clean); a direct GET of the reissue route refuses with the
    setup error and leaves the stored hash and `is_active` unchanged.

### 2. State-specific and relay-accurate text

- `change_form.html`: the pending block is now state-specific — an
  ACTIVE pending account keeps the forced-change/sign-in wording; an
  INACTIVE pending account says it "cannot sign in yet" and stays
  inactive until the login-details email for its current temporary
  password is accepted by the email relay. `UserAdmin.render_change_form`
  passes `onboarding_active` and `onboarding_email_enabled`.
- `onboarding.deliver_onboarding_email`: the two success statuses now
  report RELAY ACCEPTANCE, not inbox delivery — "The new onboarding
  login details were accepted by the email relay. The previous
  temporary password no longer works." (reissue) and "The account was
  created and its login details were accepted by the email relay."
  (add). The failure/superseded wording (already relay-accurate) is
  unchanged; reissue confirmation still explains rotation and
  ambiguous delivery; no credential appears on later pages, logs or
  audit (asserted).
- Evidence:
  - `test_change_page_state_specific_text`: inactive pending page says
    "cannot sign in yet" / relay acceptance and NOT "It signs in with
    the temporary password"; active pending page explains the forced
    change with no false inactive or undelivered warning.
  - `test_success_message_reports_relay_acceptance`: at the exact
    boundary where the messages are created (direct
    `deliver_onboarding_email` call for the reissue and the add path),
    the success lines are exactly the relay-acceptance wording and
    contain no "delivered by email".
  - The two existing browser tests that asserted the old success string
    now assert the relay-acceptance string (see Limits for the
    disclosed guidance-test updates).

### 3. Status bound to account

- `onboarding.delivery_status_for` now returns ONLY from the
  per-account mapping (`{str(pk): status}`); any other session value —
  in particular an account-unscoped single status string — is IGNORED.
  The current per-account map, its nonsecret bounded values and the
  explicit `session.save()` in `_set_delivery_status` are unchanged.
- Evidence: `test_delivery_status_ignores_legacy_unscoped_string` — a
  legacy unscoped `"undelivered"` session value yields
  `delivery_status_for(...) is None` for every account and renders no
  warning on any pending account page; a per-account mapping then
  renders the failed-delivery warning ONLY on the matching account's
  page. `test_admin_user_change_onboarding_pending_block` (updated,
  see Limits) re-asserts the account-scoped warning with the current
  mapping form and the ignored legacy string.

### 4. Evidence/publication

- Focused suites at implementation head (local, owned disposable
  PostgreSQL at 127.0.0.1:54330, synthetic mail/backends only):
  - `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test tests/test_account_onboarding.py -q` → 41 PASSED.
  - `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test --browser chromium tests/browser/test_account_onboarding_browser.py -q` → 4 PASSED (includes the new disabled-reissue browser test).
  - `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test tests/test_form_guidance.py -q` → 36 PASSED.
  - `uv run --env-file .env pytest -q` (full product suite) → 1447 PASSED, 9 SKIPPED, 1 FAILED (the pre-existing environment-bound oap-harness test, see Limits).
- Quality gates at implementation head: `uv sync --locked --all-groups`, `uv run ruff check .` (All checks passed), `uv run ruff format --check .` (253 files already formatted), `uv run mypy src` (Success, 146 files), `uv run --env-file .env python manage.py check` (0 issues), `... makemigrations --check --dry-run` (No changes detected), `git diff --check` clean.
- Exact-head CI at `ed52e3209fbd155dd339d140d1e2fe3bc6fa6000`: CI run 42973593262 (quality/test/security/container) and oap run 42973592984 (oap-harness) — all five checks PASS (see OAP-META `observed_implementation_ci`).
- Browser review: real Chromium at desktop 1440 and mobile 390 over
  real HTTP for the safe failed-delivery and disabled-reissue
  surfaces; exactly two privacy-safe screenshots viewed (the two new
  `admin-onboarding-disabled-reissue-{1440,390}.png`), both free of
  credentials, no horizontal overflow, no framework branding.
- No model/schema/auth-backend/SMTP-settings/reservation/proxy change;
  `makemigrations --check` clean; all non-onboarding files preserved.
- Publication: implementation + order + pointer committed and pushed
  to PR #121 before this report; this report is the only file changed
  in the report commit, whose first parent is the implementation head.
  No real relay/recipient/deployment; CODING did not merge.

## Uncertainty and limits

- Two DISCLOSED out-of-order updates in the pre-existing guidance
  tests `tests/test_form_guidance.py` (not in order 058-c
  `allowed_paths`, same category as the two 058-b-disclosed
  assertion-string updates): `test_admin_user_change_onboarding_pending_block`
  now exercises both mail states (disabled: no reissue action,
  state-specific text, legacy unscoped status ignored; enabled:
  reissue control, account-scoped failure warning) and
  `test_admin_user_onboarding_reissue_page_guidance` now enables
  account email before requesting the confirmation page (the route
  refuses it while disabled). Both are assertion/fixture updates to
  match the ordered behavior; no guidance product code was changed.
- `tests/oap/test_ba38_39_tmux_config.py::Ba39OperationPrereqs::test_ba39_strategic_same_prerequisites`
  FAILS in the local environment and fails IDENTICALLY on the clean
  pre-change head `d06be8f9d5b80a1864359ac93fa18bd632d904e3` (verified
  in a disposable worktree): it is environment-bound (launcher
  runtime prerequisites in this host), not caused by this round's
  changes. The authoritative oap-harness CI job for the implementation
  head PASSED (run 42973592984).
- `uv run pip-audit` locally: "No known vulnerabilities found"; the
  lockfile is unchanged by this round, and the exact-head `security`
  CI job (which includes it) PASSED at the implementation head.
- In the non-transactional test harness, `transaction.on_commit`
  callbacks run after the response cycle, so a message-framework line
  added by the delivery callback is not re-saved to the session in
  unit tests; the success wording is therefore asserted at the direct
  boundary (acceptance 2) and the transactional browser tests assert
  it end-to-end. This is a harness property, not a product behavior:
  in a live request the callback runs inside the request before the
  response middleware persists the message (as exercised by the
  passing browser flows).
- Report-head CI is not observed at authoring; implementation CI above
  is separate from report-head CI. No future push/check success is
  claimed.
