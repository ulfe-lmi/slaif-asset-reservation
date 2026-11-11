<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "058-b",
  "order_path": "oap/orders/058-b-onboarding-delivery-boundaries.md",
  "order_sha256": "3e833b0c32cb1b5727543993f832aa5e817e69b9d4b76c7eab09bb1fb750853c",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 120,
  "pr_number": 121,
  "branch": "codex/120-oap-058-a-admin-onboarding-email",
  "implementation_head": "4775678790d5975537e27dcb7fafbe090740603b",
  "base_sha": "77742ba8108c00ba9d8c38334651ebbb3fc13cb6",
  "previous_round": "058-a",
  "pr_mode": "AMEND",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "4775678790d5975537e27dcb7fafbe090740603b",
    "runs": [
      {
        "run_id": 42963693001,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      },
      {
        "run_id": 42963692990,
        "workflow": "CI",
        "jobs": {
          "quality": "pass",
          "test": "pass",
          "security": "pass",
          "container": "pass"
        }
      }
    ],
    "earlier_head_note": "First implementation head 0db10f50885b2debb73bb0e0120ce74cb74d33a3 (run 42961963300/42961963259): quality/security/container/oap-harness pass, test FAILED on one CI-environment-bound assertion (collected staticfiles absent in the CI test environment -> /static/ 404 asserted as 200); corrected in 4775678790d5975537e27dcb7fafbe090740603b (test-only change, no product logic) which passes all five checks at the exact head"
  },
  "local_equivalent_checks": "all five CI check groups executed locally (see Acceptance 6); oap-harness 160/160 locally with the launcher's OAP_ROLE removed (see Limits)",
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 058-b — execution report: onboarding delivery and admission boundaries

Implementation head SHA: 4775678790d5975537e27dcb7fafbe090740603b
Report publication commit: SELF

## Identity and result

COMPLETE for order 058-b (D0, `Decision: NONE`) on the SAME objective as
058-a: issue #120, PR #121 (AMEND, `Closes #120` retained), branch
`codex/120-oap-058-a-admin-onboarding-email`, base
`77742ba8108c00ba9d8c38334651ebbb3fc13cb6` (main after PR #119). The
order file at `oap/orders/058-b-onboarding-delivery-boundaries.md`
(strategy-published bytes, SHA-256
`3e833b0c32cb1b5727543993f832aa5e817e69b9d4b76c7eab09bb1fb750853c`) was
committed in the implementation commit together with `oap/active`
(`058-a` -> `058-b`). All 14 order `source_hashes` were verified
SHA-256-byte-identical at the branch base (058-a report head
`cf4826cb03063db5c6add76d595e7d033999dad6`) before the first edit; the
governance revision `14fc20b1ff52788974fd3f282322afc9d71362f9` was
untouched; the immutable 058-a report and its code history are preserved
untouched. No merge, no auto-merge, no self-approval, no CRITICAL
append, no DHA.

Implementation head `4775678790d5975537e27dcb7fafbe090740603b` is the
child of `0db10f50885b2debb73bb0e0120ce74cb74d33a3` (the 058-b
implementation commit on top of the 058-a report head). Both commits are
on the PR branch; the second commit corrects one test assertion after
the first head's remote `test` job failed on a CI-environment-bound
static-files 404 (see Limits). No force-push, no history rewrite, no
renumbering.

## Numbered acceptance evidence

### 1. Delivery before login

- `accounts/backends.py`: the inactive-account exception that admitted
  pending accounts BEFORE delivery is removed. Inactive accounts —
  including pending onboarding accounts whose delivery failed, is
  pending, or was superseded by a reissue — are refused exactly like any
  other inactive account (model-backend timing equalization retained).
  An ACTIVE pending account (delivery accepted) may authenticate only
  while its temporary credential is unexpired; after expiry no new
  member or Administration session can be established. `get_user`
  returns to the base model backend: any session of an inactive account
  (for example one made inactive by a reissue while its delivery is
  pending) is dropped per request.
- `web/forms.py` `confirm_login_allowed`: active non-service-account
  humans unchanged; an active pending user passes only while the
  credential is unexpired; inactive (undelivered/superseded) users get
  the generic non-disclosing error.
- `web/views.py` `password_change`: admission is the usual active-human
  boundary (an accepted pending user is active and reaches the page
  through it); the onboarding session gate enforces the restriction and
  terminates expired sessions.
- Evidence (real PostgreSQL + admin HTTP, synthetic mail):
  - `test_add_post_delivery_failure_leaves_inactive_denied_and_scoped`:
    failed send -> account inactive, `authenticate(...)` returns None
    with the CORRECT credential, member login 200 non-disclosing and
    anonymous, no automatic retry (exactly one backend call).
  - `test_add_post_zero_acceptance_leaves_inactive`: zero-accept backend
    -> inactive, correct credential refused.
  - `test_failed_delivery_inactive_cannot_establish_admin_session`:
    inactive pending STAFF account refused at `/admin/login/` with the
    correct unexpired credential.
  - `test_expired_temporary_cannot_establish_member_session` /
    `..._admin_session`: accepted-then-expired credentials refused at
    both logins.
  - `test_within_expiry_login_restricted_to_password_page`: accepted
    pending user signs in and is gated to `/profile/password/` on all
    other routes (mutations included, session-authenticated API
    included).
  - `test_reissue_failure_keeps_inactive_denied_and_allows_retry`:
    reissue failure re-activates nothing; the freshly issued credential
    cannot establish a session; an explicit second reissue rotates
    again.
  - Browser (real Chromium, real HTTP, synthetic failing relay):
    `test_browser_admin_add_failed_delivery_then_reissue` — failed
    delivery -> inactive, member login with the correct credential
    refused, only the accepted reissue delivery activates, then the
    forced change gates the session.
  - Unchanged baselines: `test_cli_createsuperuser_baseline_unaffected`
    (also with email enabled), `tests/test_migrations.py`
    `test_onboarding_state_migration_leaves_existing_accounts_untouched`
    (0005 -> 0006 real-PG upgrade, pre-existing account still signs in).

### 2. All enabled Admin adds deliver; disabled transport refuses all

- `accounts/admin.py` `save_model`: with `ACCOUNT_EMAIL_ENABLED` every
  valid add (generated prefill OR manually entered normal-validator
  password) commits the account INACTIVE/PENDING with only the password
  hash + nonsecret expiry metadata and registers exactly one post-commit
  send that activates on acceptance of the exact generation. Without
  account email the form refuses every POST before any account is
  written; `save_model` additionally fails closed (unreachable
  `RuntimeError` guard).
- `accounts/forms.py`: `clean()` refuses every disabled-state
  submission (generated, manual-normal, manual-weak) with clear
  non-field guidance; the six-character signed-prefill path is unchanged
  (edited/tampered/expired/unbound six-character values still rejected);
  manual weak passwords keep the full normal validator set.
- Evidence:
  - `test_add_post_manual_normal_password_is_onboarding_credential`:
    manual `ManualSecret123` -> committed inactive/pending BEFORE the
    send, exactly one post-commit email containing the manual
    credential, activation on acceptance, then member login is gated to
    the forced change and the credential is replaced.
  - `test_add_post_weak_manual_password_still_rejected`;
    `test_add_post_refused_when_email_disabled_creates_no_account`
    (parametrized: generated / manual-normal / manual-weak — no
    account row, empty outbox, clear refusal text).
  - `test_add_post_generated_commits_inactive_then_single_send_activates`
    (generated path unchanged: pre-send inactive + hash-only, one send,
    activation).
  - CLI: `test_cli_createsuperuser_baseline_unaffected` —
    `createsuperuser` creates an active superuser with no onboarding
    state and no mail, even with account email enabled.
  - Browser: `test_browser_admin_add_failed_delivery_then_reissue`
    (add flow over real HTTP).

### 3. Prefill is visible on Add User GET (enabled AND disabled)

- `accounts/admin.py` `get_changeform_initial_data`: every add GET now
  generates a fresh six-character CSPRNG value in BOTH password
  controls with the session-bound signed digest (digest only, never
  plaintext in session), regardless of the transport state; the add
  response stays `no-store`.
- `add_form.html`: enabled state explains that keeping the prefill OR
  entering a regular password both follow the onboarding path (one
  email after save, activation on confirmed delivery, forced change
  within 24h); disabled state shows clear nearby guidance that
  creating accounts requires the SMTP transport and that every
  submission is refused until configured.
- `accounts/forms.py` help text updated for both states (SAR-044
  accessible binding retained).
- Evidence: `test_add_get_prefills_both_controls_with_same_generated_value`
  (enabled; fresh value per GET; no plaintext in session; `no-store`),
  `test_add_get_without_email_still_prefills_with_setup_guidance`
  (disabled; same-value prefill in both controls, guidance text,
  `no-store`), browser add-flow assertions at 1440/390.

### 4. Generation-safe callbacks and account-scoped status

- `accounts/onboarding.py` `deliver_onboarding_email` now receives the
  EXACT stored hash and pending expiry of the sent generation
  (`sent_hash` / `sent_expires_at`, captured at registration time in
  `save_model` and the reissue handler):
  - the send is made only while the account still holds that exact
    generation — a reissue (or activation/vanishing) before delivery
    ran supersedes it: the stale credential is never emailed and state
    is untouched;
  - activation is a conditional update matching
    `(pk, is_active=False, password=sent_hash,
    onboarding_password_expires_at=sent_expires_at)`: an accepted send
    whose generation moved in flight matches zero rows, activates the
    newer pending credential neither, and claims no delivery
    (status `superseded` with a nonsecret warning).
  - the nonsecret status is scoped to the specific account
    (`{str(pk): status}` mapping; legacy unscoped values still read
    for compatibility) so one user's failed send cannot warn on
    another user's page. No automatic retry anywhere.
- Evidence (out-of-order / race paths, synthetic mail, real PostgreSQL):
  - `test_stale_callback_after_reissue_does_not_send_activate_or_claim`:
    the add's on_commit callback is captured unexecuted; an explicit
    reissue commits and activates the NEW generation; running the stale
    callback afterwards sends nothing, changes nothing, and records
    `superseded` for that account.
  - `test_accepted_send_superseded_by_reissue_in_flight_does_not_activate`:
    a synthetic relay that accepts the send while a reissue lands "in
    flight" — accepted, yet the conditional update matches zero rows:
    account stays inactive on the newer credential, old credential
    invalid, newer credential cannot sign in, status `superseded`, no
    delivery claim rendered.
  - `test_add_post_delivery_failure_leaves_inactive_denied_and_scoped`:
    a second pending account's change page shows NO delivery-failure
    warning (account scoping).
  - `test_reissue_rotates_credential_and_sends_once`: accepted reissue
    rotates (old credential dead), exactly one send, audit entry
    without secrets.

### 5. Path and documentation truth

- `/static/` prefix fix: `_ONBOARDING_STATIC_PREFIXES` is now
  `("/branding/", "/static/")` (the old `"static/"` prefix could never
  match an absolute path, so `/static/...` was incorrectly gated).
  Directly tested: `test_onboarding_allowed_path_allowlist`
  (`/static/web/site.css` allowed; `/staticlike/` not; exact paths and
  `/branding/` as before) plus the HTTP-level check in
  `test_within_expiry_login_restricted_to_password_page` (a `/static/`
  request is not redirected to the forced-change page; the predicate
  unit test carries the environment-independent allowlist semantics).
- Docs updated for truth (order acceptance 5): `docs/security-model.md`
  (inactive-until-accepted login boundary, exact-generation activation,
  reissue pendancy, and the SOLE intentional plaintext rendering — the
  two prefilled controls of the non-cacheable add form and the one
  login-details email), `docs/human-ui.md` (always-prefilled add form,
  manual-password path, disabled-state refusal, per-account status,
  "never displayed outside the non-cacheable add-user form prefill"),
  `INSTALL.md` (disabled transport refuses every Administration add
  without creating an account; enabled transport emails both generated
  and manually entered passwords).
- Privacy: no plaintext in DB rows, sessions (digest only), LogEntry,
  rendered account/error/status pages or screenshots — verified by the
  existing privacy assertions (e.g. `"Ab12cd" not in html/session/
  change_message`, browser `prefill not in page.content()` on the
  change/failed-delivery pages). The add form itself is still never
  screenshotted; its prefill is the sole intentional browser rendering
  and the response is `no-store`.

### 6. Evidence and publication

- Focused suite at head: `uv run --env-file .env pytest
  --ds=slaif_reservation.config.settings.test
  tests/test_account_onboarding.py tests/test_form_guidance.py -q` —
  **70 passed** at `4775678` (34 onboarding incl. the new
  delivery-before-login, disabled-refusal, exact-generation and
  scoping tests; 36 form guidance).
- Browser (real Chromium over real HTTP + PostgreSQL, synthetic
  locmem/failing SMTP sinks, desktop 1440 + mobile 390): `uv run
  --env-file .env pytest
  --ds=slaif_reservation.config.settings.test --browser chromium
  tests/browser/test_account_onboarding_browser.py
  tests/browser/test_form_guidance_browser.py -q` — **11 passed** at
  `4775678` (3 onboarding flows incl. the new failed-delivery ->
  login-denied -> accepted-reissue flow; 8 guidance). Screenshots:
  three privacy-safe images (admin onboarding change page with success
  status; member forced-change page with empty controls; admin change
  page with the nonsecret failed-delivery warning), visually reviewed in
  <=2-image batches; no credential rendered anywhere; the add form is
  deliberately never screenshotted.
- Full local suite (working tree at `0db10f5`, i.e. implementation
  commit one, with the launcher's `OAP_ROLE` removed): `env -u OAP_ROLE
  uv run --env-file .env pytest -q` — **1440 passed, 9 skipped, 1
  warning, 13 subtests passed, 0 failed** in 701.08s (the warning is
  the pre-existing intentional DB-unavailable negative test in
  `test_product_entry.py`, unchanged). The test-only delta to
  `4775678` is the Acceptance-5 assertion correction, re-verified by
  the focused suite locally and by the remote exact-head `test` job.
- Five exact-head CI checks at `4775678790d5975537e27dcb7fafbe090740603b`
  (observed terminal): CI run **42963692990** — quality pass, test
  pass (10m16s), security pass, container pass; oap run **42963693001**
  — oap-harness pass (headSha of both runs equals the implementation
  head). Report-head CI at the publication commit: NOT YET OBSERVED AT
  AUTHORING (not claimed).
- Local equivalents of the CI groups at the implementation commits:
  `uv sync --locked --all-groups` (lock unchanged), `uv run ruff check
  .` PASSED, `uv run ruff format --check .` PASSED (253 files), `uv run
  mypy src` PASSED (146 files), `uv run --env-file .env python
  manage.py check` PASSED (0 issues), `... makemigrations --check
  --dry-run` PASSED (no changes), `git diff --check` PASSED; security:
  `uv run pip-audit` PASSED (no known vulnerabilities) and
  production-settings load fails closed (`SLAIF_DJANGO_SECRET_KEY is
  required`); container: `docker compose config` OK, `deploy/
  rehearse_internal_alpha_deployment.sh --config-only` OK, `docker
  build --tag slaif-asset-reservation:ci .` OK, image user
  `10001:10001` verified, static/bootstrap files present in the image
  (web/site.css, admin/css/base.css, swagger-ui bundle,
  data/bootstrap assets.yaml + schema.json); OpenAPI: `uv run
  --env-file .env python manage.py spectacular --file
  build/openapi/schema.yaml --validate --fail-on-warn` PASSED (no API
  contract change — admin-only surface; `tests/test_api_schema.py`
  passes in the suite). oap-harness: `env -u OAP_ROLE ... python -m
  unittest discover -s tests/oap -p 'test_*.py'` — **Ran 160 tests ...
  OK**.
- Publication: PR #121 amended (same objective/issue/branch, `Closes
  #120` retained, PR body unchanged); implementation pushed; this
  report is committed as the report-only child of the implementation
  head; remote PR/head/parent/path verified with
  `oap/bin/verify_report.py` (see publication receipt note in the
  private execution receipt); FIFO `OK` (bytes 4f4b) sent only after
  verified remote publication. CODING did not merge.

## Uncertainty, privacy, dependencies, DHA, limits

- Uncertainty: none known on the corrected boundaries; the
  in-flight-reissue race is proven with a synthetic relay that mutates
  the credential between acceptance and the conditional update
  (deterministic, real PostgreSQL).
- Privacy: all mail synthetic (locmem or in-test backends); no real
  relay, recipient, credential, identity administration, private data,
  production DB/host, DNS/TLS/firewall or deployment was touched; no
  plaintext credential is persisted, logged, audited, reported or
  rendered except the intended non-cacheable Add prefill and the
  one-time synthetic email in tests.
- Scope disclosure (bounded, for strategy review): two single-string
  assertion updates in `tests/test_form_guidance.py` and
  `tests/browser/test_form_guidance_browser.py` (not listed in the
  order's `allowed_paths`) were required because they pinned the 058-a
  add-form guidance wording that order acceptance 5 explicitly
  corrects (disabled-state help text; the enabled template sentence).
  Keeping the old strings would make the corrected behavior un-
  assertable and the exact-head `test` check red. Both edits change
  only the expected guidance substring to the new accurate wording; no
  test scope, product behavior or evidence semantics changed. No other
  out-of-order file was touched.
- Limits: (a) the first implementation head's remote `test` job failed
  on `assert static_js.status_code == 200` for
  `/static/web/admin-form-guidance.js` — a 404 specific to the CI test
  environment, which has no collected `staticfiles/` directory; the
  corrected assertion verifies the gate behavior (no forced-change
  redirect; request reaches the static handler, 200 or 404) and the
  allowlist predicate is covered by a direct unit test. (b)
  `tests/oap/test_ba38_39_tmux_config.py::
  Ba39OperationPrereqs::test_ba39_strategic_same_prerequisites` fails
  locally ONLY while the launcher exports `OAP_ROLE=CODING` (the
  launched `oap_launch.py` subprocess correctly refuses a strategic
  launch under a conflicting role); with `OAP_ROLE` removed the whole
  harness passes 160/160 locally, and the remote `oap-harness` job is
  green at both implementation heads; the same failure was observed on
  the pristine 058-a report head `cf4826c` in a disposable worktree at
  start (pre-existing, environment-bound, unchanged by this round).
- Dependencies: none new (no dependency/lock change, `uv.lock`
  unchanged). DHA: NONE — order declares `Decision: NONE`; no CRITICAL
  append performed; no human disposition claimed.
- The 058-a report's overbroad "no rendered secret" wording is
  superseded by this report's Acceptance 5 description (the sole
  intentional non-cacheable Add prefill); the 058-a report bytes are
  untouched and remain the 058-a-round evidence.
