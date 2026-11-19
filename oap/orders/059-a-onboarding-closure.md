<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "059-a",
  "objective": 59,
  "round": "a",
  "slug": "onboarding-closure",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "0c4a58e419005b87585b7621f309ab4f6f704d99",
  "issue_number": 122,
  "branch": "codex/122-oap-059-a-onboarding-closure",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f7b5c98876a40b052c2d2fe057e57281e917ac5a72508e98caca512c1f0d1286",
    "PLAN.md": "e15eb06f6559886808916812dc555c244cc038ff42996a12276b58319562f864",
    "CRITICAL.md": "f5c4d78ed599ac9a8ce44687925dab29f221d8b65a2350a4f858c9f32a92c672",
    "docs/audit/ICA-PROTOCOL.md": "67075c18b6102e3cbd23c5b4836ca0e004be374458dbd5e5396bbeefdeaa098f",
    "src/slaif_reservation/accounts/admin.py": "967da3e7d135391264212e313f2421463812ab81969c786ef51f071ae2d4c171",
    "src/slaif_reservation/accounts/onboarding.py": "4cd94c2ab6d8bc66a20053e11694bd101eab85dabd42b560c669a3b9a77b00b5",
    "src/slaif_reservation/web/templates/admin/accounts/user/change_form.html": "abbe6654341cc798209c411a876080091a9f891f499246ea32f22b15fa01ee1f",
    "tests/test_account_onboarding.py": "628c57bc31ae4b1c49c50f136478203c1a08bf63f9c266f87abf0a4a6597ecde",
    "tests/browser/test_account_onboarding_browser.py": "90ddeea6a06df3fb69784291f04285abb00c9f52efe3219c6f63db91a0deee45",
    "tests/test_form_guidance.py": "5b26c7bc8ae59a2e7ffe5dae64da3bbe12ecb5dc7c9e0f64107a4839984414d1",
    "INSTALL.md": "0426a02d2a77cc650eb0245ba7497f07fdca0c971f81bfc463b661c337172d7f",
    "docs/deployment.md": "f6622c8b15a0ca181582f079b7152075b6dcf3909de2af69892aabbcbcdeb645"
  },
  "requirements": [
    "SAR-014",
    "SAR-023",
    "SAR-026",
    "SAR-036",
    "SAR-038",
    "SAR-043",
    "SAR-044",
    "SAR-055",
    "SAR-056"
  ],
  "allowed_paths": [
    "src/slaif_reservation/accounts/admin.py",
    "src/slaif_reservation/web/templates/admin/accounts/user/change_form.html",
    "tests/test_account_onboarding.py",
    "tests/browser/test_account_onboarding_browser.py",
    "tests/test_form_guidance.py",
    "INSTALL.md",
    "docs/deployment.md",
    "oap/active",
    "oap/orders/059-a-onboarding-closure.md",
    "oap/reports/059-a-onboarding-closure.md"
  ],
  "forbidden_resources": [
    "No User model/migration, authentication backend/member password change/onboarding callback or SMTP settings/resolver, reservation/asset/policy/group/token/API, dependencies/lock, Docker/Compose/proxy/trust, architecture/PLAN/CRITICAL/projection/OAP helper/workflow or historical audit/order/report edits.",
    "No real SMTP/recipient/credential, real identity administration, private data/production DB/host/DNS/TLS/firewall/public exposure/deployment, foreign PR113 mutation or CODING merge/automerge."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human 2026-11-09 account-onboarding product decision and 2026-11-10 implementation urgency; development-merge authority confirmed for public repository",
      "section_or_evidence": "Same selected M-ACCOUNT-ONBOARDING. No new human product choice: this objective closes a defect against the already accepted activation-only-after-relay rule and current operator truth."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE.md A-17/SAR-055 and SAR-036/SAR-038; docs/audit/ICA-PROTOCOL.md",
      "section_or_evidence": "An administrator-created pending account stays inactive until exactly one post-commit SMTP relay acceptance; failed/uncertain send requires explicit reissue. Current operator docs must distinguish implemented onboarding email/own-password change from deferred OIDC/public reset/general notifications. Fresh full-matrix ICA is required after remediation."
    },
    {
      "marker": "E",
      "source": "Fresh independent architecture-first ICA against exact merged main 0c4a58e419005b87585b7621f309ab4f6f704d99, private report SHA256 2972d29e52164bf9168208ec10e80383e78cfd648a6580910ab72ba43640989a; all five exact-main CI green",
      "section_or_evidence": "Auditor dynamically mapped SAR-001..056: 53 IMPLEMENTED, 3 PARTIAL (036,038,055). Owned disposable PG17/CSRF-valid HTTP reproduction: synthetic zero-accept Add creates inactive pending user; UserAdmin change POST with is_active=on returns302, persists active, and temporary credential authenticates without SMTP acceptance. Current INSTALL lines726/738 and docs/deployment line722 still say password/email workflows absent. Audit containers removed; no real mail/deployment."
    },
    {
      "marker": "I",
      "source": "Current UserAdmin fieldsets/save_model(change=True), pending state helper, existing Admin HTTP/browser tests and current operator sections",
      "section_or_evidence": "Make is_active read-only/unchangeable for an inactive pending account in Admin, with a server-side backstop against forged POST; do not affect ordinary accounts or deactivation of active accounts. Explain accepted recovery via configured SMTP and reissue. Correct exactly the stale current operator lines. Add negative real PG/CSRF/Admin/browser tests; preserve all domain/migration/proxy behavior."
    },
    {
      "marker": "C",
      "source": "Independent ICA F-01/F-02 and selected human target; CRITICAL register empty",
      "section_or_evidence": "D0/DHA NONE. Strongest objection is restricting an administrator\u2019s emergency activation control; the already selected fail-closed enrollment contract requires this, and explicit reissue remains available. A trusted operator with direct DB access remains outside the browser Admin boundary and is not made safe by this change. No D2 crossing."
    }
  ],
  "decision_class": "D0",
  "target_gate": "Reviewed development PR fixing F-01 activation bypass and F-02 current operator prose, exact-head five CI green; after merge independently repeat full SAR-001..056 architecture-to-current-main ICA before any milestone claim; no real SMTP/deployment",
  "expected_report_path": "oap/reports/059-a-onboarding-closure.md",
  "tests": [
    "Owned real PostgreSQL + CSRF-valid Admin HTTP: synthetic zero-accept SMTP through actual Add GET/POST creates pending inactive account; Admin change GET shows activation unavailable/readonly with useful explanation; direct crafted change POST including is_active=on plus all required fields cannot activate, cannot make authenticate accept temporary credential, and does not mutate unrelated fields or create false delivery status. Standard user change permissions and CSRF remain enforced.",
    "Positive preservation: accepted SMTP activates only through exact-generation callback; ordinary non-onboarding account administrators may still activate/deactivate with existing permission; active pending account may be deactivated deliberately if current UI permits, then reissue is required to reactivate. Reissue, forced-change, normal password validation, service-account denial and CLI createsuperuser remain unchanged.",
    "Chromium Admin desktop/mobile: failed-delivery account clearly shows why activation is unavailable and reissue path; no framework branding/overflow/secret display. Focused onboarding/form-guidance/browser tests, docs relative links, ruff/format/mypy/check/no-migrations and full normal five exact-head CI at implementation/report heads. No unrelated bespoke qualification. After merge, new independent full-matrix ICA; preserve failed private audit evidence."
  ]
}
-->

# 059-a — close account-onboarding ICA blockers

## Goal and scope

Fix the independently reproduced SAR-055 activation bypass and three stale current operator sentences on the exact merged main identified in metadata. This is a new proof-sized closure objective, issue122/branch as declared. Do not replay 058 or rewrite its reports. The independent ICA against `0c4a58e419005b87585b7621f309ab4f6f704d99` remains a failed historical checkpoint: 53 IMPLEMENTED, SAR-036/038/055 PARTIAL. Its private artifact has the SHA-256 in provenance; the concrete F-01/F-02 evidence is reproduced below so CODING need not ingest the full strategic audit.

## Numbered acceptance and negative paths

1. **Pending-account Admin activation guard.** When an Administrator-created account is inactive and pending its first forced change (non-null onboarding expiry), the Administration User change form must not offer an editable `is_active` switch that can make it active. A manually constructed POST with `is_active=on` and all required current form fields must also fail safely or ignore the attempted activation; the account remains inactive, its password hash/expiry unchanged, no false relay-acceptance status appears, and a fresh login with the correct temporary value is refused. Preserve account change permission/CSRF checks. Use the existing pending state and relay callback; do not introduce another model field or change the SMTP send path.
2. **Ordinary account operations remain.** Non-onboarding accounts retain normal permission-checked Admin activation/deactivation. An accepted-delivery active pending account may be deactivated deliberately if existing Admin behavior allows it; subsequent activation must require the already supported explicit SMTP reissue, not a manual checkbox. The accepted-delivery callback still activates the exact generation; failed delivery and reissue paths, forced change, expiry, service-account denial, CLI superuser and group grants remain unchanged.
3. **Current operator prose.** In `INSTALL.md` (the two current lines near the security/operating-limits sections) and `docs/deployment.md` (current operating-limits paragraph), replace the false “password-reset/email workflows absent” wording with a precise distinction: administrator-created onboarding email and logged-in own-password change work when configured; public forgotten-password reset, OIDC and general notifications remain deferred. No historical audit/bootstrap rewrite. Do not turn README into a ledger.
4. **Evidence/publication.** Focused positive and negative tests per metadata, real owned PostgreSQL/Admin HTTP/CSRF and Chromium desktop/mobile with at most two privacy-safe screenshots viewed at a time, docs links, and normal five exact-head CI. On the declared branch open one PR with `Closes #122`, publish immutable implementation then report-only child with literal implementation head/SELF and remote verification/FIFO OK. CODING never merges. Strategy reviews/merges only after exact checks; fresh independent full architecture-to-new-main ICA follows and is not CODING self-certification.

## Strongest objection and recovery

Removing the manual activation switch for an inactive pending account can slow emergency account recovery. The selected human onboarding contract deliberately makes relay acceptance the activation boundary; configure SMTP and use explicit reissue. A database operator can still deliberately act outside the web application’s Admin boundary, which this objective does not regulate. D0, Decision NONE; no real SMTP, recipient, identity, data or deployment. Fresh CODING through sourced supervision `codex.sh`, `--yolo --profile early-beta` in the right tmux pane. Preserve foreign PR113 and all valuable worktrees/resources.

## Deferred human adjudication
- Decision: NONE
