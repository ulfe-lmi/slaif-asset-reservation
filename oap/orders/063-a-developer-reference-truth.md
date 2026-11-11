<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "063-a",
  "objective": 63,
  "round": "a",
  "slug": "developer-reference-truth",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "287b23ba687689d9f7cb947d9a3ec8acb38ff1ab",
  "issue_number": 131,
  "branch": "codex/131-oap-063-a-developer-reference-truth",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f7b5c98876a40b052c2d2fe057e57281e917ac5a72508e98caca512c1f0d1286",
    "PLAN.md": "e95135e756f6610b78e086a0b11395a2faa4d0fc0fa3a7bed658a091101a486f",
    "CRITICAL.md": "f5c4d78ed599ac9a8ce44687925dab29f221d8b65a2350a4f858c9f32a92c672",
    "docs/audit/ICA-PROTOCOL.md": "67075c18b6102e3cbd23c5b4836ca0e004be374458dbd5e5396bbeefdeaa098f",
    "README.md": "9f535cf8326d79a59208892b98f5cce92a946d1f1a5f2eab635354204966c5c2",
    "docs/README.md": "03c9b7ce85ab5616f1b39cd52f5ba87ac820e5980aac67c443ba2bb7303b4cf6",
    "docs/domain-model.md": "bf631a5da90040aa881328c9cc5a63b7d93bef5fb62b9115cb35424cfea5bd54",
    "docs/ux/form-guidance-inventory.md": "172c495d78b83caac9aa803fe9d81f3d6d2547f0e94d656073ee22ca917a12ef",
    "docs/authorization.md": "cba3ef323d6f964d3e142060bb5a5b465c16aa4bf71eefba3131835b4563a5dd",
    "docs/human-ui.md": "a9e323cddb853262e5341392a1127e483460ffffbcac147121707b1007df9f20",
    "TESTING.md": "3fd59cf037e1428484ac2de0f236e55da909e75c0fb4a8ebf3a6c41456f66e72",
    "src/slaif_reservation/accounts/admin.py": "c225afd0692ff2eb5307085fd7c64d4052168544be5351f16ad720f450d788c4",
    "src/slaif_reservation/web/forms.py": "16539444d9aa831446846c743fd45a1a90b88bca02245f6ce7985b815b7bd616",
    "src/slaif_reservation/web/views.py": "8b2af90919b1e4e6194cabe72fc08ccd014c57a7f39319c1fca43a9ca0de4b52",
    "src/slaif_reservation/management_ui/views.py": "b9f589caf65a5edf697180d178ff314385bf1200c35ea6e72b7723917e26c81a"
  },
  "requirements": [
    "SAR-036",
    "SAR-037",
    "SAR-038",
    "SAR-044",
    "SAR-048",
    "SAR-050",
    "SAR-053",
    "SAR-054",
    "SAR-055",
    "SAR-056"
  ],
  "allowed_paths": [
    "README.md",
    "docs/README.md",
    "docs/domain-model.md",
    "docs/ux/form-guidance-inventory.md",
    "oap/active",
    "oap/orders/063-a-developer-reference-truth.md",
    "oap/reports/063-a-developer-reference-truth.md"
  ],
  "forbidden_resources": [
    "No INSTALL/QUICKSTART/SECURITY/PLAN/ARCHITECTURE/CRITICAL/projection/authorization/human-ui/TESTING/runbook changes, no application source/migrations/tests/fixtures, dependencies/lock, Docker/Compose/proxy/settings/API behavior, OAP helpers/workflows or historical audit/order/report rewrite. If a current link cannot be repaired in allowed paths, report to STRATEGIC rather than expanding scope silently.",
    "No real SMTP/recipient/credential, real identity administration, private data/production DB/host/DNS/TLS/firewall/public exposure/deployment, foreign PR113 mutation or CODING merge/automerge."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human product-first repository documentation and field-help requirements, selected group authorization and account onboarding; 2026-11-10 instruction to execute through closure",
      "section_or_evidence": "Current README/docs navigation and live form inventory must reflect implemented source without making a user learn work-order history. This is a docs-only correction, not a feature round."
    },
    {
      "marker": "A",
      "source": "Full current ARCHITECTURE.md A-05/A-06/A-16/A-17 and SAR-037/044/048/050/053/054/055/056; docs/audit/ICA-PROTOCOL.md",
      "section_or_evidence": "Architecture is canonical current data/domain authority; historical design sketches must be labeled and demoted. Current form inventory linked by TESTING.md/human-ui must describe own-password change, Admin onboarding and capability-gated management accurately. After repair, full architecture-to-current-main ICA."
    },
    {
      "marker": "E",
      "source": "Fresh independent full ICA at exact merged main 50502f2e158d64fb0f16135e0ea187fa44b82589, private report SHA256 67c2187c5b4544aea87cbf5ec48b42abf64bb516d9af1a9b2b4cf86250124ba9; PR129/062-a merged as docs-only main287b23ba687689d9f7cb947d9a3ec8acb38ff1ab",
      "section_or_evidence": "Auditor found current README:110 and docs/README:28 route readers to docs/domain-model.md, whose header calls it a design contract yet diagram proposes unimplemented PROJECT/MEMBERSHIP/AVAILABILITY_RULE and body says group restrictions/cross-user management absent/staff-only. docs/ux/form-guidance-inventory.md:101 and161-162 claims no member own-password change and staff without management grants can access /manage/, despite current source and header claiming ACTUAL runtime inventory. Current architecture/source and exact PR121/123 implement opposite. Prior ICA 52 IMPLEMENTED/4 PARTIAL, no code blocker; exact main287 CI run43011778401 and OAP run43011778468 completed five/five SUCCESS before this order was published."
    },
    {
      "marker": "I",
      "source": "Root README docs table, docs/README task index/history, docs/domain-model design sketch, current linked form inventory; read-only source verification",
      "section_or_evidence": "Add prominent historical/superseded banner to domain-model preserving old body; route current README/docs index domain model/time semantics to ARCHITECTURE A05/A06 and authorization, retain old sketch under specialist/history. Update form inventory current rows/heading/verification for member own-password fields, Admin generated six-char+SMTP/force change/reissue/activation lock, and permission-gated management; preserve earlier order provenance and actual UI behavior."
    },
    {
      "marker": "C",
      "source": "Independent ICA linked developer-reference findings; CRITICAL empty",
      "section_or_evidence": "D0/DHA NONE. Strongest objection: demoting the only domain-model page could make current model harder to find, while a rushed inventory edit could claim untested UI help. Mitigate by prominent canonical ARCHITECTURE/authorization links and source-checked targeted inventory rows; preserve old design content. No D2 crossing."
    }
  ],
  "decision_class": "D0",
  "target_gate": "One docs-only reviewed PR making current domain/UI references truthful with exact-head five CI; then fresh independent full SAR001..056 architecture-to-current-main ICA for milestone closure, no real SMTP/deployment",
  "expected_report_path": "oap/reports/063-a-developer-reference-truth.md",
  "tests": [
    "Domain-model header immediately marks the ~370-line design sketch historical/superseded, preserves its body verbatim, and links current ARCHITECTURE A05/A06/A16 and docs/authorization. Root README and docs/README current domain/time/authorization entry points no longer lead normal readers to the old sketch; docs/README retains a specialist/history link. First ~100/normal README product-first structure remains and no OAP ledger is introduced.",
    "Form-guidance inventory linked from TESTING.md/human-ui remains a current coverage map: correct the no-own-password and ungranted-staff /manage claims; add source-accurate rows for member /profile/password/ old/new/confirm fields and rendered help, Admin Add generated six-character prefill/SMTP-disabled refusal and first forced change, Admin reissue plus inactive-pending activation lock, and capability-gated management heading/controls. No fake claim that a screenshot or help association was tested unless the existing source/tests prove it.",
    "Changed relative Markdown links/anchors and current-absence phrase scan; docs-only diff/git diff --check; product/runtime/dependency/test/Compose/PLAN/INSTALL/QUICKSTART/authorization/human-ui/TESTING bytes unchanged; normal five exact-head CI at implementation/report heads. After merge, fresh independent full56 architecture-to-new-main ICA, not merely a check of these docs."
  ]
}
-->

# 063-a — make linked domain and form-guidance references current

## Goal and scope

Close the linked developer-reference truth cluster from the fresh full ICA of exact main `50502f2e158d64fb0f16135e0ea187fa44b82589`. PR129/062-a separately corrected the operator/canonical wording and is already merged on current base in metadata; this objective is a small docs-only companion, issue131/declared branch. Do not repeat product implementation or rewrite historical body/immutable OAP evidence.

## Numbered acceptance and negative paths

1. **Domain-model navigation.** `docs/domain-model.md` contains a useful older design sketch (proposed PROJECT/MEMBERSHIP/AVAILABILITY_RULE and superseded staff-only/no-group assumptions) but its header and current README/docs index links present it as the live model. Add a prominent HISTORICAL/SUPERSEDED banner at the top, with correctly resolved relative links to root ARCHITECTURE.md A-05/A-06/A-16 and docs/authorization.md; preserve the old body verbatim. Route the root README's domain model/time-semantics entry and docs/README current task index to the full current ARCHITECTURE (and authorization where relevant), not the old sketch. Retain a clearly labeled specialist/history link to the sketch in docs/README. Use actual relative Markdown links and verified heading anchors.
2. **Current form inventory.** `docs/ux/form-guidance-inventory.md` is linked as the ACTUAL runtime control map by TESTING.md and human-ui; fix its no-self-password-change and ungranted-staff-management claims. Source-check and add focused current coverage for member `/profile/password/` fields/help, Admin Add generated six-character prefill and email/disabled state, forced first change, Admin reissue and inactive-pending `is_active` lock, plus capability-gated management surfaces. Preserve earlier 037/048 work-order provenance as dated history. Do not claim any field-help association or browser test that current source/tests do not support; do not change UI or tests.
3. **Evidence/publication.** Check changed Markdown relative targets/anchors and current-absence language, verify historical domain body preserved and first-glance README still product-first, prove only four docs+order/pointer/report paths changed and all product/runtime/dependency/test/Compose/PLAN/INSTALL/QUICKSTART/auth/human-ui/TESTING bytes unchanged. Run normal five exact-head CI at implementation/report heads. CODING opens PR with `Closes #131`, commits docs+order/pointer, then report-only child with literal implementation head/SELF, verifies remote parent/path/head and sends FIFO OK; never merges. Strategy reviews/merges after checks, then a NEW independent full architecture-to-current-main ICA determines milestone closure.

## Strongest objection and recovery

Demoting the old design sketch could leave readers without a usable current model guide; link the authoritative ARCHITECTURE directly in README/docs and preserve the sketch under history. A form inventory can overclaim coverage if rows are guessed, so verify current rendered forms/tests before editing. D0, Decision NONE. Fresh CODING through sourced supervision `codex.sh`, `--yolo --profile early-beta` in right pane. No real mail/identity/data/deployment and no foreign PR113 mutation.

## Deferred human adjudication
- Decision: NONE
