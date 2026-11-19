<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "058-c",
  "objective": 58,
  "round": "c",
  "slug": "reissue-disabled-guard",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "77742ba8108c00ba9d8c38334651ebbb3fc13cb6",
  "issue_number": 120,
  "branch": "codex/120-oap-058-a-admin-onboarding-email",
  "pr_mode": "AMEND",
  "pr_number": 121,
  "previous_round": "058-b",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f7b5c98876a40b052c2d2fe057e57281e917ac5a72508e98caca512c1f0d1286",
    "PLAN.md": "e15eb06f6559886808916812dc555c244cc038ff42996a12276b58319562f864",
    "oap/reports/058-b-onboarding-delivery-boundaries.md": "306c42ccbf1dd2acfa64a3b08d990e3620495f23d7dbfbf40f504a4c4a3f86b4",
    "src/slaif_reservation/accounts/admin.py": "97d0a1095b1bc241940a63d020a213acbc2bc36fccd96c3d9fdddbd96a7a8519",
    "src/slaif_reservation/accounts/onboarding.py": "7567c16e447bb5abc3a06da5de0bef28183ff25f247b8218c1f198991055b455",
    "src/slaif_reservation/web/templates/admin/accounts/user/change_form.html": "a59789aab21f415688db954fba3aa062f3dae38843946bc1becfbe15676bdec2",
    "tests/test_account_onboarding.py": "ebf79108744788cd6de7f10595cc51ddd80e092e2bb92f081b83071cde4b90ba",
    "tests/browser/test_account_onboarding_browser.py": "56ded23b29053d1763388384f39bc57e7b455ce06730337a5dc52aa5845c4e36",
    "docs/human-ui.md": "9f1f520599e228c25582e311331bdc1684162d4d98da79436bd51aa4076e85db"
  },
  "requirements": [
    "SAR-014",
    "SAR-023",
    "SAR-026",
    "SAR-043",
    "SAR-044",
    "SAR-055",
    "SAR-056"
  ],
  "allowed_paths": [
    "src/slaif_reservation/accounts/admin.py",
    "src/slaif_reservation/accounts/onboarding.py",
    "src/slaif_reservation/web/templates/admin/accounts/user/change_form.html",
    "src/slaif_reservation/web/templates/admin/accounts/user/onboarding_reissue.html",
    "tests/test_account_onboarding.py",
    "tests/browser/test_account_onboarding_browser.py",
    "docs/human-ui.md",
    "docs/security-model.md",
    "oap/active",
    "oap/orders/058-c-reissue-disabled-guard.md",
    "oap/reports/058-c-reissue-disabled-guard.md"
  ],
  "forbidden_resources": [
    "No account model/migration, auth backend/login/member password-change, reservation/asset/policy/group/token/API, SMTP settings/resolver, proxy/Compose/Docker, dependency/lock, architecture/PLAN/projection/CRITICAL, OAP helper/workflow or prior immutable order/report changes.",
    "No real SMTP/recipient/credential, real identity administration, private data/production DB/host/DNS/TLS/firewall/public exposure/deployment, foreign PR113 mutation, CODING merge/automerge."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human 2026-11-09 selected emailed login details and administrator account creation; human 2026-11-10 requires working implementation",
      "section_or_evidence": "Same issue120/PR121 onboarding milestone; completion of the approved recovery path, no new feature or real delivery."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE.md A-17/SAR-055/SAR-056 and order058-a/058-b acceptance",
      "section_or_evidence": "Email-disabled/incomplete paths fail closed, no unusable account mutation or false delivery claim, exact-generation reissue and clear admin status; synthetic SMTP only."
    },
    {
      "marker": "E",
      "source": "Frozen 058-b implementation head 4775678790d5975537e27dcb7fafbe090740603b, report-only head d06be8f9d5b80a1864359ac93fa18bd632d904e3, PR121; five implementation-head CI checks green; screenshot and source review",
      "section_or_evidence": "UserAdmin.onboarding_reissue has no ACCOUNT_EMAIL_ENABLED guard: POST under disabled mail rotates password, sets inactive, logs change, then callback cannot send. Admin change page says inactive failed-delivery account \u201csigns in\u201d before warning says it cannot. delivery_status_for accepts unscoped legacy session string and may show another account\u2019s warning; 058-a legacy status was never merged to main. UI success messages say \u201cdelivered\u201d where backend only reports relay acceptance."
    },
    {
      "marker": "I",
      "source": "Existing permission-checked reissue view, current SMTP flag, account-scoped status helper and branded change template",
      "section_or_evidence": "Check email enabled before reissue GET/POST mutation; hide or disable action and explain setup on change page while disabled; preserve permission and CSRF checks. Show active-vs-inactive truthful account guidance. Ignore legacy unscoped status; report accepted-by-relay without promising inbox delivery. Add focused negative tests and browser screenshot at 1440/390, at most two images viewed."
    },
    {
      "marker": "C",
      "source": "One final consolidated frozen-head strategic correction; CRITICAL empty",
      "section_or_evidence": "D0/DHA NONE. Strongest reason not to merge: a disabled SMTP reissue silently invalidates a working temporary password and locks an account without sending new details. All fixes are confined to existing onboarding recovery/UI truth; no D2 crossing."
    }
  ],
  "decision_class": "D0",
  "target_gate": "Accept same PR121 only after disabled-SMTP reissue refuses without mutation, status text matches account state/relay acceptance, focused browser/HTTP tests and five exact-head CI checks; no real email/deployment",
  "expected_report_path": "oap/reports/058-c-reissue-disabled-guard.md",
  "tests": [
    "On a pending active accepted account and a pending inactive failed-delivery account, set ACCOUNT_EMAIL_ENABLED false: reissue GET/POST direct requests do not rotate hash/expiry, change activity, create LogEntry or send; visible action is hidden or clearly disabled; permission and CSRF boundaries remain. When re-enabled, normal reissue still rotates once and sends once.",
    "Admin change page for inactive pending account says it cannot sign in until confirmed relay acceptance; active pending account explains forced change without false inactive warning. Success status says relay accepted/queued, not inbox delivered. Ignore a legacy unscoped status session value for all accounts; current per-account mapping still displays only the matching warning.",
    "Real Chromium desktop1440/mobile390 for safe failed-delivery and disabled-reissue UI, inspect at most two privacy-safe screenshots; focused onboarding/admin tests, changed docs links, ruff/mypy/check/no-migrations, then normal five exact-head CI on implementation/report. Preserve prior reports and all non-onboarding files."
  ]
}
-->

# 058-c — guard disabled-SMTP reissue and truthful account status

## Goal and scope

Finish the existing account-onboarding recovery boundary on the same issue120/PR121/branch. The 058-b report and implementation heads are immutable. This is a small correction to an observed lockout path and false administration status text, not a new account or mail feature. Wait for terminal 058-b report-head CI before activation.

## Numbered acceptance and negative paths

1. **No reissue without mail.** When account email is disabled, both GET and POST of the reissue route refuse safely after the existing permission check. A POST must not generate/rotate a credential, set an account inactive, alter expiry, create a reissue audit LogEntry, register a send or call a dummy backend. The user change page must not present a working reissue action while disabled and should tell the administrator to configure account email before retrying. Test active accepted-pending and inactive failed-delivery accounts, including direct forged POST, CSRF and change-permission boundaries. Re-enabling mail preserves one explicit rotation and one post-commit send.
2. **State-specific and relay-accurate text.** An inactive pending account page says it cannot sign in until the login-details email is accepted by the relay; an active pending account explains the forced change and expiry. Do not assert inbox delivery from a `send_mail` return of 1: success messages/status use “accepted by the email relay” or equivalently precise plain language. Reissue confirmation remains explicit about rotation and ambiguous delivery. No credential appears on later pages or in logs/audit.
3. **Status bound to account.** `delivery_status_for` must ignore old unscoped session strings (058-a was never merged to main) rather than applying one account’s warning to every pending account. Current per-account map remains; a user-specific failed-delivery warning appears only on its account page. Keep session metadata nonsecret and bounded to this purpose.
4. **Evidence/publication.** Focused tests and privacy-safe browser review per metadata. No model/schema/auth/backend/SMTP settings/reservation/proxy change. Amend PR121 with implementation/order/pointer, then report-only child with literal implementation head and SELF; verify remote parent/path/head, send FIFO OK. CODING never merges. Full exact-head five CI is required at implementation/report heads. No real relay/recipient/deployment.

## Strongest objection and recovery

The dangerous current path is a privileged but ordinary administrator clicking reissue after SMTP has been disabled: it invalidates a still-working password and makes the account inactive without any chance to deliver the replacement. Fail before mutation and explain recovery. D0, Decision NONE. Fresh CODING through sourced supervision `codex.sh`, `--yolo --profile early-beta` in right pane; preserve foreign PR113 and valuable worktrees/resources.

## Deferred human adjudication
- Decision: NONE
