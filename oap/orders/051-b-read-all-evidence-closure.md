<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "051-b",
  "objective": 51,
  "round": "b",
  "slug": "read-all-evidence-closure",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "3461fa0106c55994a959f88450d4866b018ad890",
  "issue_number": 105,
  "branch": "codex/105-oap-051-a-read-all-bearer-authority",
  "pr_mode": "AMEND",
  "pr_number": 106,
  "previous_round": "051-a",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd",
    "PLAN.md": "2c856ae47ec985b953a8d26edbe2c07fd343833a41bc45aefcd304a7e67c1432",
    "ARCHITECTURE-for-agents.md": "41c32e0b0d6427a173dfe0b722446ae8ee311f3880929db65ed0245309b3a59e",
    "src/slaif_reservation/config/abuse.py": "64f6cfa7415264f38d0f280d020d5b32ce210d03fac92eea8826e0ba354f009e",
    "src/slaif_reservation/api/read_all_views.py": "790bfe8eddb72ea320720c0dfdd7aa5a584e050dfdc9703d60b925bb66ef3cc4",
    "tests/test_read_all_api.py": "ddca4636a2086cd5b0343ac9ed94c5ae5168fbb13cab709558f59f82ff8ac5b5",
    "tests/browser/test_token_scope_authority_browser.py": "89f3cdb1a6a53a49f21e5bbb057dd9f5ef957d0ab7e465bf9e3756cbddc7c121",
    "docs/api-contract.md": "889daa3af03f4f14eebae935856931a17a3be1c803d757676cf7a6070c0744c2",
    "docs/security-model.md": "b0b5594722d8bcd65e9a4a8045eee95923b1924446441d83a050c559d472ca89"
  },
  "requirements": [
    "SAR-001",
    "SAR-005",
    "SAR-006",
    "SAR-009",
    "SAR-010",
    "SAR-011",
    "SAR-012",
    "SAR-014",
    "SAR-015",
    "SAR-016",
    "SAR-017",
    "SAR-018",
    "SAR-019",
    "SAR-021",
    "SAR-026",
    "SAR-033",
    "SAR-043",
    "SAR-044",
    "SAR-048",
    "SAR-049",
    "SAR-050",
    "SAR-051",
    "SAR-052",
    "SAR-053"
  ],
  "allowed_paths": [
    "src/slaif_reservation/config/abuse.py",
    "tests/test_read_all_api.py",
    "tests/browser/test_token_scope_authority_browser.py",
    "docs/api-contract.md",
    "docs/security-model.md",
    "oap/active",
    "oap/orders/051-b-read-all-evidence-closure.md",
    "oap/reports/051-b-read-all-evidence-closure.md"
  ],
  "forbidden_resources": [
    "User/Asset/Reservation/ApiToken models/migrations/schema/constraint/units/lifecycle/policy/exclusivity/bookingeligibility/audit/idempotency storage or replay changes; no existing token scope backfill/mutation, no scopeauthority in modelclean/normalizer/genericownerlock/revoke/last-use.",
    "Existingowner API contracts/scopes/queryownership/mutations, human login/StaffAdmin/privateAssetAPI exposure/authentication/abuse/proxy/runtime/deps/Compose/securitysettings changes. settings/base.py allowed ONLY SPECTACULAR_SETTINGS.DESCRIPTION documentation literal if updated.",
    "No management feature/groupownership/projects/policyDSL/userdirectory/enforcement/PAM/SSH/accountsync/jobs/execution/notifications/monitoring; no API token lifecycle endpoints.",
    "ARCHITECTURE/PLAN/projection/law/OAPhelpers/tests/history/CRITICAL unchanged; no unrelatedrefactor, globalfixtures/defaultgrants. No privateuserdata/exports/credentials/hosts/DNS/TLS/firewall/exposure/deployment/foreigncleanup/merge/automerge/delegation."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Selected human authorization request, sections 6/8/9/11 and latest Concentrated OAP/coding selection",
      "section_or_evidence": "Authorized read-only global bearer data must preserve current permissions, private fields, real lifecycle semantics and security controls; meaningful evidence and docs required."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE.md A-16 / SAR-051, SAR-053; 051-a criteria 1,3,6,8,9",
      "section_or_evidence": "Dual authority, minimal effective interval, no-store errors, actual service-produced lifecycle proof, actually viewed safe screenshots, current contract docs."
    },
    {
      "marker": "E",
      "source": "Private 051-a strategic review at implementation 52045f887a2a5994a9b1d9f757cf8be1d2b32683 / report 6050a00c5057db63fc9e99e858092687f809738b",
      "section_or_evidence": "Root real PG/HTTP probes: real service release/cancel privacy/inactive-history and live group revocation pass; early IP budget 503 returns only Cache-Control:no-store and lacks Vary:Authorization. New 051-a lifecycle test uses direct ORM construction, contrary to its ordered real-service evidence/report claim. Both retained screenshots crop out the new read_all checkbox. Current API/security prose retains false group/throttle-deferred statements."
    },
    {
      "marker": "I",
      "source": "config/abuse.py AbuseControlMiddleware and tests/test_read_all_api.py test_blocking_interval_semantics_per_status",
      "section_or_evidence": "Middleware returns before view.finalize_response. Existing no-store is safe but does not meet the published new route header contract. Narrow response-header-only adjustment; no limiter/proxy/auth behavior changes."
    },
    {
      "marker": "C",
      "source": "Frozen PR106 / objective051, one corrective round",
      "section_or_evidence": "Finish published acceptance with one bounded cache-header correction plus required durable tests/docs/screens; preserve all reviewed source implementation otherwise."
    }
  ],
  "decision_class": "D0",
  "target_gate": "M-GROUP-AUTHORIZATION explicitreadonlybearer slice; integratedqualification/freshindependentICA follows; no release/deployment",
  "expected_report_path": "oap/reports/051-b-read-all-evidence-closure.md",
  "tests": [
    "Focused read-all API and unchanged shared-abuse tests; real create/release/cancel services and half-open effective interval boundary + private canaries in list/detail/errors; live group-permission and inactive history coverage.",
    "Early IP 429/503 and in-view errors for new list/detail have private,no-store + Vary Authorization; existing owner API/login denial headers/status/Retry-After unchanged.",
    "Only two affected Chromium form cases rerun for full/targeted safe screenshots showing the actual read_all choice/effect at default1440/custom390; inspect both and retain before pytest output cleanup.",
    "Canonical Ruff/types/check/no-migrations/OpenAPI validate--fail-on-warn/changed links+anchors/scope; full normal five CI checks at final implementation and report heads. No unrelated local full/rehearsal/operational/HTTPS/Gunicorn/restore runs."
  ]
}
-->

# 051-b — complete read-all evidence and response contract

## Goal

Finish the already implemented PR #106; do not restart 051-a or create a new PR. Start from frozen report `6050a00c5057db63fc9e99e858092687f809738b` (implementation `52045f887a2a5994a9b1d9f757cf8be1d2b32683`); original main base is unchanged. The whole implementation has been strategically reviewed. This is one consolidated correction, not a new feature.

## Scope / non-goals

Only the listed paths. Preserve all other reviewed product files and existing tests, especially reservation services/models, issuer/DTO/filters, owner-only interfaces, asset ACL, dependencies, authentication/proxy/DB topology, old reports/orders and BA26 fix. No feature redesign, new generic cache framework, optional refinements or local full qualification. Read current coding law/projection/communication, this order, the affected code/tests/docs and prior 051-a report evidence as needed; no full strategic book.

## Numbered acceptance

1. **Early abuse responses meet the already published contract.** Root reproduced `GET /api/v1/all-reservations/` with security budget unavailable: HTTP503, safe problem+correlation, but only `Cache-Control: no-store` and no Authorization Vary because `AbuseControlMiddleware` returns before the new view. Make the smallest response-header-only change for the `/api/v1/all-reservations/` route family so early IP 429/503 also have `Cache-Control: private, no-store` and a Vary containing Authorization. Keep status/body/Retry-After/limit keys/rates/DB locking/error privacy and every old route's behavior unchanged. Do not move or weaken abuse/authentication. Add meaningful tests of early 429 and 503 for list and valid-UUID detail, plus unchanged old owner/login denial headers. Existing in-view 401/403/404/405 and token-budget failures remain safe.
2. **Durable real-service lifecycle/negative evidence.** `test_blocking_interval_semantics_per_status` currently constructs all records with ORM, although 051-a criterion6/report claim real service-produced bookings. Replace/extend the focused tests using actual `create_reservation`, `release_reservation`, `cancel_reservation` with valid policy/grants and controlled aware instants. Prove original end survives release, consumed prefix/effective end and half-open overlap boundaries, cancelled null/nonblocking, history predating query from included when still overlaps. Confirm old history remains visible after asset inactive/account inactive. Do not invent impossible future-released rows as the main lifecycle proof or weaken domain validation. Include exact payload allowlists/canaries for BOTH list and detail and safe denial/error responses (populate purpose, cancellation reason, physical locator/location, email/name/private metadata, not just search absent field names). Include current group permission removal with SAME valid token and another additive grant retained, using existing helper behavior unchanged. Reuse fixtures only locally; no broad test refactor. Record explicitly that 051-a's real-service test claim was inaccurate and is superseded by this actual evidence; never edit immutable report.
3. **Current docs say what is implemented.** In `docs/security-model.md` replace the now-false section9 paragraph saying every human can book and groups only grant Administration: active-human Book permission + exact-asset group eligibility, owner history/lifecycle retained, explicit management capabilities, read-all dual gate/minimal data, projects/per-token asset scopes deferred. In `docs/api-contract.md`, remove false header/deferred claims that API abuse control and group/resource booking authorization are absent; describe existing shared abuse controls/link and current exact-asset booking boundary without changing the contract. Clarify external identifier null means the consumer cannot infer a machine identity; UUID is only an explicit external mapping key, not automatic Linux UID fallback. Describe read-only HTTP methods accurately (no POST/PUT/PATCH/DELETE; standard safe HEAD/OPTIONS may exist). Do not reintroduce product ledger/history prose or rewrite historical evidence.
4. **Actually view the changed UI control.** The two 051-a retained PNGs show only upper form; neither reaches the new read_all checkbox. Adjust only the two screenshot calls/capture framing to show the actual read_all choice with its human label/effect and surrounding form at default1440/custom390 (full_page=True or bounded fieldset capture is fine). No UI redesign. Rerun these two relevant Chromium tests, actually view and retain MAX TWO safe FORM screenshots, no plaintext token/password/header/CSRF/trace. Ensure fresh final source state and no overflow; no additional whole browser run.
5. **Exact evidence and frozen publication.** Focused tests during edits only. Run relevant static/schema/link checks and all five normal CI jobs at final implementation; publish a report-only commit with that literal first parent, then verify remote PR/head/report-only paths before one OK response. Report all failed attempts honestly, distinguish implementation CI from report-head CI not yet observed. Preserve `Closes #105` and PR106. Do not merge/self-approve/auto-merge. If code outside the explicit allowance is genuinely necessary, report the reproducible boundary instead of editing it.

## Verification / negative paths

Use existing owned disposable PG17/Chromium at `~/codex-work/slaif-auth-048-922064` with verified CID/loopback ownership, existing known-owned runners and exact canonical-source parity. No valuable checkout env or real data. Existing root probes live privately; the cache mismatch was reproduced after correcting a private fixture's missing reservable flag (that setup error is not a product defect). Focus on cases above; do not rerun unrelated operational or deployment qualification. Final full checks run once via normal CI, repeat only for relevant correction/failure.

## Documentation / reporting

One COMPLETE/PARTIAL/BLOCKED/FAILED immutable report. Include criterion-by-criterion short evidence, actual commands/results, honest failures, exact changed files, two image paths/capture timing/viewing claim, strongest reason against merge and limits. FULL `OAP-META` JSON is mandatory: schema_version=1, kind=report, id=051-b, exact order_path + SHA256, repo, issue_number=105, pr_number=106, branch, literal implementation_head, base_sha, result, observed_implementation_ci exact observed head/jobs/runs, report_head_ci honest observation. Verify all fields/digest privately before commit; the remote structural verifier alone does not validate them. State implementation-head SHA and publication SELF, commit ONLY the report after final code head. No further mutation after publication.

## Recovery

Fresh coding context for 051-b in right pane through existing qualified wrapper (source supervision codex.sh from dev cwd, --yolo, isolated coding home). Existing 051-a is frozen and must never rerun. On interruption reconcile this same branch/PR/pointer and current implementation, never reset/clean foreign state or invent another round. No old report rewrite.

## Decision / strongest objection

D0. Strongest reason not to change shared middleware is disturbing established global abuse controls for a header-only discrepancy. Mitigate by changing only the new route family's response headers and pinning old route responses; no budget/auth changes. The original `no-store` did not leak private data; this repairs the explicit new response contract and truthful documentation/evidence.

## Deferred human adjudication
- Decision: NONE
