<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "058-b",
  "objective": 58,
  "round": "b",
  "slug": "onboarding-delivery-boundaries",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "77742ba8108c00ba9d8c38334651ebbb3fc13cb6",
  "issue_number": 120,
  "branch": "codex/120-oap-058-a-admin-onboarding-email",
  "pr_mode": "AMEND",
  "pr_number": 121,
  "previous_round": "058-a",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f7b5c98876a40b052c2d2fe057e57281e917ac5a72508e98caca512c1f0d1286",
    "PLAN.md": "e15eb06f6559886808916812dc555c244cc038ff42996a12276b58319562f864",
    "oap/reports/058-a-admin-onboarding-email.md": "88f3f5fea853149776f1040352054b698087947e52df53f1fb50fc585d5311f9",
    "src/slaif_reservation/accounts/admin.py": "e295b1c3e43873837fb9d8caf836abdbac28d9c4619be1d417ee7a9847342242",
    "src/slaif_reservation/accounts/forms.py": "1229a5f4f3a08e43f69440ea35d0a4a1a1b0b4c25682fa1bf7cfd06cfc428a7a",
    "src/slaif_reservation/accounts/onboarding.py": "7b1ab6b33a68747245490f85623afc21d5828204b29c2871b4788695082fd22a",
    "src/slaif_reservation/accounts/backends.py": "79f29a2fd9f67a360aead622d8b98537e94b744f84e3712d2bf0e364f6a862e3",
    "src/slaif_reservation/web/forms.py": "cff364eb6e2bd162bf3a552b0c37083078662f31a929b7b8960f7992900b1f98",
    "src/slaif_reservation/web/views.py": "0f3a9300910aadc4c8eb3c0ed8a1e5eb83d8cd922973fbc152f83f4d7fa20c74",
    "src/slaif_reservation/web/templates/admin/accounts/user/add_form.html": "00373dc6d9696bc03d78bf961cf2387bc2bed100277a44c9015eb0212258099d",
    "src/slaif_reservation/web/templates/admin/accounts/user/change_form.html": "c9af72c977a463e7fb535d103fe049e93c1ef240976f40da1bd856d03556d8ad",
    "docs/security-model.md": "232264a0d5292103d59359c90bd1060c299f0f2249d5fee491d16ddcad559638",
    "tests/test_account_onboarding.py": "d309607ce1592af587f3480baf64d6701acb95f38ae4c0061f8436bc522b1580",
    "tests/browser/test_account_onboarding_browser.py": "ecdaa2db08d19679b947442c4301647d1ece2c58ea925f9a21e2a5af455e66dd"
  },
  "requirements": [
    "SAR-014",
    "SAR-023",
    "SAR-026",
    "SAR-040",
    "SAR-043",
    "SAR-044",
    "SAR-054",
    "SAR-055",
    "SAR-056"
  ],
  "allowed_paths": [
    "src/slaif_reservation/accounts/admin.py",
    "src/slaif_reservation/accounts/forms.py",
    "src/slaif_reservation/accounts/onboarding.py",
    "src/slaif_reservation/accounts/backends.py",
    "src/slaif_reservation/web/forms.py",
    "src/slaif_reservation/web/views.py",
    "src/slaif_reservation/web/templates/admin/accounts/user/add_form.html",
    "src/slaif_reservation/web/templates/admin/accounts/user/change_form.html",
    "tests/test_account_onboarding.py",
    "tests/browser/test_account_onboarding_browser.py",
    "docs/security-model.md",
    "docs/human-ui.md",
    "INSTALL.md",
    "oap/active",
    "oap/orders/058-b-onboarding-delivery-boundaries.md",
    "oap/reports/058-b-onboarding-delivery-boundaries.md"
  ],
  "forbidden_resources": [
    "No reservation/asset/policy/group/token/API, proxy/Compose/Docker, dependency/lock, SMTP configuration resolver, User model/migration, architecture/PLAN/projection/CRITICAL, OAP helper/workflow or prior immutable order/report edits.",
    "No real SMTP/recipient/credential, real identity administration, private data/production DB/host/DNS/TLS/firewall/public exposure/deployment, foreign PR113 mutation, CODING merge/automerge."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human 2026-11-09 selected admin-created login email, own-password change and six-character prefill; human 2026-11-10 requires immediate implementation",
      "section_or_evidence": "Same issue120/PR121 onboarding objective; correct observed acceptance gaps without a new product feature or real delivery."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE.md A-17/SAR-055/SAR-056; immutable order058-a acceptance1-4",
      "section_or_evidence": "Prefill both Add User controls, email enabled Admin add, inactive until confirmed delivery, reissue rotation, forced first change and no plaintext except administrator prefill/email."
    },
    {
      "marker": "E",
      "source": "Frozen 058-a implementation c546a91b8ab74d677cfe80ed3b7d76d6d99bddb2, report-only head cf4826cb03063db5c6add76d595e7d033999dad6, PR121; exact report-head five CI SUCCESS",
      "section_or_evidence": "Source review: backend+login form admit any inactive pending account before/after failed delivery; save_model bypasses mail for manually entered normal password even with email enabled; Add GET does not prefill when email disabled; callback activation filter ignores credential generation; /static/ allowlist prefix misses slash; delivery-status session key not bound to account; security-model says no rendered secret despite intended Add prefill."
    },
    {
      "marker": "I",
      "source": "Current UserAdmin/save_model, SlaifUserCreationForm, onboarding delivery callback, auth backend/login form and existing synthetic tests",
      "section_or_evidence": "Make only accepted active pending users able to establish sessions; keep inactive failed-delivery accounts denied. With email enabled, send/force-change for both generated and manually entered validator-valid passwords. Always show generated six-character prefill; with email disabled, refuse every Admin Add POST without creating an account, while CLI createsuperuser remains usable. Bind post-commit activation to the exact saved password hash/generation, scope status to user, fix static prefix and documentation."
    },
    {
      "marker": "C",
      "source": "One consolidated frozen-head strategic correction; CRITICAL register empty",
      "section_or_evidence": "D0/DHA NONE. Strongest reason not to merge is early login or stale callback activating an account whose current credential was never accepted by SMTP. The correction changes only onboarding authorization/delivery boundary and focused evidence; no D2 crossing."
    }
  ],
  "decision_class": "D0",
  "target_gate": "Accept the same account-onboarding PR only after failed-delivery login denial, exact-generation activation, complete enabled Admin-add email, prefill and truth corrections, and five exact-head CI checks; no real SMTP/deployment",
  "expected_report_path": "oap/reports/058-b-onboarding-delivery-boundaries.md",
  "tests": [
    "Focused synthetic PostgreSQL/admin HTTP: failed/zero/uncertain SMTP leaves account inactive AND a known correct temporary credential cannot establish member or Administration session; accepted SMTP activates pending and gates all other routes until normal-validator own password change. Existing active users and CLI superuser unchanged.",
    "With ACCOUNT_EMAIL_ENABLED true, both unchanged generated six-character and manually entered validator-valid passwords create inactive pending accounts, send exactly once post-commit, activate only on acceptance and force first change; manual weak password remains rejected. With disabled email, Add GET still prefills both six-character controls and gives clear setup guidance; every Add POST, generated or manually entered, is refused without account, while CLI createsuperuser and existing accounts remain usable.",
    "Synthetic out-of-order callback/reissue race: a stale accepted callback cannot activate or report success for a newer credential generation; new failed delivery stays inactive; old password is invalid. Status warning is account-scoped; /static/ and /branding/ allowed by the gate. Privacy: no plaintext stored, logged, audited, screenshotted or rendered except intended non-cacheable Add prefill and one email.",
    "Real Chromium desktop1440/mobile390 for Admin add, accepted/failed delivery, forced change/reissue; privacy-safe screenshots viewed in <=2-image batches. Existing account/abuse/auth/permissions and unchanged OpenAPI; focused ruff/mypy/check/migrations/docs links; full normal five CI at exact implementation and report heads. Preserve 058-a report and code history."
  ]
}
-->

# 058-b — close onboarding delivery and admission gaps

## Goal and scope

Correct the one frozen 058-a implementation on the same issue120/PR121/branch. The 058-a report and head are immutable and verified. Its report-head quality, test, security, container and oap-harness checks are all green, but green checks do not override the source-observed failures below. No other product behavior or deployment is in scope.

## Numbered acceptance and negative paths

1. **Delivery before login.** A temporary credential belongs to an inactive account until its email has been accepted. Member and Administration login MUST reject the correct credential while the account is inactive after a failed/zero/ambiguous send or before callback acceptance. After acceptance, the account is active and its pending state forces password change before all other work; expiry still denies a new session. Reissue makes the account inactive again while delivery is pending. Preserve normal inactive/service-account denial and current-session/other-session semantics on successful change. Update tests that currently model an inactive pending user as successfully logged in: accepted-delivery pending users are active.
2. **All enabled Admin adds deliver.** When account email is enabled, a manually entered normal-validator password is also an onboarding credential: account commits inactive, gets one post-commit login-details email, activates only on accepted send, and must be changed on first login. The six-character generated-only validation exception remains narrow; manual weak/edited six-character submissions remain rejected. Without account email, refuse the Administration Add POST for either generated or manual credentials before any account is written; CLI createsuperuser and existing accounts remain usable. This fulfills the parent 058-a fail-safe rule and the human expectation that an Administration-created account gets email.
3. **Prefill is visible on Add User GET.** Both password controls display the same newly generated six-character CSPRNG value on every GET even if SMTP is disabled. A disabled transport must present clear nearby guidance that user creation requires SMTP setup, and every disabled Add POST must create no account. Keep non-cacheable add response, signed session-bound digest, no plaintext server-session persistence and ordinary validators for manual passwords.
4. **Generation-safe callbacks and status.** The post-commit send may activate only if the current account still has the exact password hash and pending expiry/generation for the credential that was sent. A stale accepted callback after reissue must not activate the newer pending credential or claim its delivery; a newer failed send stays inactive. A stale email may have been accepted by a test sink but its credential remains invalid. The administrator status flag must identify the specific account so a failed send for one user cannot show on another user's page. No automatic retry.
5. **Path and documentation truth.** Correct the /static/ prefix allowlist; test it directly. Update current Admin help/template and only necessary current operator/security prose. The sole intentional browser rendering of plaintext is the non-cacheable Add User form's two prefilled password controls; no later account/error/status page, stored row, audit/log or screenshot includes it. Do not rewrite immutable 058-a evidence; 058-b report explicitly supersedes its overbroad wording.
6. **Evidence/publication.** Focused positive/negative tests as metadata, synthetic mail only, real PostgreSQL and Chromium. Run the normal exact-head five CI checks at implementation and report heads. CODING amends PR121 (retaining `Closes #120`), commits implementation/order/pointer, then report-only child with literal implementation head and SELF, verifies remote parent/path/head and sends FIFO OK. CODING never merges.

## Strongest objection and recovery

The dangerous path is a login or callback treating an inactive/undelivered or superseded temporary credential as valid. Use the existing active flag and exact-generation conditional update; do not add a second account state or a general mail queue. This is D0, Decision NONE. Resume the same issue/branch/PR without editing the prior report or resetting valuable work. Fresh CODING through sourced supervision `codex.sh`, `--yolo --profile early-beta` in the right tmux pane. No real relay, recipient or deployment.

## Deferred human adjudication
- Decision: NONE
