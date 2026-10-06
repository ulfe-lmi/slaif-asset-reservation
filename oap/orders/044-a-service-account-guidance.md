<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "044-a",
  "objective": 44,
  "round": "a",
  "slug": "service-account-guidance",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "7877fbe82809c082111c8dcfe0ab47aa8620e508",
  "issue_number": 87,
  "branch": "codex/87-oap-044-a-service-account-guidance",
  "pr_mode": "CREATE_OR_RESUME",
  "previous_round": null,
  "pr_number": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f8a8df265d4dd452969d4bee874045c8f8a8261f9c87c96ba4c049a7dddf320d",
    "PLAN.md": "b19219e2d727af5a9554e011ba45a786f1bb61f25c001011fc18006cae665d08"
  },
  "requirements": [
    "SAR-014",
    "SAR-044"
  ],
  "allowed_paths": [
    "src/slaif_reservation/accounts/admin.py",
    "tests/test_form_guidance.py",
    "tests/browser/test_form_guidance_browser.py",
    "docs/audit/reports/M-INTERNET-UX-PILOT-7877fbe.md",
    "oap/active",
    "oap/orders/044-a-service-account-guidance.md",
    "oap/reports/044-a-service-account-guidance.md"
  ],
  "forbidden_resources": [
    "Authority/service/authentication/model/schema/migration/API/runtime/dependency/theme changes",
    "Optional audit O1 static-test prerequisite and O2 readiness reporting",
    "History/audit rewriting/new OAP machinery",
    "Real exposure/hosts/DNS/TLS/firewall/identities/secrets/private data/lab/Neumann",
    "Valuable-checkout product tests/reset/clean/forcepush"
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human M-INTERNET-UX-PILOT instructions",
      "section_or_evidence": "requirement5 all fields/choices explain current effect; human takeover coding stopped"
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE.md",
      "section_or_evidence": "A-04/A-05/A-15; SAR-014 existing service-account token deferral and SAR-044 accurate help"
    },
    {
      "marker": "E",
      "source": "Fresh ICA at 7877fbe",
      "section_or_evidence": "88c2edbcf3983276c2e3aa035817ae724bc836bb6ec3ae67b85dcba8bf8f0197; real rendered help/G issuance TOKEN_OWNER_INVALID and existing bearer401; all5 main CI996passes"
    },
    {
      "marker": "I",
      "source": "ICA F1",
      "section_or_evidence": "46IMPLEMENTED/1PARTIAL SAR-044; narrow wording correction; no security bypass"
    },
    {
      "marker": "C",
      "source": "CRITICAL.md",
      "section_or_evidence": "D0 known accurate behavior, no unresolved human choice; DHA_NONE"
    }
  ],
  "decision_class": "D0",
  "target_gate": "M-INTERNET-UX-PILOT independent qualification; real deployment remains human D2",
  "expected_report_path": "oap/reports/044-a-service-account-guidance.md",
  "tests": [
    "Rendered help bound to current human-token positive and service-flag issuance/bearer denial",
    "Real browser administration user change at1440/390, visible associated help and viewed screenshots",
    "All5 exact implementation and immutable report-head CI; fresh FULL architecture-to-new-main ICA"
  ]
}
-->

# 044-a — explain current service-account restrictions

## Goal / scope
One purpose: correct the mandatory fresh ICA F1 guidance contradiction, without
changing rights. ROOT executes under human takeover; no coding client restart.
Base is exact merged7877fbe82809c082111c8dcfe0ab47aa8620e508/PR86 closed85,
source clean and all5 main CI SUCCESS/996 tests. Actual issue87; PRnumber retrieved
only after creation. Frozen ICA88c2edbcf3983276c2e3aa035817ae724bc836bb6ec3ae67b85dcba8bf8f0197
is preserved byte-identically in the allowed report path.

## Acceptance
1. Change only accounts/admin.py service-account field help: explain that the
   reserved service-account class currently blocks member/admin sign-in AND API
   token issuance/use; current automation uses an active human owner's scoped
   token. The effect of enabling this high-impact flag must be plain.
2. Pin meaningful rendered help/ARIA and current behavior: human-owned token
   succeeds before flag change; the existing token is denied afterward and new
   issuance is refused. Preserve existing password/admin/validation assertions.
   Prove the new expectation fails against the old inaccurate text.
3. Real Playwright user-change surface at1440/390: useful exact guidance visible
   and associated, no page overflow, controls/actions usable; capture and actually
   inspect changed help at both widths. No unrelated visual refinements.
4. Preserve the full fresh47-row partial ICA bytes, history and its failed static-
   prerequisite diagnostic; do not rewrite it as a passing report. Optional O1/O2
   are not this objective. Application services/auth/model/schema/API/runtime/
   dependencies/themes/architecture/projection/law remain byte-identical.
5. Focused tests during edits; full required5 CI jobs at literal final implementation
   and immutable report heads, actual report-only firstparent/SELF/remoteverify,
   expected-head development merge. Afterward a NEW fresh FULL architecture-to-
   current-main ICA remains required, not merely F1 text-queue closure.

## Verification / negative paths
Owned disposable source/PG17/minimal role-cleared child env for product tests;
old text regression fails, human token positive and service-account issuance/use
negative paths stay real. Browser screenshot evidence contains no entered password,
token, cookies/CSRF/hash/private identities. Lint/type/diff and exact path checks;
standard CI includes PG/concurrency/browser/HTTPS/abuse/Gunicorn/default/restore/
container/pip-audit and OAP. Never invoke product fixtures in valuable checkout.

## Non-goals / documentation / recovery
No permission/backend feature, migration, API or style change; no optional audit
refinements or new infrastructure. Only immutable audit/report/order evidence is
added; product documentation already directs automation to human-owned tokens.
Preserve any existing work and reconcile actual same objective/branch/PR after
interruptions. Immutable orders/reports never amended. No real D2 action.

Strongest reason against change: a conceptual machine-account description might
be read as intended future meaning. Current visible help must explain current
behavior and immediate token denial, while preserving the explicitly deferred
service-account capability; test the same authority rather than implement it.
This is ordinary D0 accuracy repair, not a CRITICAL dilemma.

## Reporting
Short exact evidence report, real counts/failures/commands/head/PR/screenshot
views/scope/remaining fullICA gate; observed implementation CI separate from
report-head checks not yet observed. PRbody Closes #87. No coding merge/auto-merge,
no claim of release, full milestone acceptance or real exposure authorization.

## Deferred human adjudication
- Decision: NONE
