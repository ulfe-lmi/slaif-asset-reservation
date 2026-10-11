<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "046-a",
  "objective": 46,
  "round": "a",
  "slug": "home-portability",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "dadfb0a8a5a370c166b71a90c44b5e76ca2b7420",
  "issue_number": 91,
  "branch": "codex/91-oap-046-a-home-portability",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f8a8df265d4dd452969d4bee874045c8f8a8261f9c87c96ba4c049a7dddf320d",
    "PLAN.md": "d30d89981907dd2af475b7a5f27aa0715defed3a78c6431b76e7e05204ef833f"
  },
  "requirements": [
    "SAR-034",
    "SAR-035",
    "SAR-037",
    "SAR-038"
  ],
  "allowed_paths": [
    "oap/bin/oaplib.py",
    "oap/bin/oap_launch.py",
    "oap/bin/oap_doctor.py",
    "oap/bin/publish_order.py",
    "oap/bin/check_state.py",
    "oap/bin/verify_report.py",
    "oap/bin/check_ica.py",
    "oap/bin/append_critical.py",
    "oap/bin/oap_fifo.py",
    "oap/runtime.env.example",
    "oap/strategic-instructions/OAP-COMMUNICATION-strategic.md",
    "oap/strategic-instructions/strategic_model_init_material.md",
    "docs/OAP-RUNBOOK.md",
    "docs/AGENT-ROLE-SETUP.md",
    "tests/oap/oaptestlib.py",
    "tests/oap/test_home_paths.py",
    "oap/active",
    "oap/orders/046-a-home-portability.md",
    "oap/reports/046-a-home-portability.md"
  ],
  "forbidden_resources": [
    "Application/runtime/deployment/schema/migrations/dependencies/inventory changes",
    "Immutable orders/reports/history/bootstrap snapshots or authority evidence rewriting",
    "Credential/auth/session/history copying; provider/model/permission fallback; role/model launch or inference",
    "Real deployment/DNS/TLS/firewall/proddata/private exports/lab/Neumann jobs; broad cleanup; foreign process signals"
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human instruction2026-10-11",
      "section_or_evidence": "Everything moved to different machine/account; reconcile; paths relative to home; prior coding shutdown remains"
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE A02/A03 and strategic S13/S14/S19/S21",
      "section_or_evidence": "separate portable local roots, safe data parsing, no implicit launch/authority, preserve history/ownership"
    },
    {
      "marker": "E",
      "source": "Current live reconciliation and parser experiment",
      "section_or_evidence": "main dadfb0a, clean checkout, noopenPRissues,045acceptedquiescent; oldubuntu roots absent; ~/ config rejected; CLI0.162.1 version/help only"
    },
    {
      "marker": "I",
      "source": "New-machine path diagnostic",
      "section_or_evidence": "runtime seven pathkeys and active instructions use obsolete account; qualified records historical; FIFOs owned0600"
    },
    {
      "marker": "C",
      "source": "CRITICAL and human migration scope",
      "section_or_evidence": "known routine workflow portability D0; no new unresolved risk or product meaning; NONE"
    }
  ],
  "decision_class": "D0",
  "target_gate": "Development-control-plane portability only; no product milestone/release/deployment acceptance",
  "expected_report_path": "oap/reports/046-a-home-portability.md",
  "tests": [
    "home relative config/argv/CLI positive and malformed/foreign-user/traversal/interpolation negatives",
    "fake-client end-to-end with portable cwd/rolehome; real CLIhelp/print-only/state/FIFO/mode checks; no realmodelcalls",
    "fullOAPstdlib harness; standard five exactimplementation/report CI and report verification; scope/product neutrality"
  ]
}
-->

# 046-a — portable home-relative control-plane reconciliation

One purpose: safely support the human-authorized machine/account move without
hardcoding a login name in active OAP configuration/instructions. ROOT directly
executes under the retained coding-stop preference. Actual issue91/base dadfb0a8a5a370c166b71a90c44b5e76ca2b7420;
actual PR retrieved after creation, never invented. Prior045 is merged/completed,
not replayed. No new product target or real deployment is selected.

## Acceptance
1. Runtime data accepts absolute/empty paths as before and bounded `~/...` (or
   home itself where appropriate), expands against the current home without shell
   evaluation; refuses ~other-user, escaping .., NUL and all existing interpolation/
   duplicate/unknown/boolean/argv negatives. CLI paths also accept quoted home
   paths; existing cwd-relative file arguments remain. Argv path tokens resolve
   before execution, no eval or changed nonpath tokens. Ownership/symlink/root-
   separation/authority/activation/duplicate/report safety remains intact.
2. Active templates/runbooks/strategic communication/init path references and
   test default home use ~/ conventions, not old ubuntu or new janezp literals.
   Preserve immutable history/bootstrap/orders/reports. Full strategic role law/
   architecture and dense executor obligations remain unchanged; protocol data
   path contract is explicit. No hidden mandatory context expansion.
3. Isolated fixture tests prove two different home mappings, cwd independence,
   malformed/escape/foreign/symlink/ownership refusals and fake-client path/cwd/
   rolehome launch behavior; no real model. Original ~/ parser failure reproduced
   before implementation. Real installed CLI0.162.1 help/version is qualified
   separately from credentials/provider/live inference. Current print-only,
   state/FIFO/permissions checks must name real results/limits, not old passes.
4. Private reconciliation, with backups/receipts: runtime path fields end as
   home-relative; preserve model/provider/permission flags, auth/history,
   original human approval/qualification artifacts and completed journal.
   Current SDK-required concrete paths may be derived from current home (never
   assumed unexpanded ~ works); copied live qualification is historical, not a
   new-host pass. Update STATE/RUNTIME continuity and validated installed current
   instruction copies only after candidate acceptance. Coding remains stopped;
   no inference/autostart or unrestricted new-host authorization inferred.
5. Focused tests first, full OAP harness and all5 standard exactimplementation and
   immutable report-head CI; source review, report-only literalfirstparent/SELF/
   actualremote verification, expectedhead development merge and quiescence.
   PRbody Closes #91. Report source neutrality and new-runtime limitations.

## Scope / verification / negative paths
Only declared OAP helpers/tests/active docs plus authorized private migrated
configuration/continuity. Private backups/receipts contain no copied credentials
or raw transcripts. Exclude app/runtime/dependency/data/deployment edits and
immutable history. No source product tests in valuable checkout; stdlib fixtures
use owned temp roots. New client flags/providers/models are not selected and
live role startup is not authorized. Current controls are preserved, not relaxed
because roots moved. Verify actual home-relative behavior and no-write print-only;
current source/file diffs and published identities, not just a replace-all pass.

Strongest objection: automatic tilde expansion can resolve another user's home,
escape bounds, hide symlink ownership or accidentally reuse old authority/client
qualification. Limit it to current-home notation, retain pre-resolution ownership
checks/guards, exercise real boundaries with fake clients, preserve signed/history
artifacts and explicitly distinguish path reconciliation from new live approval.
Ordinary D0 portability; no CRITICAL admission or real exposure permission.

## Recovery / reporting
One immutable ID/branch/PR; preserve foreign work and current045history. Report
actual focused/full/static/CLI results, failures/skips/limits, current paths and
private changes structurally without secrets. No future PR/SHA/result. Report
publication SELF and exact implementationfirstparent; report-head checks unknown
at authoring remain mandatory. No hidden role resurrection or milestone claim.

## Deferred human adjudication
- Decision: NONE
