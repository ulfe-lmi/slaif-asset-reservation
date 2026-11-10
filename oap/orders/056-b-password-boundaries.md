<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "056-b",
  "objective": 56,
  "round": "b",
  "slug": "password-boundaries",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "bfc6efd2beeeeebe9df794cdbfc0e93b38ddfff0",
  "issue_number": 116,
  "branch": "codex/116-oap-056-a-member-password-change",
  "pr_mode": "AMEND",
  "pr_number": 117,
  "previous_round": "056-a",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "src/slaif_reservation/web/views.py": "e4d5faa3b6d3d59fc5f427980e798a43dd95f8d6ed9a7acb3190dbcdd504c2cf",
    "tests/test_member_password_change.py": "5c67af1f74e86617b4bf6fedcf6662d75081e113959ed444d187080c03e8bef4",
    "src/slaif_reservation/web/forms.py": "f64c4f8f042cb0620777bb56499a3962f33041c5ea3c1bdd91ed11735e1e63a9",
    "src/slaif_reservation/web/templates/web/password_change.html": "148d712aeef3f94b36fb5ca70506535655a837bac924b672eb5e09ae8db8b9bf",
    "docs/security-model.md": "3c62587f61fcd3f3d757d8e01105a48f0dcf1c6ceea8e8227703302910776b69"
  },
  "requirements": ["SAR-014", "SAR-040", "SAR-043", "SAR-044", "SAR-054"],
  "allowed_paths": [
    "src/slaif_reservation/web/views.py",
    "tests/test_member_password_change.py",
    "oap/active",
    "oap/orders/056-b-password-boundaries.md",
    "oap/reports/056-b-password-boundaries.md"
  ],
  "forbidden_resources": [
    "No form/template/admin/doc change, model/migration/settings/dependency/lock, SMTP/onboarding/temporary credential, auth backend/validator/rate limit, API/bearer route or reservation/domain/permission change.",
    "No edit of immutable 056-a order/report or prior records, architecture/PLAN/projection/OAP helpers/CI workflows, Docker/Compose/proxy/deploy, foreign PR113, real account/secret/private data or deployment; CODING never merges or enables auto-merge."
  ],
  "provenance": [
    {"marker":"H","source":"Human 2026-11-09 logged-in own-password change; 2026-11-10 explicit demand for implementation","section_or_evidence":"Same issue116/PR117, no new feature or planning-only round. Protect submitted credentials while delivering the approved member page."},
    {"marker":"A","source":"ARCHITECTURE.md A-17/SAR-054 and SAR-014/040/043/044; order056-a acceptance2/3/5","section_or_evidence":"Current password, full normal validators, CSRF, current-session continuity, other-session invalidation, direct denial, no bearer mutation, secret-safe request/exception path. Only GET and POST form the member route."},
    {"marker":"E","source":"Frozen 056-a implementation e5f2cb94dcc5f4a10cfe3b832ad18b203abfbf86 / report 4457e9e5b6ca1f5f26fb624e4626bb0ab95f96bf, PR117","section_or_evidence":"Implementation-head five CI success (1316 product/160 OAP); local browser screenshots 1440/390 and error state visually reviewed, good. Report-head CI must be observed terminal. Source uses sensitive_variables('form') but not sensitive_post_parameters, whereas Django's PasswordChangeView marks POST; docs claim POST values excluded from exception logging. Bearer-only test puts result.token (ApiToken object) in Authorization header instead of the valid result.bearer_token, so it only proves invalid bearer denial. NonGET/POST methods render the GET form with 200 rather than 405 despite GET+POST contract."},
    {"marker":"I","source":"Root whole frozen source/test/diff review and Django5.2 PasswordChangeView implementation","section_or_evidence":"Three small fixes in views.py and one focused test file suffice; no UI layout/domain/session change. Standard sensitive_post_parameters decorator must cover old/new/confirmation even in exception reporter; valid bearer test must use opaque bearer secret without logging it; unsupported methods must be rejected before form creation."},
    {"marker":"C","source":"One consolidated strategic correction; CRITICAL empty","section_or_evidence":"D0/DHA NONE. Strongest reason not to merge current head: the denial test does not exercise a real bearer token and request POST secret-marking is weaker than the current security-model claim. Narrow negative-path and exception-redaction evidence closes it; no other mandatory issue found in full review."}
  ],
  "decision_class": "D0",
  "target_gate": "Accept one reviewed development PR for logged-in password change after narrow secret/method/bearer corrections and five green exact-head checks; no SMTP/onboarding/real deployment claim",
  "expected_report_path": "oap/reports/056-b-password-boundaries.md",
  "tests": [
    "Observe and record all terminal 056-a report-head jobs without waiver; prior report stays immutable.",
    "Add Django sensitive_post_parameters() to member password-change view in the correct decorator order, preserving existing sensitive_variables; focused negative test of rendered/exception output or request metadata proves all submitted credential fields are marked sensitive without echo or logging.",
    "Change bearer-only denial test to send actual issue_api_token(...).bearer_token (not ApiToken object), with no printed secret; GET/POST remain denied and account password unchanged.",
    "Return 405 with Allow GET, POST on PUT/PATCH/DELETE for an active session, no password change; focused tests. Re-run focused member+browser and relevant profile/admin tests, ruff/format/mypy/check/no-migrations, normal five CI jobs at exact implementation/report heads; unchanged UI screenshot/source evidence may be reused by byte identity."
  ]
}
-->

# 056-b — complete member password-change security boundaries

## Scope

Same issue116/PR117/branch and first frozen round 056-a. Root reviewed the entire implementation diff, focused tests, rendered desktop/mobile/error screenshots and the exact implementation-head CI once. The new member flow works, but three negative-path gaps remain. Correct ONLY those, preserve 056-a order/report bytes and all other product files. This is one consolidated corrective round, not a new feature.

## Numbered acceptance

1. Decorate the existing member password-change view with Django `sensitive_post_parameters()` so submitted `old_password`, `new_password1`, and `new_password2` are marked sensitive for technical exception reporting. Keep `sensitive_variables("form")` and the existing safe request logger. Prove with a focused failure-path test that submitted canary values are not rendered/exposed; no real passwords in test output. Do not weaken form validation, CSRF, current-session hash update or active-human gate.
2. Reject methods other than GET/POST with 405 and `Allow: GET, POST` for an admitted member; test PUT/PATCH/DELETE and unchanged stored hash. Anonymous/inactive/service-account behavior stays under the existing active-human guard. The route remains a browser form only.
3. Repair the bearer-only direct-request test to use the actual `bearer_token` string from issuance. With no session, a valid bearer-only GET and POST still redirect to login and never mutate the password. Do not add a bearer authentication backend, scope or endpoint. Keep the bearer canary out of logs/reports/assertion diagnostics.
4. Focused tests and normal exact-head five CI jobs as metadata specifies. No form/template/docs/model/dependency change; prior local screenshots and original browser pass remain usable only because those bytes do not change. Amend PR117 description if needed, `Closes #116` remains. Freeze literal implementation SHA, publish only matching report-only child with SELF, verify remote PR/head/parent/path and signal FIFO OK; CODING never merges.

## Recovery / strongest objection

First-round report-head CI may still be pending; observe all terminal outcomes before activating this suffix. Fresh CODING context through sourced `codex.sh` and `--yolo --profile early-beta` in right pane. Preserve foreign PR113 and all existing work; no reset/clean/force or real identity/email/deployment action. Strongest objection is secret disclosure through Django's technical exception reporter despite normal page rendering; explicit POST marking plus negative evidence resolves it. No CRITICAL entry for this routine correction.

## Deferred human adjudication
- Decision: NONE
