<!-- OAP-META
{
  "id": "041-a",
  "round": "a",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "cec4ed7c59dad30e841745a4842af397f40f3e0b",
  "issue_number": 81,
  "branch": "codex/81-oap-041-a-import-integrity",
  "pr_mode": "CREATE_OR_RESUME",
  "previous_round": null,
  "pr_number": null,
  "allowed_paths": [
    "src/slaif_reservation/legacy_import/importer.py",
    "tests/test_legacy_import_integrity.py",
    "tests/test_legacy_import.py (only integrity/rollback regressions)",
    "docs/audit/reports/M-INTERNET-UX-PILOT-cec4ed7.md (byte-identical frozen independent report only)",
    "oap/active",
    "oap/orders/041-a-import-integrity.md",
    "oap/reports/041-a-import-integrity.md"
  ],
  "forbidden_resources": [
    "Schema/models/migrations/dependencies/runtime/Compose/proxy/security/permissions/UI/inventory changes",
    "Import locking changes (separate F1 round), cache ownership fixes (separate F3 round), optional readiness refinement O1",
    "Real exposure/deployment/DNS/TLS/firewalls/private data/exports/secrets/lab/Neumann resources",
    "Valuable-source product tests, unowned cleanup, immutable orders/reports/audit rewrites/OAP machinery expansion"
  ],
  "requirements": [
    "SAR-007",
    "SAR-009",
    "SAR-029",
    "SAR-030"
  ],
  "decision_class": "D0",
  "target_gate": "M-INTERNET-UX-PILOT independent closure; real exposure remains human D2",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f8a8df265d4dd452969d4bee874045c8f8a8261f9c87c96ba4c049a7dddf320d",
    "PLAN.md": "b19219e2d727af5a9554e011ba45a786f1bb61f25c001011fc18006cae665d08"
  }
}
-->

# 041-a — truthful import integrity failures

One purpose: correct ICA F2 so an unexpected audit/import persistence failure
cannot become an APPLIED batch/reservation_conflict. Preserve the initial audit
unchanged as evidence; no other selected functionality is removed or deferred.

H: human M-INTERNET-UX-PILOT preservation of integrity/audit/PostgreSQL guarantees
and fresh independent audit/repair requirement. A: A-06/A-11, SAR-007/009/029/030.
E/I: exact merged base cec4ed7c59dad30e841745a4842af397f40f3e0b; full47 fresh native
ICA context /root/ica_internet_ux_cec4ed7, fork_turns=none; frozen report SHA256
2c148bbb6213a34fddb78299da3b2b0a35a53c03cb825aa6d0c1ec04c73c3305.
Actual audit CHECK failure was mislabeled conflict, batch APPLIED, imported0/
conflict1/error0; savepoint removed row artifacts but kept a successful batch.
All five exact-main CI jobs passed (CI37387624385/OAP37387624605,964 tests), which
did not cover this demonstrated fault. C: D0, DHA_NONE; architecture resolves
unknown-integrity behavior. F1/F3 remain separate required repairs, O1 optional.

## Scope and acceptance

1. Only a validated named reservation exclusion failure originating from the
   reservation insert may become reservation_conflict. Never translate arbitrary
   IntegrityError from audit, import-record persistence, batch or another stage.
   Unexpected failures propagate; the complete atomic apply must roll back its
   batch/reservations/audits/import records, including earlier successful rows.
   Retain benign preflight/revalidation conflict categories and safe final counts.
2. Add real PostgreSQL regression evidence: actual named exclusion exercised;
   actual audit CHECK failure and import-record CHECK failure propagate instead
   of returning APPLIED; multi-row second-failure rolls back first-row artifacts;
   unknown errors remain investigation errors. Real persistence/constraints are
   mandatory; mocks alone do not qualify. New negative tests must fail on the
   old behavior before implementation. Existing idempotency/stale plans/historical
   exception/policy/blackout/ordinary booking behavior remains intact.
3. Preserve docs/audit/reports/M-INTERNET-UX-PILOT-cec4ed7.md byte-identically from
   the frozen independent report after verifying its digest. Do not rewrite its
   results/context or present it as current closure after source changes.
4. During implementation use focused owned PostgreSQL tests. At the literal
   final implementation head and immutable report head require all five standard
   quality/test/security/container/oap-harness checks. No unchanged repeated full
   local suite; real final CI supplies it. Report honest old failures, focused
   results, unresolved F1/F3 and excluded O1. Full fresh architecture-to-new-main
   ICA is required after all repairs; this round is not milestone closure.
5. No model/schema/API/permissions/UX/dependency/deployment/locking/private-data
   changes. Ordinary booking translation is reviewed for reference but unchanged.
   Reuse its named constraint semantics where appropriate, while narrowing the
   catch boundary to the actual reservation insert. Preserve all authority,
   privacy/idempotency/audit/exclusion/protected-history boundaries.

Strongest reason against the change: a broader exception handler or weakened
validation could disguise corruption or break legitimate idempotent imports.
Use a narrow insert-specific classification boundary, actual database fault
injection, whole-batch rollback and existing import/booking checks. Lock inversion
and warm-cache qualification remain visibly pending in separate bounded rounds.

## Execution/publication

ROOT implements directly under the human shutdown/takeover instruction. No coding
client is started. Product tests use the qualified owned-source runner, explicit
owned PG17 URLs/settings and minimal role-cleared environment; never valuable
checkout tests or foreign project/resource cleanup. No real exports/secrets/hosts.

Branch codex/81-oap-041-a-import-integrity, CREATE_OR_RESUME issue81; actual PR
number is retrieved after creation, never invented. PR body uses Closes #81.
Commit/push final implementation then immutable report only with literal full
implementation head first parent and Report publication commit: SELF. Verify
actual report-only path/parent/remotePR identity; report-head CI is mandatory.
Conditional expected-head development merge only; no real deployment authority.

## Deferred human adjudication
- Decision: NONE
