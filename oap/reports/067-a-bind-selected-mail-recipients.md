<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "067-a",
  "order_path": "oap/orders/067-a-bind-selected-mail-recipients.md",
  "order_sha256": "9692d48a449c57f9cea79da118e1c2f3d5cf270d2616e2293a57cc74c81553b1",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 139,
  "pr_number": 140,
  "branch": "codex/139-oap-067-a-bind-selected-mail-recipients",
  "implementation_head": "04cb66e4879f8cab923590e4b6aae43218ae640c",
  "base_sha": "255652843da759166d6b7772af53b217ab61cb05",
  "previous_round": null,
  "pr_mode": "CREATE_OR_RESUME",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "04cb66e4879f8cab923590e4b6aae43218ae640c",
    "runs": [
      {
        "run_id": "44698972713",
        "workflow": "CI",
        "jobs": {
          "quality": "PASS",
          "test": "PASS",
          "security": "PASS",
          "container": "PASS"
        }
      },
      {
        "run_id": 44698972725,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "PASS"
        }
      }
    ]
  },
  "local_equivalent_checks": "real owned PostgreSQL 17 and real Chromium at the exact implementation head: focused server mail/form suites PASSED (tests/test_admin_bulk_email.py 26/26 incl. forged/unselected-UUID, direct-POST, foreign/stale/superseded-nonce, deleted-account, select-across, CSRF/permission-loss and resubmission guards; tests/test_form_guidance.py 37/37); onboarding and mail-settings regressions PASSED (tests/test_account_onboarding.py + tests/test_account_email_settings.py 131/131); real Chromium mail flow PASSED (3/3 tests/browser/test_admin_bulk_email_browser.py at 1440 and 390 over real HTTP with a synthetic locmem sink, incl. the forged-recipient negative and the order-independent set assertion); full local product suite 1518 passed / 9 skipped / 1 failed, the single failure being the OAP-harness tmux fixture test tests/oap/test_ba38_39_tmux_config.py::Ba39OperationPrereqs::test_ba39_strategic_same_prerequisites which is environment-only (the coding process exports OAP_ROLE=CODING, conflicting with the fixture's strategic launcher subprocess; it passes 12/12 in the same environment with `env -u OAP_ROLE` and the identical oap-harness job passes in CI at the exact head) and is outside this order's product scope; ruff check / ruff format --check / mypy (148 source files) / manage.py check / makemigrations --check --dry-run / git diff --check all clean; three privacy-safe Chromium screenshots (synthetic addresses only) captured and inspected <=2 at a time; no link-check tool is configured in this repository and the doc edits added prose only (no new links)",
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 067-a — execution report: bind selected-user mail recipients to the checked Admin selection

Implementation head SHA: 04cb66e4879f8cab923590e4b6aae43218ae640c
Report publication commit: SELF

## Identity and result

COMPLETE for order 067-a (D0, `Decision: NONE`), issue #139, PR #140
(CREATE_OR_RESUME, `Closes #139`), branch
`codex/139-oap-067-a-bind-selected-mail-recipients`, base
`255652843da759166d6b7772af53b217ab61cb05` (verified equal to the
exact merged main named by the order). The order file at
`oap/orders/067-a-bind-selected-mail-recipients.md` (state FINAL,
SHA-256
`9692d48a449c57f9cea79da118e1c2f3d5cf270d2616e2293a57cc74c81553b1`)
and the `oap/active` pointer (`067-a` + LF) were committed with the
implementation commit. All order source hashes were verified against
the base revision at startup. Remote reconciliation: before this
round there was no remote branch and no open PR for issue #139 (the
prior interrupted round ended before publication); the branch was
pushed fresh and PR #140 created fresh (no resume, no renumbering —
same objective, same branch name, same PR slot). This round resumed
the same valuable WIP (session-bound selection implementation, order
and pointer) without reset/clean/stash; the only additions made this
round were the browser-test assertion fixes, a dead-code removal, a
template-comment defect repair, doc reconciliation and test guards
described below.

## Numbered acceptance evidence

### 1. Bind the checked selection

- Selection step (`UserAdmin.email_selected_users`,
  `@admin.action(permissions=("change",))`): validates the bounds
  (empty and over 200, including select-across — refused wholesale,
  never truncated) and then stores the exact checked user UUIDs
  (sorted by PK, presentation only) plus a random nonce
  (`secrets.token_urlsafe(32)`) in the administrator's own session
  (`bulk_email.store_selection`; the session holds UUIDs + nonce
  only — no addresses, subject or body). The redirect URL carries
  ONLY the nonce (`?selection=<nonce>`). `test_action_redirects_to_compose_binding_session_selection`
  (redirect parameter set, session entry is exactly
  `{nonce, pks}` of well-formed UUIDs, no address in the URL, no
  send) and `test_action_refuses_empty_and_oversized_selection`
  (empty and select-across over-bound bind nothing; exactly 200
  binds) PASSED.
- Compose GET: requires the same-session nonce
  (`bulk_email.take_selection`, constant-time compare) and renders
  only for the stored selection. `test_compose_get_shows_count_addresses_and_never_sends`
  (exact count, exact checked addresses, no unselected address, the
  form carries the session nonce and never a recipient list,
  `no-store`, and NO leaked template syntax),
  `test_compose_get_refuses_missing_forged_and_direct_url` (no
  nonce, forged nonce, and the historical `pks` parameter with a
  valid UNSELECTED account UUID — all refused back to the user list
  with a reselect notice, nothing sent) and
  `test_compose_get_refuses_superseded_and_deleted_selection` (a
  newer checked selection supersedes the older pending one — the old
  compose tab is refused while the current one composes; a deleted
  selected account is a stale selection — refused and the pending
  selection cleared) PASSED.
- Final send POST: derives recipients ONLY from the stored checked
  UUIDs; the browser-supplied list no longer exists.
  `test_final_post_never_mails_forged_or_unselected_uuids` (ICA
  F-1: a valid unselected UUID added into the browser fields of an
  otherwise legitimate send is ignored; swapping the checked set via
  a forged field sends only the stored set; no selection at all sends
  nothing), `test_final_post_refuses_missing_forged_foreign_and_stale_nonce`
  (missing/forged nonce refused; a different administrator's session
  presenting the nonce refused; a stale nonce after the selection
  was replaced refused with the replacement untouched and still
  sendable), `test_final_post_refuses_deleted_selected_account`
  (stale selection cleared, nothing sent) and
  `test_final_post_collapses_duplicate_stored_pks` PASSED.
- Authority and transport guards preserved:
  `test_action_visible_only_with_change_permission`,
  `test_admin_admission_gates_bulk_email_surface` (member/service/
  inactive staff terminated to the login, nothing sent, even with a
  forged selection parameter), `test_forged_action_without_change_permission_sends_nothing`
  (no selection bound), `test_compose_get_requires_change_permission`,
  `test_final_post_requires_change_permission`,
  `test_final_post_requires_csrf_token` (session-bound selection
  shared across a CSRF-enforcing client still yields 403 and no
  send), `test_final_post_disabled_transport_fails_closed` and
  `test_compose_get_disabled_transport_offers_no_send` PASSED.
- One pending selection per session and consumption: a successful
  send discards the pending selection so a form resubmission can
  never resend — asserted in
  `test_final_post_sends_one_plain_text_message_per_recipient`
  (resubmission with the consumed nonce is refused, outbox
  unchanged) and in the real Chromium flows (below). An invalid form
  POST does NOT consume the selection: the corrected resubmission
  sends (`test_final_post_validates_subject_and_body` tail) PASSED.

### 2. Preserve mail boundaries

- One plain-text message per selected recipient, exact set, no
  CC/BCC, unselected users receive nothing, no Admin action log
  entry, `Cache-Control: no-store`:
  `test_final_post_sends_one_plain_text_message_per_recipient`
  PASSED. Subject/body validation including CR/LF header injection
  and length bounds: `test_final_post_validates_subject_and_body`
  PASSED.
- Bounded failure semantics (synthetic backends only):
  `test_zero_acceptance_stops_without_retry` (explicit rejection
  stops after one relay call), `test_exception_after_partial_acceptance_stops`
  (no retry) and `test_all_accepted_reports_full_count` PASSED.
- POST/Redirect/GET one-shot result:
  `test_result_get_refresh_never_resends` and
  `test_result_get_refuses_invalid_and_foreign_nonces` PASSED.
- No content in URLs/logs/session/action log:
  `test_final_post_leaves_no_content_in_urls_or_logs` (action
  redirect carries only the nonce; session selection state holds
  UUIDs only; redirect and GET paths carry no subject/body/address;
  caplog clean) PASSED.
- Affected regressions unchanged and PASSED: account onboarding and
  mail settings suites (131/131 across
  `tests/test_account_onboarding.py` + `tests/test_account_email_settings.py`).
  No new model, migration, config, permission or SMTP behavior
  (`makemigrations --check --dry-run`: no changes detected).

### 3. Fix exact merged-main CI failure

- `tests/browser/test_admin_bulk_email_browser.py` now asserts the
  exact selected recipient SET and per-message privacy
  (`{tuple(m.to) for m in mail.outbox} == {(r0.email,), (r2.email,)}`)
  instead of assuming fixture creation order — the Admin action
  sorts selected rows by random UUID PK, which is not product
  meaning, and the merged-main CI run `44688064642` failed exactly
  this order assumption (1 failed / 1522 passed at
  `test_browser_admin_bulk_email_desktop_flow[chromium]` line 142).
- The flaky desktop pixel fold threshold
  (`button bottom <= viewport height`) is replaced by a semantic
  visible/enabled Send action assertion; the existing
  no-horizontal-overflow check and the manual screenshot evidence
  are kept, with no CSS churn. The mobile flow's reachable-after-
  normal-scroll assertion is unchanged.
- New Chromium negative: a valid UNSELECTED account UUID is forged
  into the final send request in the real browser (hidden field
  injected into the form) and receives no mail, while the checked
  set is still delivered exactly.
- `test_browser_admin_bulk_email_desktop_flow`,
  `test_browser_admin_bulk_email_mobile_flow` and
  `test_browser_admin_bulk_email_disabled_transport` PASSED (real
  Chromium over real HTTP, synthetic locmem sink); three privacy-safe
  screenshots (synthetic addresses only) captured and inspected ≤2 at
  a time.
- Repaired during local browser verification: the compose form
  contained a MULTI-LINE template comment, which Django template
  comments do not support (they must be single-line) — it rendered as
  literal `{# ... #}` text on the page. It is now single-line, and
  `test_compose_get_shows_count_addresses_and_never_sends` gained a
  no-template-syntax-leak guard (`{#` and the comment text absent
  from the rendered HTML).
- The exact-head `test` CI job (full suite incl. Chromium) passed at
  the implementation head (see below).

### 4. Evidence and publication

- Static checks at the implementation head: `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy src` (148 source
  files), `manage.py check`, `manage.py makemigrations --check
  --dry-run`, `git diff --check` — all clean. No link-check tool is
  configured in this repository; the doc edits added prose only (no
  new links).
- Docs reconciled to the session-bound selection contract:
  `docs/security-model.md` (recipients derive only from the stored
  checked selection behind a same-session random nonce; forged/
  foreign/stale/superseded selections and deleted accounts are
  refused before any send; a new checked selection supersedes the
  pending one) and `docs/human-ui.md` (compose page and single send
  bound to the exact checked selection; reselect notice when the
  selection is replaced or stale). The form-guidance inventory row
  remained accurate and is unchanged.
- Dead-code removal: `bulk_email.selected_pks` (the client-supplied
  comma-string parser) had no remaining callers after the binding
  and was deleted; no client-selected-pks authority remains in the
  module.
- Full local product suite at the implementation head: 1518 passed,
  9 skipped, 1 failed — the single failure is the OAP-harness tmux
  fixture test
  `tests/oap/test_ba38_39_tmux_config.py::Ba39OperationPrereqs::test_ba39_strategic_same_prerequisites`,
  which STRATEGIC independently diagnosed as environment-only: the
  CODING process exports `OAP_ROLE=CODING`, conflicting with the
  fixture's strategic launcher subprocess. With `env -u OAP_ROLE`
  the file passes 12/12 in the same environment, and the identical
  oap-harness CI job passes at the exact head (below). It is not a
  product failure and is outside this order's allowed paths (no
  helper/OAP test changes made).
- Observed implementation CI at `04cb66e4879f8cab923590e4b6aae43218ae640c`:
  CI run 44698972713 — quality PASS, test PASS, security PASS,
  container PASS; oap run 44698972725 — oap-harness PASS. Five
  exact-head checks all pass.
- PR #140 published with `Closes #139`; verified remote head equals
  the implementation head and the PR is mergeable. CODING did not
  merge, approve or enable auto-merge.

## Uncertainty, limits and follow-ups

- Report-head CI is NOT YET OBSERVED AT AUTHORING; it runs on this
  report-only child commit after push.
- Post-merge main CI and the fresh independent full
  SAR-001..058 ICA at the exact merged revision are strategy/human
  steps outside this round; no release, deployment or real
  SMTP/recipient/credential/user-data action was taken or authorized.
- The one pending-selection-per-session contract intentionally
  invalidates an older compose tab when a newer checked selection is
  made (fail closed with a reselect notice, per the order's
  strongest-objection resolution); churn is covered by
  `test_action_selection_supersedes_previous_pending_selection`,
  `test_compose_get_refuses_superseded_and_deleted_selection` and
  `test_final_post_refuses_missing_forged_foreign_and_stale_nonce`.
