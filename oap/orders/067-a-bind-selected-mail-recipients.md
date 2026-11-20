<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "067-a",
  "objective": 67,
  "round": "a",
  "slug": "bind-selected-mail-recipients",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "255652843da759166d6b7772af53b217ab61cb05",
  "issue_number": 139,
  "branch": "codex/139-oap-067-a-bind-selected-mail-recipients",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "c01fe2fcab3bb5b360f7065737a3440f155884150f25a2f47b931ec3fd19d2ca",
    "PLAN.md": "6642b433fae5f56548bcf3765093a9a4821a1a4ab58b533883f3b9cac3128e59",
    "ARCHITECTURE-for-agents.md": "dcae030bf6a5c01c2ef48e8e01adbe852a92e6a8e8ca799319d8c447cf1f3cf0",
    "CRITICAL.md": "f5c4d78ed599ac9a8ce44687925dab29f221d8b65a2350a4f858c9f32a92c672",
    "src/slaif_reservation/accounts/admin.py": "6ed2b9c4ee6fa60d05e670ff335f85da230c6fea1859755df793f737cd782a03",
    "src/slaif_reservation/accounts/bulk_email.py": "019e1541342d4ee709994745c676fa3b316fcbd8f6532c4c456ac91217cc8009",
    "src/slaif_reservation/web/templates/admin/accounts/user/bulk_email.html": "01dec5f9bd874b80831dfd9cd5d4488801e7c78b89749018bd2737746cdb8a32",
    "tests/test_admin_bulk_email.py": "6eb560523177054441343bdabb54ef82b2800383466598a45ba3838a18724075",
    "tests/browser/test_admin_bulk_email_browser.py": "ef2f96e85ac3f5e1039eb48bba12ff7d48947511350cc2a41c690806305c5dd3",
    "docs/security-model.md": "3788f89abc8e856de2ad2ac91b4a57296ffb2c01df2c010a0c349a81dc0630ef",
    "docs/human-ui.md": "460938f6c1354ee15aac56a7997771a124d608a33e32fdd9298a79a64dcca613",
    "docs/audit/ICA-PROTOCOL.md": "67075c18b6102e3cbd23c5b4836ca0e004be374458dbd5e5396bbeefdeaa098f"
  },
  "requirements": [
    "SAR-014",
    "SAR-026",
    "SAR-032",
    "SAR-043",
    "SAR-044",
    "SAR-055",
    "SAR-058"
  ],
  "allowed_paths": [
    "src/slaif_reservation/accounts/admin.py",
    "src/slaif_reservation/accounts/bulk_email.py",
    "src/slaif_reservation/web/templates/admin/accounts/user/bulk_email.html",
    "tests/test_admin_bulk_email.py",
    "tests/browser/test_admin_bulk_email_browser.py",
    "tests/test_form_guidance.py",
    "docs/human-ui.md",
    "docs/security-model.md",
    "docs/ux/form-guidance-inventory.md",
    "oap/active",
    "oap/orders/067-a-bind-selected-mail-recipients.md",
    "oap/reports/067-a-bind-selected-mail-recipients.md"
  ],
  "forbidden_resources": [
    "No real SMTP/recipient/credential, deployment, DNS/TLS/firewall, real user data, production DB, physical resource, or exposure. Tests use synthetic accounts with locmem/fake transport only.",
    "No account/onboarding/permission/asset/reservation/schema/migration/dependency/lock/Docker/Compose/proxy/settings/CI/OAP helper/governance/architecture/PLAN change; no generalized mailing framework, queue, HTML/attachments, export or campaign. Preserve 066-a one-click compose, per-recipient privacy, cap and PRG result; CODING never merges."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Attributable human selected checkbox-based Administration mail to the CHECKED users and requested OAP CODING through PR/CI/merge; issue #137 original objective, issue #139 records independent closure findings.",
      "section_or_evidence": "Unselected users must receive nothing; one Send email click after composing; no real send authorized."
    },
    {
      "marker": "A",
      "source": "Current ARCHITECTURE.md A-19/SAR-058 at exact SHA 2556528, SAR-032 exact-head CI, preserved SAR-055 SMTP/onboarding and SAR-026 privacy; ICA-PROTOCOL requires fresh architecture-to-current-main re-audit after remediation.",
      "section_or_evidence": "Implement existing stable selected-user requirement; no new product meaning or requirement ID. The final POST must derive recipients only from the prior checked selection in the same administrator session, not browser-provided UUIDs."
    },
    {
      "marker": "E",
      "source": "Fresh isolated ICA at exact merged main 255652843da759166d6b7772af53b217ab61cb05, full ARCHITECTURE.md digest c01fe2fcab3bb5b360f7065737a3440f155884150f25a2f47b931ec3fd19d2ca, private complete matrix SHA256 64b60486e2f96f85ee6c0db7381d335767a6728bb85208de2f7dbfa013954564; issue #139.",
      "section_or_evidence": "ICA F-1: accounts/admin.py final POST resolves request.POST[selected_pks] against existing UUIDs with no checkbox/compose binding; a valid unselected UUID can be mailed. F-2: exact main CI run44688064642 test FAILURE (1 failed,1522 passed) at browser mail test line142, assumes fixture order while Admin action sorts random UUIDs. PR#138 implementation/report heads five checks green, but merged main CI red; no remediation yet."
    },
    {
      "marker": "I",
      "source": "Existing UserAdmin action/compose/send flow, Django session, CSRF and permissions, current synthetic email and Chromium fixtures.",
      "section_or_evidence": "At action time create a bounded random nonce and session-held UUID selection (no addresses/subject/body); GET compose and final POST require same-session nonce and resolve only stored selected UUIDs; new selection supersedes old; invalid/foreign/stale nonce or missing user fails before send. Remove client-selected-pks authority. Keep 200 cap, permission/CSRF/disabled-SMTP/PRG. Browser assertion compares exact recipient set and per-message privacy independent of ordering."
    },
    {
      "marker": "C",
      "source": "Human already selected exact checkbox semantics; independent ICA demonstrated a narrower implementation defect and exact CI defect; CRITICAL register has no relevant unresolved entry.",
      "section_or_evidence": "D0/Decision NONE. Strongest objection: session-bound selection can make a previously opened compose tab stale when a new selection is made. Fail closed with a clear reselect message, keep one pending selection per session and test churn. No D2 action."
    }
  ],
  "decision_class": "D0",
  "target_gate": "One reviewed development closure PR for issue #139 with exact checked-selection binding and deterministic browser assertion, negative synthetic tests, five exact-head CI at implementation/report heads and green post-merge main; then fresh independent full SAR001..058 ICA. No real SMTP/deployment.",
  "expected_report_path": "oap/reports/067-a-bind-selected-mail-recipients.md",
  "tests": [
    "Synthetic server: action-selected A/B bind to one session nonce; compose and send show/email exactly A/B. Direct GET or final POST with valid C UUID but no prior checkbox selection fails; tampering hidden field to add/swap C never sends to C. Foreign session nonce, stale nonce after new selection, missing/deleted selected account, empty/oversized/select-across rules, permission loss between GET/POST and CSRF all fail before send. No addresses/subject/body in URL/session/logs; session may hold UUIDs only.",
    "Preserve one-click compose, one plain-text message per selected recipient, no CC/BCC, disabled transport fail closed, stop-on-failure counts and PRG refresh-never-resends; no new model/config/permission/SMTP behavior. Focused server tests include account onboarding and mail settings as affected regressions.",
    "Chromium desktop/mobile real HTTP with synthetic locmem mail: select A/B, forge C valid UUID in final request, assert C receives none; normal selection sends exact set. Fix existing browser test to compare selected address set/per-message privacy without assuming UUID order; rerun focused Chromium and inspect privacy-safe screenshots <=2 at a time if UI changes.",
    "Normal ruff/format/mypy/Django check/makemigrations/diff/link checks and five exact-head CI at frozen implementation and report heads. CODING pushes one PR Closes #139, immutable report-only child with literal implementation SHA/SELF, verifies remote and signals FIFO OK; CODING never merges. Strategy merges only after exact-head review and checks; post-merge main CI must pass, then fresh independent full architecture-to-current-main ICA."
  ]
}
-->

# 067-a — bind selected-user mail recipients to the checked Admin selection

## Goal and authority

Close the two precise independent-audit/CI findings at exact merged main `255652843da759166d6b7772af53b217ab61cb05`, issue #139. This is a narrow repair of already-selected SAR-058 and the flaky browser assertion under SAR-032, not a new mail feature. The immutable initial full-matrix ICA is retained privately by strategy; do not edit it or pre-claim a passing re-audit.

## Numbered acceptance and negative paths

1. **Bind the checked selection.** The UserAdmin checkbox action must establish the exact selected user UUID list (≤200) and a random nonce in the current authorized administrator session, without storing subject/body/addresses. Compose GET and final send POST require that same-session nonce; final recipients derive ONLY from the stored checked IDs, never from an arbitrary submitted UUID list. A direct forged GET/POST with a valid existing UUID, or a valid unselected UUID added/swapped into browser fields, cannot send to that user. Invalid/foreign/stale nonce, missing selected account, no selection, >200, and replaced selection fail closed with a useful reselect message before mail. A new action selection supersedes the old pending selection. Keep active-human staff and accounts.change_user checks, CSRF, exact selection count/preview, one Send email click and selected-account current email re-read. Do not add group/permission model or DB migration.
2. **Preserve mail boundaries.** Existing opt-in SMTP config, one plain-text message per selected account, no CC/BCC, form bounds/header safety, disabled-transport refusal, partial/uncertain counts, and POST/Redirect/GET result refresh-never-resends all remain. No subject/body/recipient email address in URL/session/logs/audit. Only bounded UUIDs/nonce may be session selection state; do not expose them to unauthorised sessions. No real mail.
3. **Fix exact merged-main CI failure.** The browser test must assert the exact selected recipient SET and one private message per recipient, not fixture creation order. The action sorts by UUID PK, and UUID order is not product meaning. The CI run `44688064642` failed this assertion with 1 failed/1522 passed; obtain green exact-head CI at implementation, report and merged main.
4. **Evidence/publication.** Run focused negative/positive tests per metadata, including valid-unselected UUID tamper, direct POST, foreign/stale session, permission/CSRF, PRG, disabled/partial mail, Chromium desktop/mobile, onboarding regression and static checks. No broad unrelated qualification. Update current Admin/security docs only if needed for the session-bound selection contract. Commit exact order/pointer with implementation, push one PR `Closes #139`, publish immutable report-only child with literal implementation head/SELF, verify remote parent/path/head and signal FIFO OK. CODING never merges.

## Strongest objection and recovery

A one-pending-selection session contract can invalidate an older compose tab when an administrator starts a new selection. Prefer a clear reselect refusal over sending to a surprising recipient; test it. D0, Decision NONE. The source/branch/worktree/PR state and foreign worktrees must be reconciled before edits; no reset, clean or force. Fresh CODING through sourced `~/codex-supervision/slaif-asset-reservation/codex.sh` from checkout, `codex --yolo --profile early-beta` in the existing right pane. Real mail/deployment D2 remains unperformed.

## Deferred human adjudication
- Decision: NONE
