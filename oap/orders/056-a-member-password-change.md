<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "056-a",
  "objective": 56,
  "round": "a",
  "slug": "member-password-change",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "bfc6efd2beeeeebe9df794cdbfc0e93b38ddfff0",
  "issue_number": 116,
  "branch": "codex/116-oap-056-a-member-password-change",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f7b5c98876a40b052c2d2fe057e57281e917ac5a72508e98caca512c1f0d1286",
    "PLAN.md": "e15eb06f6559886808916812dc555c244cc038ff42996a12276b58319562f864",
    "ARCHITECTURE-for-agents.md": "66d578e9fc263a77ceb4500bb2e8dac88b6080bf8f38890942fd46bc718f60ca",
    "src/slaif_reservation/web/forms.py": "c90d7590edcecbc44eb3a05d898a101c2072a5e9c8f5b732315aa7811476dfda",
    "src/slaif_reservation/web/views.py": "3c1840292bd6db9c40665d1faee8bec87a29981490c1c01186e52b676ddcf29d",
    "src/slaif_reservation/web/urls.py": "16bfe798fd4c1f8539a1939f2f656be3fdf009d02842f88cad7674b61f505651",
    "src/slaif_reservation/accounts/admin.py": "ad8e1610181d0ed9186406717c463ebb2ff34bc4f8792cf89506478daa73fa34",
    "docs/human-ui.md": "b63b79431cebdc5484148529772a988e7c475fc582fea9108b130bbc83dcf381",
    "docs/security-model.md": "7fcd7abf72a7c7c5e8db9dccaa47e9d281e4662a221caf3add6bf002d6c4d1f1"
  },
  "requirements": ["SAR-014", "SAR-040", "SAR-043", "SAR-044", "SAR-054"],
  "allowed_paths": [
    "src/slaif_reservation/web/forms.py",
    "src/slaif_reservation/web/views.py",
    "src/slaif_reservation/web/urls.py",
    "src/slaif_reservation/web/templates/web/profile.html",
    "src/slaif_reservation/web/templates/web/password_change.html",
    "src/slaif_reservation/accounts/admin.py",
    "tests/test_member_password_change.py",
    "tests/browser/test_member_password_change_browser.py",
    "tests/test_form_guidance.py",
    "tests/browser/test_form_guidance_browser.py",
    "docs/human-ui.md",
    "docs/security-model.md",
    "oap/active",
    "oap/orders/056-a-member-password-change.md",
    "oap/reports/056-a-member-password-change.md"
  ],
  "forbidden_resources": [
    "No SMTP/email, administrator onboarding/temporary six-character credential, new user model field/migration, public forgotten-password reset/self-registration, API/bearer route, password-validator/settings/dependency/lock change or login-rate-control change.",
    "No reservation/asset/group/permission/audit/domain/DB-schema mutation, Docker/Compose/proxy/deploy/workflow/OAP machinery/ARCHITECTURE/PLAN/projection/CRITICAL or unrelated UI redesign.",
    "No real account/SMTP/secret/private-data/production DB/host/DNS/TLS/firewall/exposure/deployment, foreign PR113/branch edit/reset/force, merge/automerge by CODING."
  ],
  "provenance": [
    {"marker":"H","source":"Human 2026-11-09 explicitly selected logged-in user password change and requested OAP plan THEN implementation; 2026-11-10 demanded immediate functional code after contract","section_or_evidence":"This is the first product-code purpose, not another planning-only round. A member can change their own password after sign-in; no public reset is selected."},
    {"marker":"A","source":"Merged ARCHITECTURE.md A-17/SAR-054 and SAR-014/040/043/044; PLAN.md P-09","section_or_evidence":"Current password required, normal validators including existing minimum, CSRF, active non-service human, only self, current session retained, other sessions invalidated; no bearer mutation/reset/email, product identity/help. Existing session and group/booking invariants preserved."},
    {"marker":"E","source":"Live merged main bfc6efd2beeeeebe9df794cdbfc0e93b38ddfff0 / PR115 exact reviewed report-head five CI green; source inspection 2026-11-10","section_or_evidence":"Web profile edits display name/timezone only; no password-change route; UserAdmin add help falsely says members cannot change their password once this feature lands. Django5.2 PasswordChangeForm and update_session_auth_hash are available. Foreign PR113 remains open and touches web/forms.py, web/views.py, docs/human-ui.md, so preserve/reconcile without editing that PR."},
    {"marker":"I","source":"Current web/login/decorator/form/template/test structure and Django 5.2 official auth guidance","section_or_evidence":"Use one branded authenticated member route at /profile/password/ with standard old/new/confirmation validation and safe session-hash update. Link from Profile. No credential value in rendered errors, logs or report. Existing model and validators remain byte-identical."},
    {"marker":"C","source":"STRATEGIC full source and prior exact-head review, CRITICAL empty","section_or_evidence":"D0/DHA NONE. Strongest objection: a self-service password change could accidentally permit other-account mutation, bypass CSRF or log the submitted secret. Guard with active-human decorator and sensitive POST handling; verify direct negative requests, CSRF, session semantics and no secret rendering. No real identity action."}
  ],
  "decision_class": "D0",
  "target_gate": "One reviewed development PR delivering logged-in own-password change; no SMTP/onboarding/milestone closure/real deployment claim",
  "expected_report_path": "oap/reports/056-a-member-password-change.md",
  "tests": [
    "Focused Django tests: anonymous/inactive/service-account/Bearer-only direct GET+POST denial; current password required; wrong current/mismatch/weak/common new password rejected with no DB change; valid own change updates hash, old credential fails, current session continues, separate session invalidates, other account unaffected; GET and failed POST never echo password/hash; forged POST without CSRF denied.",
    "Focused real Chromium HTTP/PostgreSQL at desktop1440 and mobile390: Profile link, guided fields with labels/help/aria association, successful change and current-session continuity, wrong-old validation, no horizontal overflow/framework branding; privacy-safe screenshots inspected in batches<=2.",
    "Relevant existing member login/profile/admin-help/browser tests and no OpenAPI/API/migration/constraint diff; ruff/format/mypy/check/no-migrations, docs links/diff; normal full five CI checks at exact implementation and report heads, then reviewed merge."
  ]
}
-->

# 056-a — logged-in member password change

## Goal and source boundary

Deliver the first visible feature of the human-selected M-ACCOUNT-ONBOARDING target. Active, non-service-account human members can change only their own password after sign-in. Use existing Django password validation/hash/session behavior, not a parallel credential engine. This is a new objective after merged 055-b, issue116, base/branch in metadata. The foreign PR113 is separately open and overlaps web/forms.py, web/views.py and docs/human-ui.md; inspect it read-only before editing/merging to avoid clobbering or misattributing its work. Reconcile if main changes; never edit or merge PR113 as part of this order.

## Compact ordered reads

Normal CODING startup set and this order; compact projection SAR-014/040/043/044/054 plus A-17 reference only as needed, current web/urls.py, profile/login views/forms/templates, accounts/admin.py add-form help, active_human_required decorator, relevant existing tests/browser fixture and docs/human-ui.md/security-model.md affected paragraphs. Official Django5.2 PasswordChangeForm/update_session_auth_hash as technical reference; no full strategic history or whole Gateway repository.

## Numbered acceptance and negative paths

1. Add GET+POST `/profile/password/` (`web:password-change`) for an authenticated active non-service-account human, with an obvious link on Profile. GET shows product-branded title, current password, new password, confirmation, normal validator guidance and accessible help near controls; password widgets never prefill/echo a secret. Only POST changes the current request user's password. GET and error responses do not reveal password hashes or other users' data. Member login/profile/reservation/token behavior remains otherwise unchanged.
2. Use Django's standard PasswordChangeForm validation and password hashing, including current password and the unchanged global minimum/other validators. CSRF is mandatory. Wrong old password, mismatched/weak/common new password and missing fields fail without mutating the User. Protect submitted values from exception/request logging (sensitive POST handling); never include them in messages/audit/report/test output. Do not add a bearer/API mutation route or public reset flow.
3. On success, call the standard session-auth-hash update so the current browser remains signed in and other sessions for that account are invalidated. Redirect to Profile or a clear success page with a nonsecret confirmation. Old password no longer authenticates; new password does. A direct anonymous/inactive/service-account request cannot use the route, even if navigation is hidden. No other account can be modified. Preserve current group/permission/token/reservation behavior.
4. Replace only the now-false Administrator add-form help claim that members cannot change their own password; retain admin's per-user set/change action and existing validator help. Update docs/human-ui and security-model current behavior while keeping public forgotten-password reset, email onboarding and OIDC correctly deferred until later objectives. No model/migration/settings/proxy/dependency/API change.
5. Focused Django and Chromium positive/negative evidence in metadata tests, desktop/mobile screenshots actually viewed (<=2 per batch), relevant existing member/admin test changes only where an old assertion became false. Run normal five CI checks at exact frozen implementation AND report heads, honest failure labels, then strategic review/conditional development merge. PR body `Closes #116`; no code publication to real deployment.

## Recovery and report

Fresh CODING context via existing right-pane OAP wrapper: source supervision `codex.sh` FROM development checkout, `codex --yolo --profile early-beta` (human-confirmed model/backend). If interrupted, resume same ID/branch/PR and preserve foreign work; no reset/clean/force. Commit/push only allowed implementation+order/pointer paths, create one PR before immutable report, record literal implementation head/SELF in report-only child, verify remote first-parent/path/PR identity and send exact FIFO OK. Strategy accepts only reviewed five-green report head and no D2 crossing. No CRITICAL entry is needed for this routine self-change interface.

## Deferred human adjudication
- Decision: NONE
