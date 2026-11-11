<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "058-a",
  "order_path": "oap/orders/058-a-admin-onboarding-email.md",
  "order_sha256": "bc34d58c76d36cd804ba51619092286c43b30549a4299347e2d9bc00ff0b3a8c",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 120,
  "pr_number": 121,
  "branch": "codex/120-oap-058-a-admin-onboarding-email",
  "implementation_head": "c546a91b8ab74d677cfe80ed3b7d76d6d99bddb2",
  "base_sha": "77742ba8108c00ba9d8c38334651ebbb3fc13cb6",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "c546a91b8ab74d677cfe80ed3b7d76d6d99bddb2",
    "runs": [
      {
        "run_id": 42953649233,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "ci_run": {
      "run_id": 42953649251,
      "workflow": "CI",
      "jobs": {
        "quality": "PENDING_AT_AUTHORING",
        "test": "PENDING_AT_AUTHORING",
        "security": "PENDING_AT_AUTHORING",
        "container": "PENDING_AT_AUTHORING"
      }
    },
    "local_equivalent_checks": "all five CI check groups executed locally at c546a91b8ab74d677cfe80ed3b7d76d6d99bddb2 (see Acceptance 4)"
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 058-a — execution report: administrator onboarding email and temporary password

Implementation head SHA: c546a91b8ab74d677cfe80ed3b7d76d6d99bddb2
Report publication commit: SELF

## Identity and result

COMPLETE for order 058-a (D0, `Decision: NONE`): issue #120, PR #121,
branch `codex/120-oap-058-a-admin-onboarding-email`, base
`77742ba8108c00ba9d8c38334651ebbb3fc13cb6` (merged main after PR #119).
The order file at `oap/orders/058-a-admin-onboarding-email.md` (strategy-
published bytes, SHA-256
`bc34d58c76d36cd804ba51619092286c43b30549a4299347e2d9bc00ff0b3a8c`) was
committed per the order's allowed paths; `oap/active` moved `057-b` ->
`058-a` in the same implementation commit. All order `source_hashes`
(14 files) were verified SHA-256-byte-identical at the branch base before
the first edit; governance revision `14fc20b1ff52788974fd3f282322afc9d71362f9`
was untouched. Foreign PR #113 was not touched (no branch/resource
mutation, no reconciliation conflict surfaced). The merged 056-a/056-b and
057-a/057-b prerequisites (member self-change, SMTP transport) were
preserved: `config/email.py` is unmodified in this round and its 87-test
suite passes unchanged.

The implementation delivers the selected M-ACCOUNT-ONBOARDING workflow:
the Administration add-user form prefills a fresh CSPRNG six-character
temporary password in both password controls under a short-lived signed
digest proof bound to the creating administrator's session; the account
commits inactive/pending with only a password hash plus nullable expiry
metadata; exactly one plain-text login-details email is sent after the
commit (canonical configured HTTPS base URL + `/login/`, account
identifier, temporary password) and the account is activated only on SMTP
acceptance; failure or an unconfirmed result leaves it inactive with a
nonsecret admin status and no automatic retry; an explicit
permission- and CSRF-checked reissue rotates the credential; the
temporary credential expires within 24 hours and cannot establish a new
session after expiry; an in-window session is restricted to the
password-change page, logout, login and static/branding/health; the
forced change uses the normal validators, keeps the current session,
invalidates every other session and clears the onboarding state.

## Acceptance evidence

Commands below ran at implementation head
`c546a91b8ab74d677cfe80ed3b7d76d6d99bddb2` on real PostgreSQL 17 with
synthetic mail sinks only (locmem or in-test backends; no real relay or
recipient).

### 1. Admin add GET, signed prefill proof, fail-closed, CLI baseline

`uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test
tests/test_account_onboarding.py -q` (part of the 28-test focused suite,
see item 4): same fresh six-character value prefilled in
`#id_password1`/`#id_password2` (deterministic-generator injection;
real-CSPRNG shape asserted separately: exactly 6 chars, at least one
letter and one digit), `no-store` in `Cache-Control`, temporary-path help
rendered and aria-bound; the session proof is a SHA-256 digest signed by a
30-minute `TimestampSigner` mixed with a per-session nonce — it contains
no plaintext, is bound to the creating session (a different session's
proof fails), and an edited, tampered, stale (`_stale_signed`) or unbound
six-character value is rejected with the non-disclosing
`PREFILL_MISMATCH_MESSAGE` while a manually entered normal-length
password keeps the full validator set; with account email disabled or
unconfigured the add POST creates no active/short-password account and
sends nothing; `createsuperuser --noinput` with
`DJANGO_SUPERUSER_PASSWORD` is unaffected (active superuser,
`onboarding_password_expires_at` NULL, no mail). PASSED.

### 2. Admin add enabled: commit precedes exactly one accepted send

Within `django_capture_on_commit_callbacks(execute=True)` the committed
account is asserted inactive/pending with the hashed credential and an
empty outbox BEFORE the post-commit callback runs; after it, exactly one
message: from `DEFAULT_FROM_EMAIL` to the account identifier, body
containing only the canonical `{PUBLIC_BASE_URL}/login/`, the account
email and the temporary password. `test_delivery_url_never_derived_from
_request_host` asserts the test-server Host never appears (canonical
configured origin only). SMTP acceptance (count == 1) activates the
account; `_FailingSMTPBackend` (raised error) and `_ZeroAcceptBackend`
(returned 0) each leave the account inactive with exactly one backend
call (no automatic retry) and the nonsecret change-page warning ("could
not be confirmed as delivered", "reissue again") persisted in the
creating administrator's session and rendered on the account page. The
explicit reissue control is permission-checked (non-editor 403),
CSRF-checked, rotates the stored hash (old credential fails), keeps the
account pending, sends exactly one new message with a NEW six-character
value, and is refused for non-pending accounts; double/forged/unauthorized
negative paths are covered. The browser reissue E2E (item 4) repeats the
rotation over real HTTP/Chromium. PASSED.

### 3. Temporary lifecycle (24h) and forced change

Member AND Administration login with an expired temporary credential are
denied by `SlaifOnboardingAuthenticationBackend` (new-session denial on
both paths; inactive-pending-unexpired accounts authenticate through the
narrow fallback with not-found timing equalized); before expiry, an
in-window session reaches only `/profile/password/`, `/logout/`,
`/login/`, `/health/live`, `/health/ready` and static/branding — the
`OnboardingForcedChangeMiddleware` redirects every other path (dashboard,
profile, assets, admin, `/api/v1/me/`) back to the password-change page
without dropping the session (no redirect loop), and an expired session
is terminated to the login page. The shared login abuse budget still
applies (429 on the 11th login attempt, pre-existing test retained). The
forced change runs the normal validator set, keeps the current session
(`update_session_auth_hash`), invalidates every other session (hash
rotation), clears `onboarding_password_expires_at` and re-activates the
account; the old temporary password then fails from a fresh session. No
group/booking/management grant or API-token change is ever assigned.
Real PostgreSQL upgrade test (`tests/test_migrations.py`,
`transaction=True`): a raw-SQL account created at migration 0005 comes
through `migrate accounts 0006` with `onboarding_password_expires_at`
NULL, still active, still signing in with its stored hash through the new
backend; the test restores full migrations in `finally`. PASSED.

### 4. Real PG/browser/CSRF/privacy, regression, OpenAPI, five checks

- Focused suite at head: `uv run --env-file .env pytest
  --ds=slaif_reservation.config.settings.test
  tests/test_account_onboarding.py tests/test_form_guidance.py
  tests/test_migrations.py -q` — **67 passed** (28 onboarding incl.
  privacy canaries — no plaintext in DB row, session, LogEntry, rendered
  admin/member pages; 36 form guidance incl. 3 new onboarding rendering
  tests; 3 migration incl. the new upgrade test).
- Browser (real Chromium over real HTTP + PostgreSQL, synthetic locmem
  sink, desktop 1440 + mobile 390): `uv run --env-file .env pytest
  --ds=slaif_reservation.config.settings.test --browser chromium
  tests/browser/test_account_onboarding_browser.py
  tests/browser/test_form_guidance_browser.py -q` — **10 passed** (2 new
  E2E flows: admin add → prefilled both controls → single accepted send →
  activated pending → member login lands on forced-change page → escape
  attempts → mobile forced change → current session kept, old credential
  dead; admin reissue → rotation + exactly one new send. Plus the new
  `test_browser_admin_onboarding_form_guidance` and 7 pre-existing
  guidance tests). Screenshots: exactly two new privacy-safe images
  (admin onboarding change page; member forced-change page with empty
  controls), visually reviewed; the add form is deliberately never
  screenshotted because its controls visibly carry the generated
  credential — its value equality/length were asserted semantically.
- Regression at head: `uv run --env-file .env pytest
  --ds=slaif_reservation.config.settings.test
  tests/test_member_password_change.py tests/test_accounts.py
  tests/test_product_entry.py tests/test_account_email_settings.py
  tests/test_accounts_validators.py tests/test_web_human_mvp.py
  tests/test_abuse_http.py tests/test_api_schema.py -q` — **198 passed,
  1 warning** (the warning is the pre-existing intentional DB-unavailable
  negative test in `test_product_entry.py`, unchanged).
- Full local suite at head: `uv run --env-file .env pytest` —
  **1432 passed, 9 skipped, 1 failed** in 842.83s (+35 vs the 057-b local
  baseline of 1397: exactly the new tests). The single failure is
  `tests/oap/test_ba38_39_tmux_config.py::Ba39OperationPrereqs::
  test_ba39_strategic_same_prerequisites`, a supervision-harness test in
  the separate path-gated `oap` CI job. It is environment-bound, not a
  product defect: it fails here only because the agent session exports
  `OAP_ROLE=CODING`, which the launched `oap_launch.py` subprocess
  correctly refuses for a strategic launch ("conflicting OAP_ROLE=CODING;
  refusing"); with `OAP_ROLE` removed, the whole `tests/oap` harness
  passes **12/12** locally at head, and the remote
  `oap-harness` job (run 42953649233) at the same head is
  **success**. It failed identically on pristine main `77742ba` in a
  disposable worktree at start.
- Static/config/OpenAPI at head: `uv sync --locked --all-groups`
  (lock unchanged), `uv run ruff check .` PASSED, `uv run ruff format
  --check .` PASSED (253 files), `uv run mypy src` PASSED (146 files),
  `uv run --env-file .env python manage.py check` PASSED (0 issues),
  `... makemigrations --check --dry-run` PASSED (no changes; 0006
  applied cleanly on a real PostgreSQL 17 database), `... spectacular
  --validate --fail-on-warn` PASSED (OpenAPI byte-identical scope: no API
  contract change — admin-only surface; `tests/test_api_schema.py`
  passes), `uv run pip-audit` PASSED (no known vulnerabilities),
  `git diff --check` PASSED.
- Remote exact-head CI: oap-harness run 42953649233 `success` (observed
  terminal). CI run 42953649251 (quality/test/security/container) was
  still in progress at report authoring and is recorded in the metadata
  as PENDING_AT_AUTHORING; the local equivalents of all four jobs are the
  PASSED commands above. Report-head CI at the publication commit was
  not yet observed at authoring and is recorded as such.

### 5. PR, publication, merge authority

PR #121 opened from the branch with the objective description and
`Closes #120`. This report is an immutable report-only child commit of
the implementation head (its only changed path is
`oap/reports/058-a-admin-onboarding-email.md`); remote bytes/parent/
path were verified before the completion signal. CODING did not merge,
self-approve or enable auto-merge. PASSED.

## Changed files (implementation commit)

- `src/slaif_reservation/accounts/models.py` — nullable
  `User.onboarding_password_expires_at` (metadata, never a credential).
- `src/slaif_reservation/accounts/migrations/0006_user_onboarding_state.py`
  — AddField, NULL default; pre-existing accounts untouched.
- `src/slaif_reservation/accounts/onboarding.py` — generator (CSPRNG,
  6 chars, mixed), session nonce + signed prefill proof, pending-state
  helpers, allowed-path set, canonical login URL, message builder,
  exactly-one post-commit delivery with activation-on-acceptance,
  nonsecret status persistence and messages.
- `src/slaif_reservation/accounts/backends.py` — model-backend subclass:
  expired-temp new-session denial (member and Administration), narrow
  pending-unexpired authentication, pending-session `get_user`.
- `src/slaif_reservation/accounts/middleware.py` — forced-first-change
  session gate (redirect to the password page; terminate after expiry; no
  loops).
- `src/slaif_reservation/accounts/forms.py` — `SlaifUserCreationForm`
  with the generated-only six-character exception via the signed proof;
  normal passwords keep the full validators; temporary vs regular help.
- `src/slaif_reservation/accounts/admin.py` — add form wiring (prefill,
  no-store, proof binding), `save_model` pending-commit + single
  post-commit send, change-page onboarding context (status block,
  delivery-failure warning, reissue control), permission/CSRF-checked
  `onboarding_reissue` endpoint with rotation + audited log entry.
- `src/slaif_reservation/config/settings/base.py` — authentication
  backend and middleware registration.
- `src/slaif_reservation/web/views.py`, `src/slaif_reservation/web/forms.py`
  — login admission for pending-unexpired accounts; forced-change
  admission/completion (clears onboarding, keeps session); member
  password-change form completes onboarding.
- `src/slaif_reservation/web/templates/admin/accounts/user/` (3 new) —
  add-form note, change-form onboarding block + reissue action, reissue
  confirmation page; `web/templates/web/password_change.html` — pending
  notice.
- `tests/test_account_onboarding.py` (28), `tests/test_migrations.py`
  (+1 real-PG upgrade), `tests/test_form_guidance.py` (+3),
  `tests/browser/test_account_onboarding_browser.py` (2 E2E),
  `tests/browser/test_form_guidance_browser.py` (+1 guidance).
- Docs: `README.md`, `INSTALL.md`, `docs/deployment.md`,
  `docs/human-ui.md`, `docs/security-model.md`, `docs/authorization.md`,
  `deploy/env.production.example` — current-state operator/product
  wording (no chronology, no false production claims).
- `oap/active`, `oap/orders/058-a-admin-onboarding-email.md` — pointer
  and strategy-published order bytes.

## Privacy, dependencies, DHA and limits

No real SMTP relay, recipient, credential, real account/identity
administration, production DB/host/DNS/TLS/firewall exposure or
deployment was touched; every send in the evidence is synthetic
(locmem or in-test backends). No plaintext temporary credential appears
in the database, sessions, admin LogEntry, logs, rendered pages,
screenshots (the two reviewed images contain no credential material) or
this report; the test values are fixed synthetic constants. No
dependency or lock change. DHA: `Decision: NONE` (no CRITICAL append,
none was ordered). Residual risk is stated product-side (email is not a
secure secret channel; mailbox/relay compromise and online guessing
remain mitigated by the shared login abuse budgets, the 24-hour expiry
and the one-time forced change — see docs/security-model.md). This
report claims no strategic acceptance, no merge and no production
milestone; CI observations are recorded exactly as observed above.
