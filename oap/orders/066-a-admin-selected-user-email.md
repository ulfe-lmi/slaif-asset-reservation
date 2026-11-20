<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "066-a",
  "objective": 66,
  "round": "a",
  "slug": "admin-selected-user-email",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "8fa04f54bea6d1cfcd903a155edc951423d1479c",
  "issue_number": 137,
  "branch": "codex/137-oap-066-a-admin-selected-user-email",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "69e3b5a5deb8ffd030974878ee6ad690bdc0e5507bdd71989ffeda969f34dcd9",
    "PLAN.md": "75004e5b93c4cf2d2a13c153042ba1ccbc4aad35d921dfd2bafae8f753b42712",
    "ARCHITECTURE-for-agents.md": "8d855ece24689ee9815cff71afd835e35d23bf895afc12df8a3830c12e438727",
    "CRITICAL.md": "f5c4d78ed599ac9a8ce44687925dab29f221d8b65a2350a4f858c9f32a92c672",
    "src/slaif_reservation/accounts/admin.py": "c225afd0692ff2eb5307085fd7c64d4052168544be5351f16ad720f450d788c4",
    "src/slaif_reservation/accounts/onboarding.py": "4cd94c2ab6d8bc66a20053e11694bd101eab85dabd42b560c669a3b9a77b00b5",
    "src/slaif_reservation/config/email.py": "26b9a494229537dbc396a7d27afe2217f406e84e3cb877522a036bf23fa74004",
    "src/slaif_reservation/config/settings/production.py": "fb64b02ed8f2e52fdf33aefeacf53d18c6f934838efeb7ce804774058fe5a791",
    "src/slaif_reservation/web/templates/admin/change_list.html": "b3c08928f0b4557b5056bd2e5b90eaf893da1703c2bbe6950a78f97eda9d9257",
    "docs/deployment.md": "27a10035db235f2b2e96eb3a5d488f27f38fbdd303557c783573cafe35c037aa",
    "docs/security-model.md": "c1660fcc1fbd24bfdeb0809da40f7a3a465ad131a8caab50ad3538b950f8dc6a",
    "docs/human-ui.md": "cbb81cae63685589834bfe75f608f2d6b6a8cf98620b4a2ed638a0a856b153f2"
  },
  "requirements": [
    "SAR-007",
    "SAR-014",
    "SAR-032",
    "SAR-040",
    "SAR-043",
    "SAR-044",
    "SAR-055",
    "SAR-058"
  ],
  "allowed_paths": [
    "PLAN.md",
    "ARCHITECTURE.md",
    "ARCHITECTURE-for-agents.md",
    "src/slaif_reservation/accounts/admin.py",
    "src/slaif_reservation/accounts/forms.py",
    "src/slaif_reservation/accounts/bulk_email.py",
    "src/slaif_reservation/web/templates/admin/accounts/user/bulk_email.html",
    "src/slaif_reservation/web/static/web/admin-identity.css",
    "tests/test_admin_bulk_email.py",
    "tests/browser/test_admin_bulk_email_browser.py",
    "tests/test_form_guidance.py",
    "tests/browser/test_form_guidance_browser.py",
    "INSTALL.md",
    "docs/deployment.md",
    "docs/security-model.md",
    "docs/human-ui.md",
    "docs/ux/form-guidance-inventory.md",
    "oap/active",
    "oap/orders/066-a-admin-selected-user-email.md",
    "oap/reports/066-a-admin-selected-user-email.md"
  ],
  "forbidden_resources": [
    "No real SMTP relay/recipient/credential/user directory, deployment, DNS/TLS/firewall or real exposure. Tests use synthetic users and local-memory/fake transport only. No automatic delivery or sending from this order by strategy or CODING.",
    "No reservation, asset, policy, auth/token/permission, onboarding credential/state, schema/migration, dependency/lock, Docker/Compose/proxy/settings/env, CI/OAP helper or historical evidence change. Do not expand into a mail campaign, queue, template engine, HTML/attachments, address export or external integration. CODING never merges."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Attributable human 2026-11-19/20 requested, after PR113 repair/merge and GitHub issue feature, an Administration user-list checkbox bulk email action with editable subject/body and one-click send; issue #137 records the bounded selected behavior.",
      "section_or_evidence": "Selected users only, clear compose form, plain-text message, existing SMTP, no real sending by development agents. This is the second of two human-selected features after merged denylist PR #136."
    },
    {
      "marker": "A",
      "source": "Current ARCHITECTURE.md A-17/SAR-055 and stable SAR-001..SAR-057; PLAN P-09; current account-onboarding SMTP boundary; issue #137.",
      "section_or_evidence": "Append A-19/SAR-058 as a narrow selected Administration mail action using the established opt-in SMTP transport. A-17 general-notifications deferral is narrowed only for administrator-initiated selected-user plain-text mail. Preserve SAR-055 onboarding send/activation and all reservation/authorization invariants. Update compact executor projection/source digest and PLAN without rewriting prior rows."
    },
    {
      "marker": "E",
      "source": "Remote main 8fa04f54bea6d1cfcd903a155edc951423d1479c after merged PR #136, issue #135 CLOSED, issue #137 OPEN, no open PR; local main fast-forwarded and clean; tree equals accepted PR #136 report head.",
      "section_or_evidence": "UserAdmin in accounts/admin.py already owns model permission checks, per-user onboarding reissue and branded Administration templates; config/email.py resolves operator-enabled TLS SMTP or dummy backend; onboarding.py sends one email, without a generic bulk action. Main push CI was in progress at order drafting; exact-head checks for this objective must be observed independently before merge."
    },
    {
      "marker": "I",
      "source": "Existing Django Administration UserAdmin action mechanism, existing settings.ACCOUNT_EMAIL_ENABLED and Django email backend, product Administration templates, real browser test fixtures.",
      "section_or_evidence": "Add one permission-checked selected-user action and CSRF-protected compose/final POST; fixed ≤200 explicit recipients, display count and addresses only in protected compose page; validate subject/body; one plain-text message per recipient with no CC/BCC; stop on rejection/ambiguous exception without retry and show nonsecret counts. Hide/deny when disabled; keep onboarding untouched. Tests use synthetic locmem/failing backends, Chromium desktop/mobile, no real SMTP."
    },
    {
      "marker": "C",
      "source": "Human selected the feature; CRITICAL register empty; implementation choices are contained and reversible.",
      "section_or_evidence": "D1/DHA NONE: choose existing change_user model permission, 200-recipient cap, one-per-recipient sends, no auto-retry, and no new mail transport. Strongest objection: accidental or partially accepted mass email is irreversible. Mitigate with explicit selection preview, one final Send email action, bound, CSRF/permission checks, privacy-safe per-recipient delivery, and accurate partial/uncertain status. Real external sending is D2 and remains unperformed."
    }
  ],
  "decision_class": "D1",
  "target_gate": "One reviewed development PR for issue #137 with selected-user Admin compose/send, privacy/failure bounds, synthetic SMTP/browser evidence, A-19/SAR-058 and five exact-head CI; final fresh independent ICA follows both selected objectives; no live SMTP or deployment.",
  "expected_report_path": "oap/reports/066-a-admin-selected-user-email.md",
  "tests": [
    "Admin User list checkbox action visible only to authorized active human staff with accounts.change_user; selection yields a branded compose form showing exact count/addresses, not a send. Final POST requires same authority, CSRF, POST method, valid selected existing users and enabled transport; direct URL and forged/stale/empty/>200 selections fail without any send.",
    "Bounded plain-text subject/body (nonempty, subject no CR/LF); one message to each selected address with no CC/BCC or address disclosure; not to unselected users; no subject/body/recipient metadata in application logs, URL, exception screen, session, or Admin action log. No separate mail transport/config; disabled/incomplete transport fails closed; onboarding account state and send path unchanged.",
    "Synthetic locmem/failing-backend tests for all-accepted, zero acceptance, exception after partial acceptance, nonsecret accepted/uncertain/not-attempted counts and no automatic retry. Browser Chromium Admin list→compose→single send on desktop/mobile, inspect privacy-safe screenshots ≤2 at a time. Focused account/admin/onboarding/settings regression plus normal quality/test/security/container/OAP checks at implementation and report heads. No real relay/recipient.",
    "Update current ARCHITECTURE.md A-19/SAR-058, PLAN selected amendment and compact projection/source digest; operator/Admin docs only where behavior changes; links and generated OpenAPI unaffected; CODING opens PR with Closes #137, publishes immutable report-only child with literal implementation head/SELF, verifies remote and signals FIFO OK; CODING never merges."
  ]
}
-->

# 066-a — Administration selected-user email

## Goal and authority

Implement the human-requested Administration user-list email action on exact main `8fa04f54bea6d1cfcd903a155edc951423d1479c` after issue #135/PR #136 merged. Issue #137 is the one objective identity; create or resume only its declared branch/PR. This is an administrator-initiated message to checked accounts, not a general notification system. Development and tests use synthetic addresses and a local/fake backend; no real relay, credentials, recipient or deployment.

## Numbered acceptance and negative paths

1. **Selection and compose.** Add a User list checkbox action for active human staff with the existing `accounts.change_user` permission. Selecting users opens a branded, accessible compose page with exact recipient count and protected list of selected addresses. Subject and body are editable; one **Send email** click on that page performs the final POST with no second confirmation. Empty or >200 selections fail with a useful message and no send. Django Admin `select_across` may be supported only when the resolved selection stays within the same bound; never silently truncate. Revalidate exact selected accounts, authority, enabled transport and valid form at final POST. No GET mutation; CSRF mandatory; forged direct requests cannot bypass.
2. **Delivery and privacy.** Reuse the established operator-enabled `SLAIF_ACCOUNT_EMAIL_ENABLED`/`SLAIF_SMTP_*` Django backend. While disabled, no send and no false success from the dummy backend. Validate nonempty bounded plain-text subject/body; reject CR/LF in subject. Send a separate message to each recipient, no CC/BCC/visible list, no HTML, attachment or template execution. Accepted-by-relay is not inbox delivery. Stop on zero acceptance or exception, do not auto-retry, and report accepted/uncertain/not-attempted counts without subject, body or addresses. No content/recipient metadata in URLs, sessions, logs, exceptions or Admin action log. Protect sensitive POST values and mark compose/result uncacheable. Preserve existing onboarding send/activation behavior and all account/reservation/auth/proxy/database semantics.
3. **Evidence and docs.** Add focused server tests for selected/unselected recipients, >200/empty/stale/forged selection, no change_user/active-human/staff/CSRF/GET/disabled transport, validation/header injection, per-recipient privacy, partial/ambiguous delivery, no auto-retry, and unchanged onboarding. Add meaningful Chromium flow at desktop and narrow width; inspect privacy-safe screenshots in batches of ≤2 and correct demonstrated defects. Append A-19/SAR-058 to canonical architecture, record selected meaning in PLAN and update compact executor projection/hash. Reconcile operator/Admin/security guidance without turning README into a ledger. Run appropriate focused tests, then normal five exact-head CI at the frozen implementation and report heads.

## Strongest objection and recovery

A bulk send can be irreversible and SMTP failures can make the last recipient ambiguous. The compose page previews selection, per-request cap is 200, existing user-change permission and CSRF gate both steps, each recipient gets a separate message, and a failure stops without automatic retry or false delivery claim. This is D1, Decision NONE; actual external sending and live SMTP configuration remain separate D2 human actions. Preserve foreign worktrees, current main and accepted historical records; do not reset/clean/force. Fresh CODING through sourced `~/codex-supervision/slaif-asset-reservation/codex.sh` from checkout, `codex --yolo --profile early-beta` in the existing right pane.

## Deferred human adjudication
- Decision: NONE
