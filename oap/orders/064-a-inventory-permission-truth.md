<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "064-a",
  "objective": 64,
  "round": "a",
  "slug": "inventory-permission-truth",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "d473d767208cb6ef06770f6a8a0b6dba8d17a347",
  "issue_number": 133,
  "branch": "codex/133-oap-064-a-inventory-permission-truth",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f7b5c98876a40b052c2d2fe057e57281e917ac5a72508e98caca512c1f0d1286",
    "PLAN.md": "e95135e756f6610b78e086a0b11395a2faa4d0fc0fa3a7bed658a091101a486f",
    "CRITICAL.md": "f5c4d78ed599ac9a8ce44687925dab29f221d8b65a2350a4f858c9f32a92c672",
    "docs/audit/ICA-PROTOCOL.md": "67075c18b6102e3cbd23c5b4836ca0e004be374458dbd5e5396bbeefdeaa098f",
    "docs/ux/form-guidance-inventory.md": "86ba05b933126a3b7840fc7cd726ca07a1d9c0c09d4a940344f63ff27fe64739",
    "src/slaif_reservation/assets/api.py": "0388f4565ad80d027a376bccea4765a7ec22c5a9ac1386e178088f63d4347bfe",
    "src/slaif_reservation/api/permissions.py": "cd7d3adbc3c345f07e8456ac7abf25cc3eac4d6aeb39e62909cbf5b66e5c56c4",
    "docs/human-ui.md": "a9e323cddb853262e5341392a1127e483460ffffbcac147121707b1007df9f20",
    "TESTING.md": "3fd59cf037e1428484ac2de0f236e55da909e75c0fb4a8ebf3a6c41456f66e72"
  },
  "requirements": [
    "SAR-037",
    "SAR-038",
    "SAR-044"
  ],
  "allowed_paths": [
    "docs/ux/form-guidance-inventory.md",
    "oap/active",
    "oap/orders/064-a-inventory-permission-truth.md",
    "oap/reports/064-a-inventory-permission-truth.md"
  ],
  "forbidden_resources": [
    "No other docs/README/PLAN/ARCHITECTURE/CRITICAL/projection changes, no application source/migrations/tests/fixtures, dependencies/lock, Docker/Compose/proxy/settings/API behavior, OAP helpers/workflows or historical audit/order/report rewrite.",
    "No real SMTP/recipient/credential, real identity administration, private data/production DB/host/DNS/TLS/firewall/public exposure/deployment, foreign PR113 mutation or CODING merge/automerge."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human selected product-first/factual documentation and field-guidance requirements, group authorization and account onboarding; 2026-11-10 execution-to-closure direction",
      "section_or_evidence": "Current linked field inventory must name the actual live asset API permission guard. One documentation statement correction; no new product meaning or access grant."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE.md A-15/A-16/A-17 and SAR-037/038/044; docs/audit/ICA-PROTOCOL.md",
      "section_or_evidence": "Asset list/detail REST remain staff-session-only; bearer assets:read is reserved. Current source uses IsActiveStaffHuman, which enforces active non-service staff human status. Full fresh ICA after remediation is required for milestone closure."
    },
    {
      "marker": "E",
      "source": "Fresh independent full SAR001..056 ICA at exact clean merged main d473d767208cb6ef06770f6a8a0b6dba8d17a347, private report SHA256 a58596b5df7523ed3cff020a7e81c05374535c09f16bbc4ebfcd26be4684d210; exact-main CI runs43020371985 and43020371947 five/five SUCCESS",
      "section_or_evidence": "55 IMPLEMENTED/1 PARTIAL (SAR044), no product-code blocker. docs/ux/form-guidance-inventory.md:162 says SessionAuthentication + IsAdminUser; actual src/slaif_reservation/assets/api.py list/detail both set permission_classes=[IsActiveStaffHuman], class in api/permissions.py. Existing report restates route and reserved bearer scope correctly. This is the sole current in-target finding in the full matrix."
    },
    {
      "marker": "I",
      "source": "One inventory sentence and current read-only asset API/permission source",
      "section_or_evidence": "Replace IsAdminUser with IsActiveStaffHuman in the linked inventory, optionally clarify that it rechecks active non-service staff human. Do not change any route, guard, test or other prose. Verify exact current source identity and docs-only byte scope."
    },
    {
      "marker": "C",
      "source": "Independent ICA sole SAR044 finding; CRITICAL empty",
      "section_or_evidence": "D0/DHA NONE. Strongest objection is overclaiming a security change from a one-word docs correction; explicitly state live runtime guard was already correct, preserve session-only/bearer-reserved semantics. No D2 crossing."
    }
  ],
  "decision_class": "D0",
  "target_gate": "One one-document reviewed PR correcting the live asset API permission-class name with exact-head five CI; then fresh independent full SAR001..056 ICA at exact merged main before milestone closure; no real SMTP/deployment",
  "expected_report_path": "oap/reports/064-a-inventory-permission-truth.md",
  "tests": [
    "Compare docs/ux/form-guidance-inventory.md asset REST paragraph against both current AssetListAPIView and AssetDetailAPIView permission_classes in assets/api.py and IsActiveStaffHuman in api/permissions.py. It must say SessionAuthentication + IsActiveStaffHuman (active non-service human staff) and retain no bearer assets:read route / reserved scope; no IsAdminUser reference in the current inventory.",
    "Changed-path and relative Markdown link check, git diff --check; only inventory plus OAP order/pointer/report changed, all application/runtime/dependency/test/Compose and other docs byte-identical. Normal five exact-head CI at implementation and report heads; no local full test run for one-word docs change. After merge fresh independent FULL architecture-to-current-main 56-row ICA, not just this line."
  ]
}
-->

# 064-a — correct asset API guard name in current form inventory

## Goal and scope

Close the sole in-target documentation finding from the fresh independent full ICA of exact main `d473d767208cb6ef06770f6a8a0b6dba8d17a347`: the linked form-guidance inventory names the wrong permission class for routed staff asset list/detail REST. Actual product code is correct and must remain byte-identical. Issue133/branch as metadata. Prior reports/audits remain immutable historical evidence.

## Numbered acceptance and negative paths

1. In `docs/ux/form-guidance-inventory.md`'s asset REST paragraph, replace the incorrect `IsAdminUser` with current `IsActiveStaffHuman`, verified in both `assets/api.py` views and `api/permissions.py`. Explain only the existing active non-service-account human staff session gate as needed; preserve `SessionAuthentication`, the live list/detail routes, and the reserved/non-working bearer `assets:read` scope. Do not imply tokens can discover assets or that the guard has changed now.
2. Do not edit any application source, tests, migration, settings, API schema, Docker/Compose, other documentation or historical evidence. Check the changed paragraph in context, its relative links, exact changed path list and `git diff --check`. No local full product suite is needed for this one-document correction; normal five exact-head CI must pass on implementation and report heads.
3. CODING opens one PR with `Closes #133`, commits the inventory+order/pointer, then a report-only child with literal implementation head/SELF, verifies remote parent/path/head and signals FIFO OK. CODING never merges. Strategy reviews and expected-head merges after checks. A new independent FULL SAR-001..056 architecture-to-current-main ICA, not a one-line signoff, determines whether M-ACCOUNT-ONBOARDING can close. No real SMTP/deployment.

## Strongest objection and recovery

A one-word documentation fix must not be mistaken for a new security control. The guard already exists in runtime source; this round only names it accurately. D0, Decision NONE. Fresh CODING through sourced supervision `codex.sh`, `--yolo --profile early-beta` in the right pane. Preserve valuable worktrees, foreign PR113 and all real resources.

## Deferred human adjudication
- Decision: NONE
