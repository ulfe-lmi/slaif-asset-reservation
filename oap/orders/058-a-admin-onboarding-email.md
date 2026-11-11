<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "058-a",
  "objective": 58,
  "round": "a",
  "slug": "admin-onboarding-email",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "77742ba8108c00ba9d8c38334651ebbb3fc13cb6",
  "issue_number": 120,
  "branch": "codex/120-oap-058-a-admin-onboarding-email",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f7b5c98876a40b052c2d2fe057e57281e917ac5a72508e98caca512c1f0d1286",
    "PLAN.md": "e15eb06f6559886808916812dc555c244cc038ff42996a12276b58319562f864",
    "ARCHITECTURE-for-agents.md": "66d578e9fc263a77ceb4500bb2e8dac88b6080bf8f38890942fd46bc718f60ca",
    "src/slaif_reservation/accounts/models.py": "776cbbb7f8fc73624c8c65fef5f733681cfd4478ad6fd4ec711e2525e7abf10d",
    "src/slaif_reservation/accounts/admin.py": "75c6e629210cd95bbda57e952a27c0864e2428bc3e1dbf14566a7153b3a22371",
    "src/slaif_reservation/accounts/managers.py": "de8d1ef75e044dbda5c0b381863a59111eb745657db1bb1582baae9f10f82497",
    "src/slaif_reservation/web/views.py": "c00c68f13d577cf02ad6e80bcdf4da482b6a81456fedad37d17cef604cf878c9",
    "src/slaif_reservation/web/forms.py": "f64c4f8f042cb0620777bb56499a3962f33041c5ea3c1bdd91ed11735e1e63a9",
    "src/slaif_reservation/config/settings/base.py": "a15c4b21f57b43ea40867fd5e0ad49c579ec08ba40bb8b718250d1f67cdf7e22",
    "src/slaif_reservation/config/email.py": "26b9a494229537dbc396a7d27afe2217f406e84e3cb877522a036bf23fa74004",
    "docs/human-ui.md": "3400d9bb2ffff8c3cfa3d3ab226d66985621e3921d57735bcbfcf93a09640039",
    "docs/security-model.md": "3c62587f61fcd3f3d757d8e01105a48f0dcf1c6ceea8e8227703302910776b69",
    "INSTALL.md": "0d1d843f3670ea72d94dfbcee09fd2b2cc76f9b7c3c8dabdbaa1b79647fa6654",
    "README.md": "c81539d02388dabdb97dd61dee5461dfeb8e16be5fecdeb903c6a3e6afae63cc"
  },
  "requirements": ["SAR-014", "SAR-023", "SAR-026", "SAR-040", "SAR-043", "SAR-044", "SAR-053", "SAR-054", "SAR-055", "SAR-056"],
  "allowed_paths": [
    "src/slaif_reservation/accounts/models.py",
    "src/slaif_reservation/accounts/admin.py",
    "src/slaif_reservation/accounts/forms.py",
    "src/slaif_reservation/accounts/onboarding.py",
    "src/slaif_reservation/accounts/backends.py",
    "src/slaif_reservation/accounts/middleware.py",
    "src/slaif_reservation/accounts/migrations/0006_user_onboarding_state.py",
    "src/slaif_reservation/config/settings/base.py",
    "src/slaif_reservation/web/views.py",
    "src/slaif_reservation/web/forms.py",
    "src/slaif_reservation/web/templates/web/password_change.html",
    "src/slaif_reservation/web/templates/admin/accounts/user/change_form.html",
    "src/slaif_reservation/web/templates/admin/accounts/user/onboarding_reissue.html",
    "src/slaif_reservation/web/templates/admin/accounts/user/add_form.html",
    "tests/test_account_onboarding.py",
    "tests/test_migrations.py",
    "tests/test_member_password_change.py",
    "tests/test_form_guidance.py",
    "tests/browser/test_account_onboarding_browser.py",
    "tests/browser/test_form_guidance_browser.py",
    "README.md",
    "INSTALL.md",
    "docs/deployment.md",
    "docs/human-ui.md",
    "docs/security-model.md",
    "docs/authorization.md",
    "deploy/env.production.example",
    "oap/active",
    "oap/orders/058-a-admin-onboarding-email.md",
    "oap/reports/058-a-admin-onboarding-email.md"
  ],
  "forbidden_resources": [
    "No reservation/asset/policy/group/permission/API-token domain or schema/service behavior change, no public self-registration/forgotten-password reset/OIDC/general notifications, queue/Celery/Gateway runtime dependency or new external enforcer behavior.",
    "No dependency/lock, Docker/Compose/proxy/trust/rate-limit/production SMTP config semantics, unrelated admin model edit, ARCHITECTURE/PLAN/projection/CRITICAL/OAP helper/workflow or prior immutable order/report rewrite. No broad visual redesign.",
    "No real SMTP/recipient/credential, real account/identity administration, private data/production DB/host/DNS/TLS/firewall/public exposure/deployment, foreign PR113 branch/resource mutation or CODING merge/automerge."
  ],
  "provenance": [
    {"marker":"H","source":"Human 2026-11-09: after admin creates user send login details email, logged-in self-change, six-character random prefilled password; explicit OAP plan then implement and 2026-11-10 urgency","section_or_evidence":"This is the remaining user-visible feature, not a contract/config-only round. The six-character value is an enrollment credential and email contains it because that is the selected meaning; all tests synthetic, no real delivery."},
    {"marker":"A","source":"Merged ARCHITECTURE.md A-17/SAR-055/056 with SAR-054 self-change and SAR-014/023/026/040/043/044/053; PLAN P-09","section_or_evidence":"CSPRNG six-character value prefilled both controls, narrow signed/generated-only length exception, <=24h expiry, forced change before all session app/Admin/API work, post-commit one SMTP send, inactive until acceptance, failure/reissue rotation/no auto retry, canonical configured URL, no plaintext persistence/logs, existing accounts unchanged. Real deployment/identity gates separate."},
    {"marker":"E","source":"Live merged main 77742ba8108c00ba9d8c38334651ebbb3fc13cb6 from PR119, exact report-head five CI green; current UserAdmin/PasswordChangeForm/SMTP resolver source and tests","section_or_evidence":"Member self-change at /profile/password/ exists; production opt-in SMTP settings and synthetic sink exist, disabled by default. Admin add currently uses normal Django password form and sends no mail. User model has no onboarding state; migrations through0005. Foreign PR113 still open, overlaps web/views.py/forms.py/docs/human-ui.md; preserve and reconcile before merge."},
    {"marker":"I","source":"Django5.2 UserAdmin add/change form, transaction.on_commit and password/session APIs; Gateway SMTP failure/ambiguous-delivery operational pattern as style reference","section_or_evidence":"Use a scoped admin add form and a signed digest proof (bound to admin session, short validity) for only the generated six-character value; all manual/normal passwords keep full validators. Save account inactive/pending in the admin transaction, send once via on_commit, activate only on SMTP acceptance, catch/record nonsecret failure, manual reissue rotates prior secret. Enforce expiry in session authentication backend and forced change via middleware. No plaintext persistence or Host-derived links."},
    {"marker":"C","source":"Selected human product meaning and current Internet-facing security boundary; CRITICAL empty","section_or_evidence":"D0/DHA NONE: the human already chose emailed six-character login data; temporary-only expiry/forced-change is required by existing strong-password target, not a new unresolved human selection. Strongest objection remains mailbox/relay compromise and online guessing; existing shared login rate bounds plus short expiry/one-use/change gate mitigate but do not make email a secure secret channel. No actual deployment or credential use."}
  ],
  "decision_class": "D0",
  "target_gate": "One reviewed development PR delivering synthetic-qualified administrator account onboarding with forced password change; no real SMTP/deployment/milestone acceptance",
  "expected_report_path": "oap/reports/058-a-admin-onboarding-email.md",
  "tests": [
    "Admin add GET: same fresh CSPRNG six-character string prefilled in password1/password2, no-store response, appropriate help/branding; signature/digest proof contains no plaintext, expires/binds admin session, edited/manual six-character value rejected while manually entered >=8 normal-valid value succeeds. Add POST without configured email fails safely with no active/short-password account; CLI createsuperuser baseline unaffected.",
    "Admin add enabled synthetic delivery: transaction commit precedes exactly one send; inactive pending user has hashed password, email body contains only canonical configured HTTPS login URL/email/temp password, no Host influence; SMTP accept activates, failure/zero/ambiguous result leaves inactive with nonsecret admin status; no auto retry; explicit permission+CSRF checked reissue rotates old secret and sends a new one, with double/forged/unauthorized negative paths.",
    "Temporary credential <=24h: new member and admin login denied after expiry; before expiry successful login can reach only password change/logout and necessary static/branding/health, not member/management/Admin/session API; existing shared login abuse controls apply. Strong password change clears temporary state and keeps current session, old temporary credential fails, other sessions invalidated; existing pre-upgrade users unaffected (migration test), no automatic group/Book/admin grants or API token change.",
    "Real PostgreSQL/browser/admin/CSRF/privacy and synthetic SMTP-sink integration tests at desktop1440/mobile390, screenshot visual review <=2 images/batch; no plaintext in DB/audit/admin LogEntry/logs/errors/report, no actual relay/recipient. Relevant existing auth/permission/reservation tests, no-migrations after new migration, OpenAPI unchanged, static/docs links, full normal five exact-head CI at implementation/report heads and reviewed merge."
  ]
}
-->

# 058-a — administrator onboarding email and temporary password

## Goal and authority

Implement the remaining two visible human requirements as one account-onboarding workflow: an administrator adds a human user with a fresh random six-character temporary password already shown in both password controls, and the user receives that login data through configured external SMTP. The user must replace it from the member password-change page before other work. This is an application-development target only, issue120/base/branch in metadata. No real mail, recipient, identity administration or deployment is authorized. The prior 056 self-change and 057 SMTP transport are merged prerequisites; preserve their source/behavior. Foreign PR113 remains open and overlaps web files; reconcile it read-only and do not alter its branch or claims.

## Compact read set

CODING startup core + this order; compact A-17/SAR-054/055/056 clauses, current UserAdmin add/change forms and model/manager, admin template conventions, current member password-change view/form/route, SMTP config resolver/settings and 057 synthetic sink fixture, session auth/abuse middleware, relevant tests/admin/browser/migration docs. Official Django5.2 admin/password/transaction.on_commit guidance as needed. No full strategic book, raw `.env` values, whole Gateway repo or private credential sources. Keep context bounded for the selected coding model.

## Numbered acceptance and negative paths

1. **Admin prefill and narrow exception.** A fresh Administration Add user GET generates one CSPRNG six-character mixed-alphanumeric credential and prepopulates BOTH password1/password2 controls with that SAME value. Separate GETs generate fresh values (test via deterministic generator injection, not probabilistic inequality). The form clearly labels it temporary, never stores it in a server session or database plaintext, and uses a short-lived signed digest bound to that administrator session to prove the submitted six-character value was generated. An edited/tampered/expired/unbound six-character value is rejected; manually entered normal-length passwords still pass the full existing validators. Do not lower the global minimum or exempt any later password change/admin reset. No secret in URL/query, logs, audit, error messages or report; admin add form response must not be cached. Retain current add permissions and staff/superuser checkboxes but make their newly created accounts subject to the same force-change gate.
2. **Post-commit delivery and recovery.** When `ACCOUNT_EMAIL_ENABLED` is false or incomplete, Admin add POST refuses safely and does not create an active short-password account; CLI `createsuperuser` and existing accounts remain usable. With enabled validated transport, save the new account inactive/pending first in the admin transaction with only the password hash and nonsecret state. Register exactly one post-commit send of a plain text message containing the configured `PUBLIC_BASE_URL` + login path, email identifier and temporary password; never derive URL from request Host. SMTP accepts (return count1) -> activate only that account and show safe success status; send raises/returns0 or acceptance is uncertain -> account stays inactive, no automatic retry and a nonsecret admin warning. An explicit admin-only POST reissue control (with GET confirmation, CSRF and model change permission) generates a NEW credential, invalidates the old hash/expiry, sends once after commit and reports status without showing the secret. Limit reissue to accounts still in onboarding state; no general password-reset/email API. Repeated/forged/unauthorized requests cannot leak or mutate other accounts.
3. **Temporary lifecycle and enforcement.** Add the minimum model state and migration with defaults that leave all existing users/accounts/reservations/tokens/groups untouched. A temporary credential expires no later than 24h and cannot establish a NEW member or Administration session after expiry; a custom authentication backend can enforce this across both login paths while retaining Django permission semantics. Before expiry, an authenticated onboarding user can reach only `/profile/password/`, logout and necessary static/branding/health, not dashboard/assets/reservations/tokens/management/Administration/session-authenticated API. A middleware/session gate must not redirect-loop. Successful own-password change uses the normal validators, clears temporary/expiry state, keeps current session, invalidates other sessions and unlocks ordinary permissions; old temporary password fails. No self-registration/public reset/OIDC; bearer API contract and existing token records remain unchanged. Existing shared login abuse budgets still apply. No new group/Book/admin grant is auto-assigned.
4. **Operator/user truth.** Update current README, INSTALL and deployment/security/human UI/authorization docs plus the env example to explain what is now implemented, how to enable external SMTP before Admin add, what happens on failure/expiry/reissue, and residual email/mailer risk. Root README remains product-first, no OAP chronology or false production claim. Existing quickstart CLI superuser path must remain truthful. Admin guidance is clear, branded and accessible at desktop/mobile; dangerous reissue explains rotation and ambiguous delivery. No real SMTP credentials/hostnames appear.
5. **Evidence/publication.** Add focused positive and negative real PostgreSQL/Admin/browser/CSRF/SMTP-sink and upgrade tests per metadata, no secret output in logs/screenshots/CI/report. Exercise exact admin add and reissue via real HTTP/Chromium, disabled/failed/accepted synthetic mail, expired/new session denial, forced-change escape attempts across all stated surfaces, retained account/admin permission boundaries, existing user migration and unchanged owner reservation/API rights. Inspect privacy-safe screenshots in batches <=2. Run relevant unit/integration/concurrency suites and normal five CI checks at exact frozen implementation/report heads; generated OpenAPI unchanged unless a documented API change is explicitly ordered (none is). No actual deployment/email. Open one PR with `Closes #120`, publish immutable report-only child after implementation CI, verify remote parent/path/head and send FIFO OK. CODING never merges.

## Strongest objection and recovery

Email is not a secure credential channel. A six-character secret, even CSPRNG-generated, is intentionally weaker than a normal password. This workflow is acceptable for the selected development target only because it is short-lived, cannot be reused after forced change, shares existing online login limits, never persists plaintext and fails inactive on delivery uncertainty. This is not MFA or production certification. A real operator must separately approve/configure the relay and real identity/deployment boundary. Resume interrupted work on the same ID/branch/PR without rewriting this order, resetting the valuable checkout or touching foreign PR113; fresh CODING through sourced `codex.sh`, `--yolo --profile early-beta` in right pane.

## Deferred human adjudication
- Decision: NONE
