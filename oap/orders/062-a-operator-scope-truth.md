<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "062-a",
  "objective": 62,
  "round": "a",
  "slug": "operator-scope-truth",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "50502f2e158d64fb0f16135e0ea187fa44b82589",
  "issue_number": 128,
  "branch": "codex/128-oap-062-a-operator-scope-truth",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f7b5c98876a40b052c2d2fe057e57281e917ac5a72508e98caca512c1f0d1286",
    "PLAN.md": "78dbba69805f3915a81fc1930b2f487661c88f2a3c0a3449f8ec21964570ab4d",
    "CRITICAL.md": "f5c4d78ed599ac9a8ce44687925dab29f221d8b65a2350a4f858c9f32a92c672",
    "docs/audit/ICA-PROTOCOL.md": "67075c18b6102e3cbd23c5b4836ca0e004be374458dbd5e5396bbeefdeaa098f",
    "SECURITY.md": "cb032d006df8e50c04d06302a21bd90ab4f53016653c2ea5c6501b38c5a344f4",
    "QUICKSTART.md": "9e3bfb17db58f02885771adadb90a80ada6d60a51714eceaddb7be3743c8d08e",
    "docs/human-ui.md": "4522e72388e49671e3293eab1e0d2f7875433252dd1105bd0dbd691734cfbc18",
    "docs/runbooks/README.md": "fb5688a9ab296fb118ed03aad737461b051d442f365e3d1dd3852d1944b3d645",
    "docs/runbooks/internal-alpha-pilot-preparation.md": "0f8d9cc0f828d21c513df4a3b1b80f88b5fdeb618dff186d78981f07b3614c55",
    "docs/authorization.md": "cba3ef323d6f964d3e142060bb5a5b465c16aa4bf71eefba3131835b4563a5dd",
    "src/slaif_reservation/accounts/authorization.py": "47a206e9129205c7e19cb42252022ff0ad42223be84baf8b90d758290dfe4c51",
    "src/slaif_reservation/management_ui/views.py": "b9f589caf65a5edf697180d178ff314385bf1200c35ea6e72b7723917e26c81a"
  },
  "requirements": [
    "SAR-036",
    "SAR-037",
    "SAR-038",
    "SAR-044",
    "SAR-048",
    "SAR-049",
    "SAR-050",
    "SAR-055"
  ],
  "allowed_paths": [
    "PLAN.md",
    "SECURITY.md",
    "QUICKSTART.md",
    "docs/human-ui.md",
    "docs/runbooks/README.md",
    "oap/active",
    "oap/orders/062-a-operator-scope-truth.md",
    "oap/reports/062-a-operator-scope-truth.md"
  ],
  "forbidden_resources": [
    "No README/INSTALL/deployment/authorization/domain-model/form-guidance/ARCHITECTURE/CRITICAL/projection changes, no application source/migrations/tests/fixtures, dependencies/lock, Docker/Compose/proxy/security settings/API behavior, OAP helpers/workflows or historical audit/order/report/runbook-body rewrite. Linked developer-reference truth is a separate follow-on objective; report any dependency rather than expanding paths.",
    "No real SMTP/recipient/credential, real identity administration, private data/production DB/host/DNS/TLS/firewall/public exposure/deployment, foreign PR113 mutation or CODING merge/automerge."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human-selected existing-group authorization, account-onboarding and product-first documentation objectives; 2026-11-10 direction to execute through closure",
      "section_or_evidence": "Current canonical/operator text must not imply that implemented group eligibility, management capabilities or onboarding email are absent. This is docs truth, not a feature or widened access."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE.md A-16/A-17, current dynamic SAR-001..056 index; SAR-036/037/038/044/048/049/050/055; ICA-PROTOCOL.md",
      "section_or_evidence": "Book eligibility is explicit capability+exact-asset group; management is permission-gated for active humans independent of Staff, /admin/ still staff+model permissions; own-password change and configured onboarding email are implemented. Projects/organizational membership/OIDC/public reset/general notifications remain deferred. Historical selection prose must be dated, not erased."
    },
    {
      "marker": "E",
      "source": "Fresh independent full ICA at exact clean merged main 50502f2e158d64fb0f16135e0ea187fa44b82589, private report SHA256 67c2187c5b4544aea87cbf5ec48b42abf64bb516d9af1a9b2b4cf86250124ba9; exact-main CI run43004913109 + OAP43004913190 five/five SUCCESS",
      "section_or_evidence": "Matrix 52 IMPLEMENTED/4 PARTIAL (036/037/044/053), no product-code blocker. Definite current-text contradictions: PLAN P03 line61 stale SAR038 cap and P04 lines77-82 present-tense deferred group/email; SECURITY line8 broad group deferral; QUICKSTART lines135-137 staff-only /manage and missing own-password route; docs/human-ui line75 staff-only policy; docs/runbooks/README unlabelled historical prep pack. Separate linked developer domain/form inventory findings reserved for follow-on. Full current-doc scan complete; optional first-deployment SMTP clarity is not required for this objective."
    },
    {
      "marker": "I",
      "source": "Five allowed current docs plus current authorization/management source as read-only reference",
      "section_or_evidence": "Keep P04 original selection-era statements with explicit date and add concise current A16/A17 exception/deferral pointer; replace static SAR index cap with canonical dynamic index reference. Narrow SECURITY deferral. Correct QUICKSTART management/admin/password route and human-ui policy capability sentence. Label historical pack in runbooks index. No security/authorization behavior changes."
    },
    {
      "marker": "C",
      "source": "Independent ICA collected operator/canonical-doc findings; CRITICAL empty",
      "section_or_evidence": "D0/DHA NONE. Strongest objection is accidentally erasing historical human selections or overstating current authority. Preserve dated baseline, state exact current permission gate and deferred projects/OIDC, link canonical authorization; no D2 crossing."
    }
  ],
  "decision_class": "D0",
  "target_gate": "One docs-only reviewed PR correcting current operator/canonical scope text with exact-head five CI; then separate linked developer-reference docs objective and one final fresh full SAR001..056 ICA; no real SMTP/deployment",
  "expected_report_path": "oap/reports/062-a-operator-scope-truth.md",
  "tests": [
    "Current PLAN P03 points to full dynamic ARCHITECTURE SAR index without stale 038 cap; P04 explicitly dates October2026 selection-era deferrals and states implemented A16/A17 exceptions plus remaining projects/memberships/OIDC/public reset/general-notification deferrals without changing human provenance or risk gates.",
    "SECURITY current project/group statement no longer hides exact-asset group booking eligibility; QUICKSTART describes /manage/ as matching application-permission-gated for active humans, /admin/ as staff+model permission, and includes /profile/password/ for signed-in users; docs/human-ui policy sentence uses management capability, not Staff; runbooks index labels preparation pack historical/superseded. No new false public-readiness or cross-user access claim.",
    "Changed relative Markdown links/anchors and absence-language scan, docs-only diff/git diff --check, README/INSTALL/deployment/authorization/ARCHITECTURE/product-runtime/dependency/test/Compose bytes unchanged; normal five exact-head CI at implementation/report heads. No unrelated local bespoke qualification. After this and follow-on developer-reference docs merge, fresh independent full56 ICA."
  ]
}
-->

# 062-a — correct current operator and canonical authorization wording

## Goal and scope

Close the operator/canonical current-truth cluster from the fresh independent full audit of exact main `50502f2e158d64fb0f16135e0ea187fa44b82589`. The audit is a PARTIAL historical checkpoint (52 IMPLEMENTED/4 PARTIAL; no reproduced product-code blocker). This is one small documentation purpose on issue128/declared branch. The linked developer domain/form-inventory cluster will be a separate bounded objective; do not absorb it here or repeat ICA after this PR alone. Preserve immutable historical OAP and runbook bodies.

## Numbered acceptance and negative paths

1. **PLAN dated/current truth.** In P-03, remove the stale “SAR-001 through SAR-038” cap; point to ARCHITECTURE.md's full current index without a future-stale hardcoded range. In P-04, retain the original Internet-target selection and deferred ambition as dated selection-era context, then state current A-16/A-17 exceptions: exact-asset group booking access, explicit management/read-all capabilities, configured administrator onboarding email and logged-in own-password change are implemented. Projects/organizational memberships/delegated group ownership, OIDC/public forgotten-password reset/general notifications and real exposure/deployment remain deferred/separate. Do not make P-04 another PR ledger or alter human provenance.
2. **Operator/user entry.** Narrow SECURITY.md's blanket group-resource deferral to projects/organizational membership and DB-role separation while acknowledging current exact-asset group eligibility. In QUICKSTART, show `/profile/password/` for signed-in users; `/manage/` requires the matching management capability and admits eligible nonstaff active humans, while `/admin/` requires staff admission and relevant model permissions. In docs/human-ui, replace the unqualified “Staff can configure different policies” with the explicit manage-policy capability. Do not change reservation semantics or claim all authenticated users can book/read all.
3. **Historical index.** In docs/runbooks/README.md identify the old internal-alpha pilot-preparation pack as historical/superseded, pointing current operators to INSTALL. Leave the pack body and its 060-a top banner untouched. Do not churn other runbooks; optional first-deployment SMTP clarity is outside this acceptance.
4. **Evidence/publication.** Check every changed link/anchor and present-tense absence phrase in context, prove only five docs+order/pointer/report paths changed and all product/runtime/test/dependency/Compose/README/INSTALL/deployment/auth/domain-model/form-inventory bytes unchanged. Run normal five exact-head CI at implementation/report heads. CODING opens PR with `Closes #128`, commits order/pointer+docs implementation, then report-only child with literal implementation head/SELF, verifies remote parent/path/head and signals FIFO OK. CODING never merges. Strategy reviews and expected-head merges after checks; then the separate developer-reference docs purpose and final full ICA.

## Strongest objection and recovery

A blanket rewrite could erase the reason earlier milestones deferred group and email facets, or overstate current rights. Date the old context, state the exact current gates and keep the remaining deferrals. D0, Decision NONE. Fresh CODING through sourced supervision `codex.sh`, `--yolo --profile early-beta` in the right pane. No real identity/data/SMTP/deployment or foreign PR113 mutation.

## Deferred human adjudication
- Decision: NONE
