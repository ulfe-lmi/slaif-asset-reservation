<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "053-b",
  "objective": 53,
  "round": "b",
  "slug": "authorization-documentation-truth",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "bddda89a5ddb428c64a36c7c2bd1f35cab2acbba",
  "issue_number": 109,
  "branch": "codex/109-oap-053-a-authorization-audit-publication",
  "pr_mode": "AMEND",
  "pr_number": 110,
  "previous_round": "053-a",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd",
    "PLAN.md": "8298ef941d02b05c304c48b46734ad678aff80b9ab4e62ca0814b6f03007277f",
    "ARCHITECTURE-for-agents.md": "41c32e0b0d6427a173dfe0b722446ae8ee311f3880929db65ed0245309b3a59e",
    "README.md": "e920cb6d6c403686982cd8aeeb1a60520063257d6922bbb85d998038b82f458a",
    "docs/README.md": "b6dc3d5e49d596e9dfc82c0aa33bae742d778e17329bed96eec1762b57ce0e16",
    "docs/authorization.md": "9bfabad093241dde818d0b6e721b1dc210e605c5a23dda8ccfe61fe13e4a52de",
    "docs/api-contract.md": "30a8dd76f17b44b7f555dd7c14c0dd7b1188e025b441b061cf6cc22913fc9337",
    "docs/security-model.md": "ca109b90e2cb52e45ae04c6f38982d50030c72f841185337d90a408ecabdaba0",
    "docs/audit/qualification/M-GROUP-AUTHORIZATION-FRESHNESS.md": "147fd2e1a855d5cb6fcf1c702ca65c6ba868c27d54456a72595c17432e0755fe",
    "src/slaif_reservation/reservations/admin.py": "5a8116fb110fa4f0e31bcaf0030c721f3fb87d888887ed4f36c4719d4046aac9",
    "src/slaif_reservation/api/reservation_views.py": "ae3d3d5c6ba3386bec723f6b24cd3b09aca35291dfd33c1a1ba86d19af30a33e"
  },
  "requirements": [
    "SAR-012",
    "SAR-013",
    "SAR-014",
    "SAR-016",
    "SAR-021",
    "SAR-026",
    "SAR-032",
    "SAR-033",
    "SAR-036",
    "SAR-037",
    "SAR-038",
    "SAR-048",
    "SAR-050",
    "SAR-051",
    "SAR-053"
  ],
  "allowed_paths": [
    "docs/authorization.md",
    "docs/api-contract.md",
    "docs/security-model.md",
    "docs/audit/qualification/M-GROUP-AUTHORIZATION-FRESHNESS.md",
    "oap/active",
    "oap/orders/053-b-authorization-documentation-truth.md",
    "oap/reports/053-b-authorization-documentation-truth.md"
  ],
  "forbidden_resources": [
    "No application/source, tests, models, migrations, settings, API/runtime/permission/auth behavior, dependencies/lock, Dockerfile/Compose/deploy/workflows, assets/data, proxies or environment changes.",
    "README, PLAN, docs/README, both immutable ICA report files, architecture/projection/law/CRITICAL/OAP helpers/old orders/reports byte-identical; no optional visibility history rewrite beyond correcting actual authority chronology within listed freshness paragraph.",
    "No release/deployment/exposure, real identities/secrets/private/lab data/DNS/TLS/firewall/Neumann/SmartScheduling, GitHub visibility/protection changes, foreign cleanup/reset/forcepush, coding merge/self-approval.",
    "No local whole tests/browser/OAP/operational/rehearsal/HTTPS/Gunicorn/restore sweep. Documentation edits only, source-neutrality binding and normal five exact-head CI."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human authorization extension sections2/3/5/6/9/10/11; earlier human product-first documentation truth requirement; later direct confirmation of PUBLIC repository development merges",
      "section_or_evidence": "Existing Administration model permissions and audit rights are separate from new application read-all; normal operator/API docs must explain current authority without false exclusivity or work-order ledger. The PUBLIC development confirmation came later than original authorization selection; real deployment remains D2."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE.md A-16 and SAR012/013/016/021/036/037/048/050/051/053; current full53 ICA at bddda89 and ICA-PROTOCOL.md",
      "section_or_evidence": "Selected All reservations browser and read-all bearer are separate owner-broadening application interfaces, while existing Staff Admin model View and audit history remain independently permissioned. Documentation-only clarification of already-audited behavior does not alter source, product scope or normative deployment assumption."
    },
    {
      "marker": "E",
      "source": "Strategic exact frozen053-a implementation/report review a06ff983.../1af3927..., direct source plus private realPG probe and current human PUBLIC scope text",
      "section_or_evidence": "Current docs/security-model.md says exactly two authorized cross-user read surfaces and no other route/capability discloses another owner. Independent synthetic PG: Staff+reservations.view_reservation, no view_all_reservations, /manage/reservations/403 but DjangoAdmin Reservation list/detail200 with other owner email. docs/authorization still falsely says Staff onlyadmitsAdmin at two locations. src/api/reservation_views.py MeAPIView.required_scopes=() disproves blanket scope claim; docs/api-contract retains WorkOrder0007 ledger; freshness conflates later PUBLIC confirmation with original feature request. First screen docs/authorization markets audit counts/history instead of permissions."
    },
    {
      "marker": "I",
      "source": "Root whole 053-a docs/freshness review once and originalICA/strictsource checks; prior report-only publication remote verified",
      "section_or_evidence": "All errors are operator/client prose, not authorization implementation. Correct four listed documents in ONE same-PR correction, keep rootREADME/PLAN/ICA reports/runtime bytes identical; make exact freshnesstext chronology truthful. No independent re-audit required for non-normative clarified prose, but exact source-neutrality/five CI gates remain."
    },
    {
      "marker": "C",
      "source": "Prior 053-a immutable report at 1af3927c81ab21a7c574bcd95781ee919046cf23, PR110/issue109 open, audited merged base bddda89a5ddb428c64a36c7c2bd1f35cab2acbba",
      "section_or_evidence": "One proof-sized documentation-truth correction suffix b on SAME branch/PR; no new feature/objective, D0/DHA NONE, all four findings gathered before activation. Strongest risk is falsely narrowing existing Admin/audit visibility or presenting ICA as product marketing; preserve separate permissions and move audit evidence to specialist endnote."
    }
  ],
  "decision_class": "D0",
  "target_gate": "M-GROUP-AUTHORIZATION current privacy/authority documentation correction; independent full53 ICA and source-freshness publication remain docs-only, human milestone/release separate",
  "expected_report_path": "oap/reports/053-b-authorization-documentation-truth.md",
  "tests": [
    "Check docs/security-model privacy paragraph names the selected All reservations browser and separate dual-gated bearer interface without falsely excluding independently permissioned Administration Reservation model View or audit history/export. Member and owner API remain owner-scoped; no new authority or disclosure.",
    "Check docs/authorization both stale Staff-only-Admin sentences repaired, existing10capabilities/matrix/groups/upgrade/asset eligibility unchanged, first screen user-oriented rather than audit-count ledger; current ICA link moved/preserved under specialist endnote.",
    "Check docs/api-contract GET /me actual required_scopes=() bearer auth semantics and replace Work Order0007 blackout_conflict historical lead-in with current error behavior, while all API endpoints/scopes/representations remain unchanged. docs/security-model bearer scope claim truthfully distinguishes action-specific scopes.",
    "Check freshness public-repository development authority chronology: original human feature selection versus later separate explicit confirmation after GitHub became PUBLIC; no fake human disposition or application exposure permission.",
    "Changed Markdown links/anchors and documentation ledger regression, audit report SHA574024.../old failedSHA7b030... unchanged; source/ARCH/PLAN/projection/README/index/Docker COPY inputs/deps/tests/workflows byte-identical from audited bddda base through final implementation, same prior runtime evidence only where source identity permits; no local whole suite.",
    "Normal five CI jobs at final corrective implementation AND immutable report heads; earlier 053-a report-head CI must be observed honestly (if pending, wait outside model; no waiver), exact PR/head/report-only firstparent verification, no merge by coder."
  ]
}
-->

# 053-b — correct current authorization documentation before acceptance

## Goal / exact boundary

Same issue109/PR110/branch as frozen 053-a, one consolidated documentation-truth correction. STRATEGY reviewed every changed Markdown path and source-freshness record at exact implementation `a06ff983c4bf1264f20ef53be788051624cf236e`; prior immutable report `1af3927c81ab21a7c574bcd95781ee919046cf23` is remote verified/report-only first parent. The fresh independent ICA source/audit bytes are sound. Four concrete operator/API/privacy wording problems remain. Finish only these under this AMEND round. Never rewrite the prior order/report, audited report, root README, PLAN or application source. The original 053-a report-head CI is a historical fact, not automatically accepted; record its actual outcome before final acceptance. No new issue or PR.

## Compact reads / scope

Normal coding law/projection/communication/cores; this short order; ONLY the relevant `docs/authorization.md` header + both Staff-status passages + bottom; `docs/security-model.md` bearer/admission + cross-user paragraph; `docs/api-contract.md` scope usage, problem-details and /me; `docs/audit/qualification/M-GROUP-AUTHORIZATION-FRESHNESS.md` authority paragraph. Bounded source references: `src/slaif_reservation/reservations/admin.py` read-only ReservationAdmin with independent model View; `src/slaif_reservation/api/reservation_views.py:MeAPIView.required_scopes`; `src/slaif_reservation/config/urls.py` private docs predicate; existing audit/export operator grant docs. The prior full53 ICA is read-only exact evidence, not a new audit queue or needed full context. Only allowed paths in metadata.

## Numbered acceptance / negative paths

1. **Security/privacy wording matches ALL existing authorized readers.** Current `docs/security-model.md` says the authorized cross-user read surfaces are 'exactly two' and 'No other route, scope or capability discloses another owner’s reservations.' Both are false as written: an active human Staff account with ONLY `reservations.view_reservation` Administration model permission (no `reservations.view_all_reservations`) can inspect another owner's booking in read-only Administration; independent private PG probe showed Admin list/detail200 and /manage/reservations/403. Audit browsing/export also has independent explicit grants. Keep the two SELECTED application read-all interfaces clear: All reservations browser requires current view-all capability; new bearer list/detail requires its own read_all scope AND current owner view-all, with minimal payload. State that existing Administration model View and audit history/export are separately authorized and may disclose reservation records/evidence to their authorized principals, without granting the application read-all interface. Ordinary member pages and old owner-only bearer routes remain private. Do not assert there is no other route/permission. No code/permission/source change or user-directory API.
2. **Operator grant guide is accurate and product-oriented.** `docs/authorization.md` still says at two places (`is_staff` only admits `/admin/` around its Available now area, and 'staff flag is required only for /admin/ admission' in grant setup) that Staff is ONLY used for Administration. Correct BOTH: current active non-service-account human Staff is also required for the pre-existing session-only asset list/detail API and, when enabled in private mode, schema/docs; Staff alone grants no /manage/, Book or application read-all; Administration record viewing still additionally needs per-model permission. Keep ten-capability matrix, example group setup, upgrade procedure, asset ACL and bearer contract intact. Its FIRST SCREEN should explain the implemented permissions to an operator in plain product language rather than lead with exact commit SHA/53-row audit counts. Keep the current qualification report+freshness links and human milestone caveat under a short specialist evidence note near the end (after the functional guide). Do not remove selected scope/history from canonical PLAN (forbidden here).
3. **API client contract loses the last ledger phrases and names scope exception.** `docs/api-contract.md` still says 'Work Order 0007 adds blackout_conflict' in the normal problem-details section. Replace with current endpoint behavior (an overlapping active blackout returns that machine error). Its header should describe the implemented controlled authenticated pilot, not development status chronology. `GET /api/v1/me/` requires a valid bearer but its `MeAPIView.required_scopes=()` has NO additional action scope; state that clearly without implying anonymous access. In `docs/security-model.md` replace its inherited blanket 'Every bearer endpoint checks explicit scopes' claim with the actual per-operation scope rule and /me identity exception; read_all still has both gates. Retain exact wire names/errors and no token-secret disclosure. No endpoint/schema/auth behavior change.
4. **Authority chronology in freshness is truthful.** The final freshness record currently says the original feature authorization extension 'explicitly authorized public-repository development publication/merges.' That conflates two decisions. The human selected M-GROUP-AUTHORIZATION first; AFTER GitHub was independently found PUBLIC, the human separately and explicitly confirmed continued development publication and merges there. Edit only this factual provenance wording; reaffirm no repo-visibility change by agents and no real application exposure/deployment authorization. All audited-base/source-byte-identity/normative-deployment assessments stay intact. No optional ICA-GA-O1 architecture/private-history rewrite.
5. **Prove bounded correction and publish.** Four doc paths only, plus this immutable order/pointer and last report. Audit report at `docs/audit/reports/M-GROUP-AUTHORIZATION-bddda89.md` SHA256 `574024e2511af121f4665a89fa53cdfd0eefb12c816e82697ed2b9f724cd4177` and prior failed reportSHA `7b03025c4a4f2757b5a0d2e252878ed5f236594bdc2953e2bb57dd40a28c43f1` must remain byte-identical. Root README, PLAN, docs index, ARCHITECTURE/projection, product source, settings, tests, migrations, lockfile, Docker/Compose/deploy/workflows unchanged. Verify changed Markdown local paths/anchors and first-screen normal-operator tone, link from authguide to specialist ICA. Reassess source-neutrality: these revisions clarify already-implemented permissions and chronology only, not selected meaning or normative deployment assumptions; reuse prior independent/runtime evidence only with actual byte identity/current5CI. Focused doc/static checks locally; no full local product/browser/OAP/operational/deployment/restore sweeps. Normal all five CI checks at final corrective implementation and report heads, no missing/pending/cancelled/skipped pass. PR #110 description reflects final doc-only change and keeps `Closes #109`; no merge/self-approval/auto-merge.

## Strongest objection / recovery

Overstating cross-user privacy can lead operators to assign Administration/Audit grants believing only the read-all capability reveals another owner's bookings. Correct that precise documented boundary while keeping enforced code and existing independent grants unchanged. The separate publication authority chronology matters because this public repository was not part of the original private-repository assumption; current human confirmation is attributable in this session, not a fabricated original condition or deployment grant. D0, DHA NONE, no CRITICAL append. Existing OAP state and branch must be reconciled on restart; fresh CODING context in right pane via qualified wrapper sources `~/codex-supervision/slaif-asset-reservation/codex.sh` while in dev cwd BEFORE `codex --yolo`, same isolated coding home. Do not reset/clean/replay earlier order, copy secrets or touch owned auditor worktree/PG resources. Same PR, corrective suffix b, next report-only commit after final code/head CI.

## Reporting / publication

Short criterion-by-criterion evidence, literal final implementation SHA/SELF, actual doc paths/links/privacy canaries, audit hashes/source-neutrality, honest prior and new CI states, remaining human D2/milestone gate. FULL OAP-META JSON: kind report/id053-b/order_path+SHA256/repo/issue109/PR110/branch/implementation_head/base_sha/result/observed_implementation_ci exact observedhead/jobs/runs/report_head_ci truthful. Validate metadata/digests BEFORE report commit; push report-only with implementation first parent; verify actual remote PR/head/report/path before one FIFO OK; no mutation after publication. STRATEGY alone performs exact-head review/merge. No future SHA invented.

## Deferred human adjudication
- Decision: NONE
