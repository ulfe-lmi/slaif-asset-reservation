<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "060-a",
  "objective": 60,
  "round": "a",
  "slug": "onboarding-doc-truth",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "50eab07e49fad2a56177ce22d66ec1386546b65b",
  "issue_number": 124,
  "branch": "codex/124-oap-060-a-onboarding-doc-truth",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f7b5c98876a40b052c2d2fe057e57281e917ac5a72508e98caca512c1f0d1286",
    "PLAN.md": "e15eb06f6559886808916812dc555c244cc038ff42996a12276b58319562f864",
    "CRITICAL.md": "f5c4d78ed599ac9a8ce44687925dab29f221d8b65a2350a4f858c9f32a92c672",
    "docs/audit/ICA-PROTOCOL.md": "67075c18b6102e3cbd23c5b4836ca0e004be374458dbd5e5396bbeefdeaa098f",
    "docs/runbooks/internal-alpha-pilot-preparation.md": "3c53c878bd5337c79295d47e8b7624f414c991aaa9159fdb4909a22c08e59c31",
    "docs/runbooks/internal-alpha-pilot-readiness.md": "ce5660541fcf49cc5435b9c25ad931dff1298237822e10a15747b31d256420cf",
    "docs/runbooks/README.md": "fb5688a9ab296fb118ed03aad737461b051d442f365e3d1dd3852d1944b3d645",
    "docs/README.md": "b6dc3d5e49d596e9dfc82c0aa33bae742d778e17329bed96eec1762b57ce0e16",
    "README.md": "9f535cf8326d79a59208892b98f5cce92a946d1f1a5f2eab635354204966c5c2",
    "INSTALL.md": "178ae91cf783d39d4df971545642479477280445f414d69a809ef5b316dcb0fa",
    "docs/deployment.md": "68aa2105cd63dbc10f9de7c5e06b50c2c6620d72f2c537e4a0238170afe6972d",
    "docs/authorization.md": "cba3ef323d6f964d3e142060bb5a5b465c16aa4bf71eefba3131835b4563a5dd"
  },
  "requirements": [
    "SAR-036",
    "SAR-037",
    "SAR-038",
    "SAR-054",
    "SAR-055",
    "SAR-056"
  ],
  "allowed_paths": [
    "PLAN.md",
    "docs/runbooks/internal-alpha-pilot-preparation.md",
    "docs/runbooks/internal-alpha-pilot-readiness.md",
    "oap/active",
    "oap/orders/060-a-onboarding-doc-truth.md",
    "oap/reports/060-a-onboarding-doc-truth.md"
  ],
  "forbidden_resources": [
    "No README/INSTALL/deployment/authorization/architecture/CRITICAL/projection changes, no application source/migrations/tests/fixtures, dependencies/lock, Docker/Compose/proxy/security settings/API, OAP helpers/workflows or historical audit/order/report rewrite. If a changed link makes an allowed-path-only repair impossible, report it to STRATEGIC rather than expanding scope silently.",
    "No real SMTP/recipient/credential, real identity administration, private data/production DB/host/DNS/TLS/firewall/public exposure/deployment, foreign PR113 mutation or CODING merge/automerge."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human 2026-11-09 selected account-onboarding milestone and prior product-first repository presentation objective; human 2026-11-10 demanded implementation to completion",
      "section_or_evidence": "Current canonical and operator-linked material must not contradict the merged product. This objective is a small docs-only closure of independently observed current-state ambiguity, not a new feature or roadmap."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE.md A-17/SAR-036/SAR-037/SAR-038 and docs/audit/ICA-PROTOCOL.md",
      "section_or_evidence": "Onboarding email and logged-in own-password change narrow prior deferral; historical OAP material remains available but current PLAN/operator routes must distinguish dated selection observations from current implementation. After remediation, repeat full architecture-to-current-main ICA."
    },
    {
      "marker": "E",
      "source": "Fresh independent full SAR-001..056 re-audit at exact merged main 50eab07e49fad2a56177ce22d66ec1386546b65b, private report SHA256 6b3feccbc544c1030df7c78583f62c4aa678f438047f86617a355d0fa4e58190; five exact-main CI green",
      "section_or_evidence": "54 IMPLEMENTED, SAR036/037 PARTIAL, no product-code blocker. PLAN P-09 selection-era paragraphs at lines306-309 and355-363 say today no password route, purposes056-059 draft/no PR, no email/settings/delivery, now false as current status. Live-linked docs/runbooks/internal-alpha-pilot-preparation.md retains old absent-email/resource-restriction claims; docs/runbooks/internal-alpha-pilot-readiness.md calls it a companion pack. Current INSTALL/deployment/authorization are correct and should be linked, not rewritten."
    },
    {
      "marker": "I",
      "source": "PLAN.md P-09, historical preparation pack, readiness companion link; current operator docs/index",
      "section_or_evidence": "Relabel P-09 old observations and purpose table explicitly as 2026-11-09 selection-era history, replace current status with a concise implementation/evidence pointer that remains true after final ICA and does not claim real deployment or human milestone acceptance. Place prominent historical/superseded banner at top of preparation pack with current INSTALL/deployment/authorization/architecture links; clarify readiness companion link is a historical template. Preserve old body and other docs."
    },
    {
      "marker": "C",
      "source": "Independent ICA findings at exact main; CRITICAL empty",
      "section_or_evidence": "D0/DHA NONE. Strongest reason not to edit is loss of historical provenance or creation of another stale status ledger; preserve body, date the old claims, use durable current-source/evidence pointers. No D2 crossing."
    }
  ],
  "decision_class": "D0",
  "target_gate": "One docs-only reviewed PR removing current-state contradictions in PLAN and live-linked historical pilot pack, exact-head five CI green; then fresh independent full SAR-001..056 ICA at exact merged main before milestone closure; no real SMTP/deployment",
  "expected_report_path": "oap/reports/060-a-onboarding-doc-truth.md",
  "tests": [
    "Inspect first/current P-09 paragraphs and historical table after edit: no unqualified present-tense claim that password-change route/email/SMTP settings are absent, no live DRAFT/no PR claim for delivered purposes; original human selection/mitigations/deferrals and prior context remain intact; current implementation is accurately described without claiming ICA/human release/deployment approval.",
    "Preparation pack top banner is immediately visible and explicitly says historical/superseded, directs operators to current INSTALL, deployment, authorization and architecture; old body remains intact. Readiness companion link labels pack historical. Check all changed relative Markdown targets and anchors; normal README and current operator INSTALL/deployment remain byte-identical.",
    "Docs-only diff/no application/runtime/dependency/test/Compose bytes, git diff --check, normal five exact-head CI at implementation/report heads. After merge, fresh independent full 56-row architecture-to-new-main ICA; do not self-certify from coding report."
  ]
}
-->

# 060-a — clarify current onboarding plan and historical pilot pack

## Goal and scope

Close the only remaining in-target findings from the fresh independent audit of merged main `50eab07e49fad2a56177ce22d66ec1386546b65b`: SAR-036/037 are PARTIAL because current canonical PLAN P-09 and a live-linked historical pilot pack can mislead a reader about implemented email/password and asset restriction capabilities. No product-code defect remains in the auditor's focused replay. This is one small documentation truth objective; issue124/branch as metadata. Preserve the earlier failed ICA/private evidence and all immutable OAP records.

## Numbered acceptance and negative paths

1. **P-09 dated truth.** Keep the human selection, A-17 reference, bounded mitigations, deferrals and historical 055–059 scope map. Relabel the no-password-route observation and draft-purpose/no-PR prose as facts at the 2026-11-09 target selection, never as current facts. Replace P-09's current-status paragraph with a short durable statement that the selected own-password change, operator SMTP transport and temporary Admin onboarding have landed in merged main, their exact evidence lives in merged PRs/current reports, and independent ICA plus human release/deployment judgments remain separate. Avoid a status ledger that will become false as soon as this docs PR merges; do not claim the milestone already closed or real SMTP enabled.
2. **Historical pack boundary.** At the very top of `docs/runbooks/internal-alpha-pilot-preparation.md`, add a conspicuous historical/superseded label: its absence-of-email/resource-restriction statements reflect its old internal-alpha planning date, are not current operator instructions, and must not be used to configure the current service. Link current `INSTALL.md`, `docs/deployment.md`, `docs/authorization.md` and root `ARCHITECTURE.md` (A-16/A-17). Preserve the old body verbatim below the banner; no cosmetic rewrite of history. In `internal-alpha-pilot-readiness.md`, update the companion link sentence to label the pack a historical template, not the current feature contract.
3. **Evidence/publication.** Read raw/rendered initial sections as a current operator. Verify every changed link/anchor, current README/INSTALL/deployment/authorization bytes unchanged, no code/runtime/dependency/Compose/test change, and normal five exact-head CI at implementation/report heads. CODING opens PR with `Closes #124`, commits order/pointer+docs implementation, then immutable report-only child with literal implementation head/SELF, verifies remote parent/path/head, sends FIFO OK and never merges. Strategy merges only after exact-head review. A fresh independent full SAR-001..056 audit after merge determines whether M-ACCOUNT-ONBOARDING can close; this docs change does not self-certify.

## Strongest objection and recovery

A rushed edit could erase useful selection-era evidence or replace it with another stale status paragraph. Date the historical claims and point current readers to actual source/merged evidence; preserve the runbook body. D0, Decision NONE. Fresh CODING through sourced supervision `codex.sh`, `--yolo --profile early-beta` in the right pane; no real mail/identity/deployment, foreign PR113 untouched, no reset/clean of valuable worktrees.

## Deferred human adjudication
- Decision: NONE
