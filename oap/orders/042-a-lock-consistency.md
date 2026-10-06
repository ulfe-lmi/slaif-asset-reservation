<!-- OAP-META
{
  "id": "042-a",
  "round": "a",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "3f153a97cc4d0377abbc08cdd9d8d2c03849e1a3",
  "issue_number": 83,
  "branch": "codex/83-oap-042-a-lock-consistency",
  "pr_mode": "CREATE_OR_RESUME",
  "previous_round": null,
  "pr_number": null,
  "allowed_paths": [
    "src/slaif_reservation/legacy_import/importer.py (locking only; preserve041 integrity fix)",
    "src/slaif_reservation/reservations/services.py (locking only; preserve all authority/domain checks)",
    "tests/test_import_lock_order.py",
    "tests/test_legacy_import_concurrency.py (accurate pause-seam guidance/regressions only)",
    "TESTING.md (focused locking evidence/navigation only)",
    "oap/active",
    "oap/orders/042-a-lock-consistency.md",
    "oap/reports/042-a-lock-consistency.md"
  ],
  "forbidden_resources": [
    "Schema/models/migrations/dependencies/production settings/Compose/proxy/UI/permission/inventory changes",
    "Cache ownership F3 changes; optional readiness O1; immutable audit/history rewrites",
    "Real exposure/production/private exports/data/secrets/DNS/TLS/firewall/lab/Neumann work",
    "Valuable-source product tests/unowned cleanup/forcepush/new OAP machinery"
  ],
  "requirements": [
    "SAR-007",
    "SAR-008",
    "SAR-009",
    "SAR-020",
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

# 042-a — consistent PostgreSQL domain/import locking

One purpose: remove demonstrated domain/import lock cycles while preserving
transactional reservation authority and all existing selected guarantees.

H: human milestone preservation of exclusion/policy/audit/management/private
migration boundaries plus fresh ICA repair requirements. A: A-06/A-11 and
SAR-007/008/009/020/029/030. E/I: frozen independent audit cec4ed7 reportSHA
2c148bbb6213a34fddb78299da3b2b0a35a53c03cb825aa6d0c1ec04c73c3305 F1;
real same-principal40P01; ROOT owned additional real-PG staff cancellation and
multi-owner batch cycles (042-lock-investigation.json); valid-machine policy
retarget/booking FK cycle40P01 (042-policy-reference-investigation.json).
Initial policy probe's invalid rootless GPU was rejected by model validation;
only the synthetic fixture was corrected, never validation. Exact merged base
3f153a97cc4d0377abbc08cdd9d8d2c03849e1a3/PR82, issue81closed; all5 literal
implementation/report CI successful,971 tests. C: D0,DHA_NONE. No new product
rights/meaning/exposure judgment: canonical consistent locking resolves the duty.

## Acceptance and chosen bounded design

1. Preserve admission, owner/staff authority, policy resolution/counters,
   blackout/exclusion/lifecycle rules, audit coupling, protected history and041
   named INSERT-only integrity behavior. No silent deadlock retries or error
   masking. No privilege/validation relaxation or new adapter/product feature.
2. Domain principal/asset data mutexes remain mutually exclusive with data
   updates/other domain writers while allowing nonmutating FK KEY_SHARE checks
   (PostgreSQL FOR NO KEY UPDATE where appropriate). Restrict lifecycle row
   locking to the authoritative reservation, avoiding joined-owner locks that
   can invert multi-owner ordering. Review actual create/cancel/release/policy/
   blackout/import write paths; do not change a single adapter blindly.
3. Import apply acquires all mapped candidate principals deterministically
   before candidate assets, before policy/record processing. Serialize apply
   batches at the existing import-record boundary where necessary to avoid
   reversed batch/key ordering; preserve input/report order and atomic batch.
   Advisory overlap queries under the asset mutex must not acquire conflicting
   reservation/blackout row locks after asset ownership. Revalidation remains
   authoritative, including inactive/deleted users/assets, policy/blackout/current
   reservations, existing keys/changed hashes and historical exception bounds.
4. Real PostgreSQL regressions must fail against old behavior before changes,
   then prove bounded nondeadlocking results and transactional/audit accounting:
   same-principal create/import both orderings; staff cancel/release/import;
   multi-owner/multi-asset batch against ordinary booking; same-key/reversed
   concurrent imports; actual policy-target FK race. Gates must observe real
   acquired/blocked backend locks, not mock DB persistence or force impossible
   post-fix Python barriers. Threads/connections/resources must be bounded/reaped.
   Preserve existing booking/blackout/counter/concurrency/idempotency tests.
5. Prove the selected mutex mode still blocks ordinary data changes/concurrent
   owner counters; actual FK references can proceed without the demonstrated
   cycle. No FOR SHARE substitution/unlocked quota checks. Real PostgreSQL
   exclusion remains final arbiter;041 actual audit/record fault rollback tests
   must still pass. Test batch repetition/configuration/stale plans truthfully.
6. Focused owned tests during edits; full five standard CI jobs at literal final
   implementation and immutable report heads mandatory. No unchanged repeated
   full local suites. Report actual old failures/focused results/limits and the
   still-required F3/full new-main ICA. Do not self-certify milestone closure.

Primary technical contract: PostgreSQL17 explicit-locking row compatibility
https://www.postgresql.org/docs/17/explicit-locking.html and Django5.2
select_for_update(of/no_key) https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update.

Strongest reason against change: incorrectly weakened locks or incomplete batch
ordering could permit stale/counter violations or introduce another cycle; bulk
prelocking also extends contention for mapped users/assets. Keep data mutex
exclusivity, all validators/authority and atomicity, test actual conflicting
writers/FK compatibility/batches/lifecycle across adapters, preserve legacy
cutover restrictions and qualify exact heads independently after all repairs.

## Execution/publication

ROOT direct implementation under explicit human takeover; no coding clients.
Use owned source/PG17 exact nonce/ID receipt and minimal explicit role-cleared
settings/URLs. Never tests in valuable source, real exports/hosts/secrets or
unknown deletion. No schema/stack/runtime/policy meaning change; canonical
architecture/projection need no rewrite unless demonstrated inconsistency.

Branch codex/83-oap-042-a-lock-consistency CREATE_OR_RESUME, actual issue83;
actual PRnumber retrieved after creation, never guessed. Closes #83 in PRbody.
Only after final all5 implementation CI, report-only commit literal full first
parent and SELF; verify3 actual remote/PRidentity and all5 reporthead CI.
Conditional expected-head development merge only. F3 and fresh FULL47 audit/
publication/freshness/quiescence remain; no real deployment authorization.

## Deferred human adjudication
- Decision: NONE
