<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "052-a",
  "objective": 52,
  "round": "a",
  "slug": "staff-read-human-boundary",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "1adf776e553bcd56cd0a7fa229c8eb0bcb56c1fe",
  "issue_number": 107,
  "branch": "codex/107-oap-052-a-staff-read-human-boundary",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd",
    "PLAN.md": "2c856ae47ec985b953a8d26edbe2c07fd343833a41bc45aefcd304a7e67c1432",
    "ARCHITECTURE-for-agents.md": "41c32e0b0d6427a173dfe0b722446ae8ee311f3880929db65ed0245309b3a59e",
    "src/slaif_reservation/api/permissions.py": "2083958d1288d9c3c7b0a3ec144ebd64bcc86044adb8e2ba0bc9e5cbff05da52",
    "src/slaif_reservation/assets/api.py": "685a8973554923f7932b42107dbf3a952b690924b12d2bec47f0f734d4129b4f",
    "src/slaif_reservation/config/urls.py": "7c0dc3a6c93172f143c6be3bd53345e2f5111f79ca0773d42bc10f1082054f76",
    "src/slaif_reservation/web/auth.py": "df54dbf890ff9963c66dafc2df5bbb4e0d5351191cd014c304037a6f29def529",
    "src/slaif_reservation/config/admin_site.py": "8076e2c1de3107ce4f30a7d2dc7b35731cdff375f59e12185be34034ea921a5f",
    "tests/test_api_schema.py": "3d5395e4498427be2e9e3592115cb80194b982ca933a81e6d5f40a021d402ea9",
    "tests/test_assets_web_api.py": "3552f6c06be29518975646a6877b582358c5fbe01f4d86ec550ceabaf78a00eb"
  },
  "requirements": [
    "SAR-011",
    "SAR-014",
    "SAR-016",
    "SAR-017",
    "SAR-023",
    "SAR-026",
    "SAR-033",
    "SAR-037",
    "SAR-038",
    "SAR-039",
    "SAR-048",
    "SAR-051",
    "SAR-053"
  ],
  "allowed_paths": [
    "src/slaif_reservation/api/permissions.py",
    "src/slaif_reservation/assets/api.py",
    "src/slaif_reservation/config/urls.py",
    "tests/test_staff_read_eligibility.py",
    "PLAN.md",
    "docs/audit/reports/M-GROUP-AUTHORIZATION-1adf776.md",
    "oap/active",
    "oap/orders/052-a-staff-read-human-boundary.md",
    "oap/reports/052-a-staff-read-human-boundary.md"
  ],
  "forbidden_resources": [
    "Reservation/account/asset/token models, migrations, database schema/constraints, booking/policy/lifecycle/audit/idempotency/issuer/authentication/proxy/abuse implementation, dependencies, Compose/runtime/security settings and private-data/production resources.",
    "All other source/test files, global fixtures/autogrants, ARCHITECTURE/projection/role law/CRITICAL/OAP helpers/history. No new scopes/model permissions or inventory bearer access.",
    "No exposure/visibility/DNS/TLS/firewall/identity/secret changes or deployment, real data/hosts/lab/Neumann/private exports; no unrelated cleanup or optional audit refinements. Human PUBLIC development publication and conditional strategic merge authority is active; coding never merges or self-approves.",
    "No whole local pytest/browser/OAP/deployment/operational/rehearsal/HTTPS/Gunicorn/restore sweeps. No valuable-checkout product tests/env repair, foreign cleanup/reset/clean/forcepush or delegation."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human authorization request sections2/3/6/9/10/11; explicit Concentrated OAP/coding selection; current public-development confirmation",
      "section_or_evidence": "Preserve current active-human/service-account restrictions across member/management/Administration/API; documented deliberate upgrades; meaningful direct endpoint negative evidence. No new feature meaning or deployment."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE.md A-16; stable SAR016/037/039/048/053; docs/audit/ICA-PROTOCOL.md",
      "section_or_evidence": "All privileged application access requires current active non-service human; legacy inventory remains staff-session only and private docs retain configured policy; canonical PLAN cannot contradict delivered source; independent closure must repeat full architecture-to-new-main after remediation."
    },
    {
      "marker": "E",
      "source": "Fresh independent ICA at 1adf776e553bcd56cd0a7fa229c8eb0bcb56c1fe, /root/group_authorization_ica; frozen REPORT SHA2567b03025c4a4f2757b5a0d2e252878ed5f236594bdc2953e2bb57dd40a28c43f1",
      "section_or_evidence": "Full53:48IMPLEMENTED/5PARTIAL, required ICA-GA-001 and002. Real CSRF-backed staff human login, same cookie after is_service_account=True, four staff inventory/private-doc routes return200; Admin correctlyredirectslogin, Basic unauthenticated403. PLAN P08 says none of delivered features exists. Main5CIgreen/1243tests doesnotcovermissingnegative."
    },
    {
      "marker": "I",
      "source": "Root read full frozen report/matrix, actual private repro source+failure log, assets/api.py/config/urls.py/api/permissions.py/web/auth.py/admin_site.py and current PLAN",
      "section_or_evidence": "Failure is admission BEFORE inventory/schema response. Existing is_active_human predicate is in web/auth.py and already used by AdminSite. Use tiny shared DRF active-human+staff permission; no service/model changes below boundary. PLAN status-only correction changes no selected requirement and doesnot require architecture/projection edits."
    },
    {
      "marker": "C",
      "source": "Verified PR106 merged 1adf776e553bcd56cd0a7fa229c8eb0bcb56c1fe, issue105closed, currentmainall5SUCCESS, actual issue107",
      "section_or_evidence": "One small audited-boundary repair and its canonical evidence/status reconciliation. Fresh coding context; frozen failed audit is copied byte-identically, never rewritten; independent full53 re-audit after merge. D0/DHA_NONE; optionalO1 is recorded separately, not ordered."
    }
  ],
  "decision_class": "D0",
  "target_gate": "M-GROUP-AUTHORIZATION ICA-GA-001/002 remediation; full architecture-to-new-main independent re-audit required after merge; no release/deployment",
  "expected_report_path": "oap/reports/052-a-staff-read-human-boundary.md",
  "tests": [
    "Real owned PG/HTTP: establish valid CSRF-backed human staff login (not force_login), positive200 on all four protected routes, change account flags while keeping same session, service/inactive/staff-loss denial before private list/detail/schema/docs. Exercise REST gates BEFORE any member/Admin endpoint that logs an invalid session out.",
    "Positive active-human Staff and human Super; negative nonstaff even unrelated model/all reservations permissions, anonymous, service including Super, inactive, token-only Staff bearer; no inventory/schema leakage and same403 for missing detail UUID. Preserve explicit local API_DOCS_PUBLIC=True anonymous policy and production docs-disable source behavior.",
    "Focused newtest + existing asset/API schema/product-entry/current bearer boundary suites, canonical Ruff/types/check/no-migrations/OpenAPI validate--fail-on-warn, changed links+anchors/auditbytehash/scope. Normal full five CI jobs at final implementation and report heads. No unrelated local full or bespoke qualification.",
    "PLAN current delivered/pending-ICA status preserves original selection/scope map/deferrals/all53/human gates; original failed audit copied exactapprovedSHA with all negative/interrupted evidence intact. No architecture/projection semantic change."
  ]
}
-->

# 052-a — close current-human admission at the four staff read surfaces

## Goal / current truth

Repair the exact permission-admission defect ICA-GA-001 and its current canonical-status/evidence reconciliation ICA-GA-002. This is the next bounded purpose after accepted PR106, not a restart or rewrite of 051. Actual issue107, new branch/base in metadata, no open PR observed at selection. Current main and all five checks are green; the new independent real negative demonstrates missing coverage despite that result. No milestone closure is claimed.

## Compact read set

Normal coding law/projection/communication/cores; THIS order; current three affected adapter modules; `web/auth.py:is_active_human` and AdminSite predicate as bounded references; existing API schema/assets test patterns; PLAN P08 ONLY. For the frozen ICA read identity/provenance + ICA-GA-001/002 excerpt (report lines35–63), not the whole strategic read set/full53 matrix. The original report is already strategically reviewed and privacy-safe for exact publication. No new whole architecture/PLAN book is required for coding.

## Numbered acceptance

1. **One current-human+staff permission.** In api/permissions.py add a small DRF permission using the EXISTING `web.auth.is_active_human` predicate and `user.is_staff`. It must require authenticated CURRENT active non-service human AND staff; no hardcoded group/model permissions, grant checks, superuser bypass of service/inactive/Staff status, user caching or authentication backend changes. Use it for BOTH existing staff asset inventory API classes and the PRIVATE branch of ApiDocumentationPermission. Keep token scope permission implementation unchanged. Do not move/refactor the shared human helper; it already works for Administration. Reject before inventory/query/filter/detail/schema work through normal DRF permission admission.
2. **Preserve existing contracts.** Four affected GET routes are `/api/v1/assets/`, `/api/v1/assets/<uuid>/`, `/api/schema/` and `/api/docs/` with API_DOCS_PUBLIC=False. Denials remain existing REST403 behavior with no private body. Active human Staff (including trusted active human Staff superuser) retains old read behavior; unrelated model or reservations permissions without Staff do not confer this admission. Inventory stays SESSION-only: a bearer token alone, even belonging to staff/superuser with assets/read_all scopes, never grants discovery. Do not add bearer auth classes, change schema fields/routes/filters or widen any owner/member/read_all interface. Preserve API_DOCS_ENABLED conditional route registration/default production absence; preserve deliberate local API_DOCS_PUBLIC=True public metadata behavior without a new policy. Admin/member/management behavior remains unchanged (their current-human checks already work).
3. **Durable meaningful regressions.** Add `tests/test_staff_read_eligibility.py` focused on these actual boundaries. At least one real HTTP/live_server scenario must log in an active staff human through actual `/login/` with valid CSRF, assert all four are200, retain SAME session/cookies, change only account service flag, then assert all four403 and no asset/schema private data. Do NOT force_login the main transition proof, start as service account with failed login, or call a member/Admin page that clears the session BEFORE testing the four REST routes: those would mask the defect. Include service-account-superuser, inactive and Staff removal transitions/controls, active human Staff/Super positives, anonymous and nonstaff-with-unrelated-grants negatives, bearer-only inventory/private-doc denial. A guessed UUID for a disallowed caller must not distinguish existence. Preserve explicit local public-doc positive and existing Admin/member/management guard controls. Keep test users synthetic and token scopes legitimately issuable; no global fixtures/autogrants. Reuse the independent probe as a design reference at `~/codex-work/slaif-auth-ica-7d85666bc6/test_ica_service_session.py`; do not modify the frozen audit copy or run tests concurrently on its DB. No database/model/service changes are needed.
4. **Canonical status and original failed audit.** Update ONLY PLAN P08 current-state wording: the original 2026-10-17 selection is historical provenance; foundation/booking/management/bearer/identifier/upgrade are delivered at actual merged evidence (PR100/102/104/106 and immutable reports/source). Retain the original purpose table as a labelled scope/history map, not nonexistent future implementation or a new replay queue. The original53-row ICA at 1adf776 is a FAILED closure (48implemented/5partial, required001/002), not a green result; this repair still needs fresh architecture-to-new-main independent assessment and human judgment. Preserve every human meaning/stableID/deferral, prior milestone history, pending human milestone/release/exposure gates. No normative architecture/projection change and no assumption a hash proves implementation. Copy the frozen `~/codex-work/slaif-auth-ica-7d85666bc6/REPORT.md` BYTE-IDENTICALLY to `docs/audit/reports/M-GROUP-AUTHORIZATION-1adf776.md`, SHA256 `7b03025c4a4f2757b5a0d2e252878ed5f236594bdc2953e2bb57dd40a28c43f1`, and link it from current P08 status. Do not alter its words/classifications/provenance/failures/limitations or commit raw private logs/probes/screens; the inline full matrix is complete and private supporting artifacts remain retained. Optional ICA-GA-O1 provenance refinements are recorded separately, NOT required or ordered here. No ARCHITECTURE/projection/law/private-authority edit or fresh ADR.
5. **Focused verification and exact report.** During edits run new boundary tests plus affected existing `test_assets_web_api.py`, `test_api_schema.py`, relevant `test_product_entry.py` current-human cases and relevant bearer permission tests, then static/type/check/no-migrations/OpenAPI--validate--fail-on-warn and changed Markdown links/anchors/diffscope/audit hash. No local whole pytest/browser/OAP/operational/rehearsal/HTTPS/Gunicorn/restore runs. No visual redesign, so no new screenshots required (MAX0). Normal full five CI checks at exact final implementation and report heads provide unchanged qualification. Fix demonstrated in-scope failures, report all failures honestly; no weakening old negative assertions or blind rerun-until-green. Create/resume one actual PR, `Closes #107`, never merge/self-approve/auto-merge.

## Scope / non-goals / strongest objection

ONLY the exact allowed paths, including new test and byte-identical failed-audit publication. No application changes below permission admission, new app capabilities/groups/ownership/identifiers/asset inventory/booking semantics, protected-record mutations, runtime/proxy/security settings, dependency/workflow changes, private data or deployment. Strongest reason not to alter these older read gates is a possible integration depending on a service-account browser session; that behavior violates the already selected active-human contract, while proper human staff sessions and explicit local public docs remain supported and pinned. This is a narrow D0 defect repair, not a new risk/product choice or CRITICAL waiver.

## Verification environment / recovery

Use the already owned execution copy `~/codex-work/slaif-auth-048-922064` (PG17 CID7680db038ecebff114a19a929c6b2e3800d7274b23254a41707c2873d7c4067d, loopback22708) after verifying receipt/CID and syncing exact canonical allowed files/order/pointer. Do not use the separately owned ICA DB or alter its frozen detached source. Existing runner/lockedPython/Chromium paths are qualified; avoid valuable development checkout .venv/env, remote Docker or source-tree cleanup. Verify current import path and parity before evidence. Full source hashes above are SHA256 bytes at BASE, not Git object IDs. Fresh coding context through existing right-pane wrapper sources supervision codex.sh from dev cwd BEFORE `codex --yolo`; no provider/profile change. On interruption reconcile THIS same objective/branch/PR and immutable order; never reset, replay051 or invent a new round. Repository PUBLIC publication/conditional strategic merge was explicitly human-confirmed; no real application exposure/release authorization followed.

## Reporting / publication

Write a short criterion/evidence report with literal full implementation SHA and publication SELF, exact paths/commands/results/failures, preserved original ICA SHA and pending full re-audit, strongest objection/limits, no private credentials or raw transcripts. FULL OAP-META JSON is mandatory: schema_version1, kind=report, id052-a, exact order_path+SHA256, repo, issue107, actual retrievedPR, branch, literal implementation_head, base_sha, result, observed_implementation_ci with exact observedhead/jobs/runIDs, report_head_ci honest observation. Privately verify all keys/hash/identity BEFORE report commit; structural remote verifier alone is insufficient. Push implementation/opencorrectPR/fixin-scopeCI, freeze literal implementationhead, then commit ONLY immutable report with that exact first parent, push and verify remote PR/head/parent/report-only paths before one FIFO OK. No source/report amendments after publication. A PARTIAL/BLOCKED/FAILED published result must remain truthful; pending/missing CI is not PASS. Strategy alone reviews/merges; independent full53 re-audit follows merged repaired source, not only findings queue.

## Deferred human adjudication
- Decision: NONE
