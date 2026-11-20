<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "066-a",
  "order_path": "oap/orders/066-a-admin-selected-user-email.md",
  "order_sha256": "f7260dccb9da41e6c0275d15996cbed3e15073028b1472845f62421d502336ee",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 137,
  "pr_number": 138,
  "branch": "codex/137-oap-066-a-admin-selected-user-email",
  "implementation_head": "8df4b8703baf8c610ecd884e13d460d8e27a61bc",
  "base_sha": "8fa04f54bea6d1cfcd903a155edc951423d1479c",
  "previous_round": null,
  "pr_mode": "CREATE_OR_RESUME",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "8df4b8703baf8c610ecd884e13d460d8e27a61bc",
    "runs": [
      {
        "run_id": "44684377145",
        "workflow": "CI",
        "jobs": {
          "quality": "PASS",
          "test": "PASS",
          "security": "PASS",
          "container": "PASS"
        }
      },
      {
        "run_id": 44684377012,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "PASS"
        }
      }
    ]
  },
  "local_equivalent_checks": "real owned PostgreSQL 17 product suites at the exact implementation head: 219 focused server tests PASSED (tests/test_admin_bulk_email.py incl. the new POST/Redirect/GET one-shot result, refresh-never-resends and invalid/foreign-nonce refusal tests; tests/test_account_email_settings.py; tests/test_account_onboarding.py; tests/test_accounts.py; tests/test_form_guidance.py; tests/test_member_password_change.py); real Chromium browser suite PASSED (3/3 tests/browser/test_admin_bulk_email_browser.py at 1440 and 390 over real HTTP with a synthetic locmem SMTP sink, incl. result-page refresh refusal at both widths); ruff check / ruff format --check / mypy (148 source files) / manage.py check / makemigrations --check --dry-run / git diff --check all clean; three privacy-safe Chromium screenshots (synthetic addresses only) captured and inspected <=2 at a time by strategy at the pre-correction head, no further image ingestion needed; pre-correction focused runs (219 server + 3 Chromium at 641375c) also PASSED",
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 066-a — execution report: Administration selected-user email

Implementation head SHA: 8df4b8703baf8c610ecd884e13d460d8e27a61bc
Report publication commit: SELF

## Identity and result

COMPLETE for order 066-a (D1, `Decision: NONE`), issue #137, PR #138
(CREATE_OR_RESUME, `Closes #137`), branch
`codex/137-oap-066-a-admin-selected-user-email`, base
`8fa04f54bea6d1cfcd903a155edc951423d1479c` (verified equal to
origin/main at the start of this round, before the correction edit).
The order file at `oap/orders/066-a-admin-selected-user-email.md`
(state FINAL, SHA-256
`f7260dccb9da41e6c0275d15996cbed3e15073028b1472845f62421d502336ee`)
and the `oap/active` pointer (`066-a` + LF) were committed with the
first implementation commit
`641375c1964f1c4bd5e1c14854f2f6d417f2dd61`. Remote reconciliation:
before this round there was no remote branch and no open PR for issue
#137 (the previous round was interrupted before publication); the
branch was pushed fresh and PR #138 created fresh (no resume, no
renumbering — same objective, same branch name, same PR slot).
Implementation head
`8df4b8703baf8c610ecd884e13d460d8e27a61bc` adds exactly ONE in-scope
correction on top of `641375c` after STRATEGIC reviewed the frozen
head: the successful/partial send rendered the result as the POST
response, so a browser refresh could resend the mass email; it is now
POST/Redirect/GET with a one-shot session nonce (see 3).

## Numbered acceptance evidence

### 1. Selection and compose

- User-list checkbox action **Send a plain-text email to the selected
  users** (`UserAdmin.email_selected_users`, `@admin.action(permissions=("change",))`):
  offered only to active non-service-account staff holding the existing
  `accounts.change_user` model permission; the administration site gate
  (active non-service-account human staff) applies to the route.
  `test_action_visible_only_with_change_permission` (visible to
  superuser and change-permission staff, absent for view-only staff),
  `test_admin_admission_gates_bulk_email_surface` (member/service/
  inactive staff terminated to the login, nothing sent) and
  `test_forged_action_without_change_permission_sends_nothing` PASSED.
- Selection step: validates the bound (empty and over 200, including
  select-across — refused wholesale, never truncated) and redirects to
  the compose page; it never sends. `test_action_redirects_to_compose_without_sending`
  and `test_action_refuses_empty_and_oversized_selection` (incl.
  exactly-200 accepted) PASSED.
- Compose GET: branded, accessible page with the exact recipient count
  and the protected list of selected addresses, editable bounded
  plain-text subject (single line, ≤200) and body (≤10,000), one
  **Send email** control; the GET never sends.
  `test_compose_get_shows_count_addresses_and_never_sends` (count,
  exact two of three addresses, no unselected address, `no-store`) and
  `test_compose_get_refuses_empty_stale_forged_and_oversized` (direct
  URL refusals back to the user list) PASSED.
- One-click final send: the single **Send email** click performs the
  final CSRF-protected POST with no second confirmation
  (real Chromium, both widths, `test_browser_admin_bulk_email_desktop_flow`
  and `test_browser_admin_bulk_email_mobile_flow` PASSED).
- Disabled transport: the compose surface offers no send control and
  the POST refuses before any send; the dummy backend is never
  reported as delivery. `test_compose_get_disabled_transport_offers_no_send`,
  `test_final_post_disabled_transport_fails_closed` and
  `test_browser_admin_bulk_email_disabled_transport` PASSED.
- Form guidance: `test_admin_bulk_email_compose_guidance` (bounded help
  bound to its controls via `aria-describedby`, invalid-POST page keeps
  the rendered, bound help) PASSED; inventory row present in
  docs/ux/form-guidance-inventory.md.

### 2. Delivery and privacy

- Reuses the established operator-enabled
  `SLAIF_ACCOUNT_EMAIL_ENABLED`/`SLAIF_SMTP_*` Django backend
  (config/email.py); no new transport, queue, template engine, HTML,
  attachment or address export; onboarding send/activation
  (`test_account_onboarding`, 44 tests) unchanged and PASSED.
- Final POST revalidation: exact selected accounts (existing, unique —
  duplicate pks collapse to one message per account), same authority,
  enabled transport, bounded form. `test_final_post_requires_csrf_token`,
  `test_final_post_requires_change_permission`,
  `test_final_post_refuses_empty_stale_forged_and_duplicate_selection`
  and `test_final_post_validates_subject_and_body` (empty/blank subject,
  CR/LF header injection, length bounds, empty/blank body) PASSED.
- Per-recipient privacy: one separate plain-text message per selected
  recipient, no CC/BCC/visible recipient list, unselected users
  receive nothing; no Admin action log entry.
  `test_final_post_sends_one_plain_text_message_per_recipient` PASSED.
- Bounded failure semantics (synthetic locmem/fake backends only):
  `test_zero_acceptance_stops_without_retry` (explicit rejection stops
  after one call), `test_exception_after_partial_acceptance_stops`
  (accepted 2 / uncertain 1 / not attempted 0, no retry, exception text
  not echoed) and `test_all_accepted_reports_full_count` PASSED.
- No content in URLs/logs/session/action log:
  `test_final_post_leaves_no_content_in_urls_or_logs` (POST path fixed;
  redirect and GET paths carry no subject/body/address; caplog clean)
  PASSED; compose and result responses carry `Cache-Control: no-store`.
- Real Chromium (1440 and 390): desktop flow (list → compose → single
  send → result, delivery assertions, no framework branding, no
  horizontal overflow, send control inside the first desktop
  viewport), mobile flow (reachable send control after normal scroll)
  and disabled-transport flow all PASSED; three privacy-safe
  screenshots (synthetic addresses only) captured and previously
  inspected by strategy ≤2 at a time.

### 3. POST/Redirect/GET one-shot result (correction)

- Defect (found by STRATEGIC at the frozen head `641375c`): a
  successful/partial send rendered the result as the POST response, so
  a browser refresh of the page — which says "no resend" — could
  resubmit the form and resend the mass email.
- Correction at `8df4b87` (accounts/admin.py, accounts/bulk_email.py):
  the successful POST now stores ONLY a random one-shot nonce
  (`secrets.token_urlsafe(32)`) plus the nonsecret
  accepted/uncertain/not-attempted counts in the administrator session
  (`bulk_email.store_result`; no subject/body/recipient addresses) and
  redirects to the EXISTING `/admin/accounts/user/bulk-email/` route's
  GET. The GET (`bulk_email.take_result`) matches the URL nonce against
  the session nonce in constant time, renders the counts via the
  existing template result branch and consumes the stored result; an
  invalid, empty or foreign nonce — or an already-consumed result — is
  safely refused (notice + back to the user list) without revealing
  whether a result exists and without any send. Invalid form POSTs
  still re-render errors (200) exactly as before.
- Focused server tests PASSED:
  `test_result_get_refresh_never_resends` (first GET renders once;
  refresh of the result URL → safe refusal, back to the user list,
  outbox unchanged) and
  `test_result_get_refuses_invalid_and_foreign_nonces` (a different
  session opening the same result URL gets no counts and sends
  nothing; invalid and empty nonces in the owner session are refused
  the same way; the owner's own result is still shown exactly once,
  then refused).
- Session/URL privacy of the correction:
  `test_final_post_sends_one_plain_text_message_per_recipient` now
  asserts the redirect Location carries only `?result=<nonce>` (no
  `selected_pks`, no subject/body/address), the session entry is
  EXACTLY `{nonce, accepted, uncertain, not_attempted}` with no
  content, and the nonce is consumed by the result GET.
  `test_final_post_leaves_no_content_in_urls_or_logs` asserts neither
  the POST path, the redirect Location nor the GET full path carries
  subject/body/address and caplog stays clean. PASSED.
- Real Chromium reload tests PASSED (both widths): after the single
  send click the browser lands on the same route's GET
  (`bulk-email/?result=...`); `page.reload()` is safely refused, the
  browser returns to the user list with the notice and the synthetic
  outbox length is unchanged — the refresh never resends.

### 4. Evidence and docs

- Governance (committed with `641375c`): ARCHITECTURE.md appends A-19
  (selected 2026-11-20, issue #137) and SAR-058; PLAN.md records the
  selected amendment; ARCHITECTURE-for-agents.md carries the A-19
  executor section, the SAR-058 row and the updated source digest
  (new root full-source SHA-256
  `c01fe2fcab3bb5b360f7065737a3440f155884150f25a2f47b931ec3fd19d2ca`,
  prior digests retained as historical provenance); A-17/P-04/SAR-036
  general-notifications deferral narrowed ONLY for this one
  administrator-initiated selected-user plain-text action; no schema,
  migration, dependency, container or CI change
  (`makemigrations --check --dry-run`: "No changes detected").
- Docs reconciled to the behavior (now-current prose only):
  docs/human-ui.md (Administration selected-user email paragraph),
  docs/security-model.md (SAR-058 boundary paragraph), docs/deployment.md
  (transport purpose), docs/ux/form-guidance-inventory.md (compose row),
  INSTALL.md. Product-first, no work-order ledger.
- Focused suites at the exact implementation head (real owned
  PostgreSQL 17, real Chromium): 219 server tests PASSED across
  test_admin_bulk_email / test_account_email_settings /
  test_account_onboarding / test_accounts / test_form_guidance /
  test_member_password_change; browser 3/3 PASSED (real Chromium,
  synthetic locmem SMTP sink).
- Static: ruff check / ruff format --check / mypy (148 source files) /
  manage.py check / makemigrations --check --dry-run / git diff --check:
  all clean at `8df4b87`.
- Exact-head CI (observed at authoring): CI run 44684377145 at
  `8df4b8703baf8c610ecd884e13d460d8e27a61bc` — quality PASS, test PASS,
  security PASS, container PASS; oap run 44684377012 — oap-harness
  PASS. All five exact-head checks terminal and passing. Report-head CI
  is NOT yet observed at authoring and is not claimed.

## Uncertainty, privacy, dependencies, DHA, limits

- No uncertain product behavior: every acceptance path was executed on
  real PostgreSQL 17 and real Chromium; the synthetic fake/locmem SMTP
  backends prove only the relay-boundary semantics (acceptance vs
  rejection vs exception), exactly as the order bounds them.
- No credentials, verifiers, peppers, passwords, cookies, CSRF values,
  tokens or recipient addresses appear in this report, the diff, the
  URLs or the screenshots; the result nonce is a non-secret one-shot
  correlation token, and all test addresses are synthetic fixtures in
  the repo's existing style.
- Dependencies: none added; uv.lock, Docker/Compose, proxy, settings
  and CI configuration untouched.
- DHA: `Decision: NONE` (no CRITICAL append; the register is
  unchanged).
- Limits: this is development evidence only. No real SMTP relay,
  recipient, credential, deployment, DNS/TLS or public exposure was
  touched. The fresh exact-revision independent ICA, strategic
  development merge, human milestone judgment, release and any real
  sending (D2) remain separate and are not claimed here. CODING did
  not merge, approve or enable auto-merge.
