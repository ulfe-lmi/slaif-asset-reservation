<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "061-a",
  "objective": 61,
  "round": "a",
  "slug": "current-operator-truth",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "921f7a70dbd5c9d450661746ddee0e70af2cac59",
  "issue_number": 126,
  "branch": "codex/126-oap-061-a-current-operator-truth",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f7b5c98876a40b052c2d2fe057e57281e917ac5a72508e98caca512c1f0d1286",
    "PLAN.md": "78dbba69805f3915a81fc1930b2f487661c88f2a3c0a3449f8ec21964570ab4d",
    "CRITICAL.md": "f5c4d78ed599ac9a8ce44687925dab29f221d8b65a2350a4f858c9f32a92c672",
    "docs/audit/ICA-PROTOCOL.md": "67075c18b6102e3cbd23c5b4836ca0e004be374458dbd5e5396bbeefdeaa098f",
    "INSTALL.md": "178ae91cf783d39d4df971545642479477280445f414d69a809ef5b316dcb0fa",
    "docs/deployment.md": "68aa2105cd63dbc10f9de7c5e06b50c2c6620d72f2c537e4a0238170afe6972d",
    "docs/README.md": "b6dc3d5e49d596e9dfc82c0aa33bae742d778e17329bed96eec1762b57ce0e16",
    "docs/authorization.md": "cba3ef323d6f964d3e142060bb5a5b465c16aa4bf71eefba3131835b4563a5dd",
    "docs/api-contract.md": "ff9feef1c7e57df7202749b31ed8e033e9161bb39296d88b14995449eb06d18f",
    "src/slaif_reservation/accounts/authorization.py": "47a206e9129205c7e19cb42252022ff0ad42223be84baf8b90d758290dfe4c51",
    "src/slaif_reservation/api/read_all_views.py": "790bfe8eddb72ea320720c0dfdd7aa5a584e050dfdc9703d60b925bb66ef3cc4",
    "src/slaif_reservation/reservations/services.py": "8ade38b1000db44f48c34cd4e2b273bb0b03b2d7947ec93bfa7f751b630dedae"
  },
  "requirements": [
    "SAR-036",
    "SAR-037",
    "SAR-038",
    "SAR-048",
    "SAR-049",
    "SAR-050",
    "SAR-051",
    "SAR-053"
  ],
  "allowed_paths": [
    "INSTALL.md",
    "docs/deployment.md",
    "docs/README.md",
    "oap/active",
    "oap/orders/061-a-current-operator-truth.md",
    "oap/reports/061-a-current-operator-truth.md"
  ],
  "forbidden_resources": [
    "No README/QUICKSTART/PLAN/ARCHITECTURE/CRITICAL/projection/authorization/API-contract/runbook changes, no application source/migrations/tests/fixtures, dependencies/lock, Docker/Compose/proxy/security settings/API behavior, OAP helpers/workflows or historical audit/order/report rewrite. If a broken link cannot be repaired in allowed paths, report to STRATEGIC instead of expanding silently.",
    "No real SMTP/recipient/credential, real identity administration, private data/production DB/host/DNS/TLS/firewall/public exposure/deployment, foreign PR113 mutation or CODING merge/automerge."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human selected group authorization/read-all and account-onboarding product meaning; earlier product-first repository documentation objective; 2026-11-10 demand to complete selected milestone",
      "section_or_evidence": "Current operator guidance must describe implemented permission-scoped booking and read-all accurately. This is doc truth, not a product feature, general policy language or broadened access."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE.md A-16/A-17; SAR-036/037/038/048/049/050/051/053; ICA-PROTOCOL.md",
      "section_or_evidence": "Book capability and exact-asset allowed group eligibility gate reservation creation; cross-user read is explicit permission browser surface and dual-gated read-only bearer scope. Projects/organizational membership remain deferred. Historical internal-alpha pack is specialist history, not current operator contract. Full fresh ICA after docs merge."
    },
    {
      "marker": "E",
      "source": "Fresh independent full SAR001..056 ICA at exact merged main 921f7a70dbd5c9d450661746ddee0e70af2cac59, private report SHA256 381eae88bacd80aefcf5febe736f1252eeade0f797ca1bed7a3b7427df70d147; exact-main CI run42998271752 and OAP run42998271612 five/five SUCCESS",
      "section_or_evidence": "Auditor source-first scan found current INSTALL.md:767-768 falsely says cross-user read unimplemented; docs/deployment.md:720-721 falsely says all authenticated humans broadly reserve; docs/README.md:44-45 still frames live-linked superseded preparation pack as current internal-network pack. Current README/docs/authorization/api-contract and source implement read-only read-all with permission+scope, explicit Book grant/asset group checks. Other current absence claims scoped truthfully or historical. Final ICA matrix: 53 IMPLEMENTED, 3 PARTIAL (SAR036/037/053), 0 ABSENT/UNPROVEN. Exact 921f main CI test ultimately completed SUCCESS with 1461 passed; no product-code blocker reproduced."
    },
    {
      "marker": "I",
      "source": "Three current docs and existing authorization/API contract source",
      "section_or_evidence": "In INSTALL remove cross-user read from deferred project/membership list and point to explicit read-only browser/bearer dual gate; in deployment replace broad-authenticated-human claim with Book+asset-group+policy semantics; in docs index label the linked pack historical/superseded and point to current INSTALL. Keep concise, no duplicate full security procedure or product code."
    },
    {
      "marker": "C",
      "source": "Independent ICA concrete doc findings; CRITICAL empty",
      "section_or_evidence": "D0/DHA NONE. Strongest objection: an imprecise edit could imply all agents may read everyone or all logged-in humans may reserve. State permission and token scope jointly, read-only, and preserve deferred project/membership and operator grants; no access change."
    }
  ],
  "decision_class": "D0",
  "target_gate": "One docs-only reviewed PR removing three current operator/index contradictions, exact-head five CI green; after merge fresh independent full SAR001..056 architecture-to-current-main ICA before milestone closure; no real SMTP/deployment",
  "expected_report_path": "oap/reports/061-a-current-operator-truth.md",
  "tests": [
    "Current INSTALL booking paragraph: cross-user reservation read is no longer in absent/deferred list; explain explicit browser permission and bearer permission+reservations:read_all scope, read-only, without implying cross-user mutation or directory access. Project/organizational membership and per-token asset restrictions remain deferred as in current source.",
    "Current docs/deployment operating-limits paragraph: no blanket authenticated-human booking claim; describe explicit reservations.book_assets grant, exact-asset allowed-group eligibility when restricted, and policy, with no automatic grant to new accounts. Keep existing network/SMTP/operator boundaries unchanged. docs/README marks preparation pack historical/superseded and routes current operators to INSTALL. Verify changed relative links/anchors, current absence-language scan, and README/QUICKSTART/PLAN/runbook/auth/API/code bytes unchanged.",
    "Docs-only diff/git diff --check; normal five exact-head CI at implementation/report heads. After merge, fresh independent full56 architecture-to-new-main ICA, not a check of only these three lines. No unrelated local bespoke qualification."
  ]
}
-->

# 061-a — correct current booking and read-all operator prose

## Goal and scope

Close three current-text contradictions found in the fresh independent full SAR-001..056 audit of exact main `921f7a70dbd5c9d450661746ddee0e70af2cac59`. The product implementation is already present; this round changes only the operator documentation/index paths in metadata. Issue126/branch as declared. Preserve historical OAP/audit/runbook records and all previous immutable orders/reports.

## Numbered acceptance and negative paths

1. **Read-all truth in INSTALL.** The current booking/authorization paragraph must stop saying cross-user read access is unimplemented. State concisely that the separate All reservations browser view requires explicit `reservations.view_all_reservations` permission, and bearer cross-user list/detail also requires its token's `reservations:read_all` scope plus the owner's current permission. It is read-only; no cross-user mutation or general user-directory API is implied. Keep project/organizational-membership authorization and per-token asset restriction deferrals accurate. Link to existing `docs/authorization.md` for the full matrix.
2. **Booking truth in deployment.** Replace “authenticated humans have broad reservation access under policy rules” with the actual current gate: `reservations.book_assets` must be granted to the user, a group-restricted asset requires at least one allowed group membership, and existing policy rules still apply. New accounts receive no automatic booking grant. Do not reinterpret Staff/superuser status or assert project membership exists. Keep the rest of the current operator limits and HTTPS/SMTP procedure intact.
3. **Historical-pack index.** In `docs/README.md`, label the linked `internal-alpha-pilot-preparation.md` as a historical/superseded internal-network planning template, not current operator guidance; direct current installation to `INSTALL.md`. Do not rewrite the historical pack or churn other index entries.
4. **Evidence/publication.** Read these current paragraphs as an operator, check changed relative Markdown links/anchors and absence claims, prove product/runtime/dependency/test/Compose/README/PLAN/runbook/auth/API bytes unchanged, and run normal five exact-head CI on implementation/report heads. CODING opens PR with `Closes #126`, commits order/pointer+docs implementation, then report-only child with literal implementation head/SELF, verifies remote parent/path/head, signals FIFO OK, never merges. Strategy reviews and expected-head merges only after checks. Fresh independent full architecture-to-new-main ICA after merge determines closure; no real SMTP/deployment.

## Strongest objection and recovery

Bad wording could overstate cross-user data access or make booking seem available to everyone. Keep the permission+scope and booking-grant boundaries explicit, with the detailed contract linked. D0, Decision NONE. Fresh CODING through sourced supervision `codex.sh`, `--yolo --profile early-beta` in the right pane. No real identities/data/host/deployment and no foreign PR113 mutation.

## Deferred human adjudication
- Decision: NONE
