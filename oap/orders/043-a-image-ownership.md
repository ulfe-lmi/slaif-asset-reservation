<!-- OAP-META
{
  "id": "043-a",
  "round": "a",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "fcaec5c2ee11c4599d714a762ae04e4fb0c67642",
  "issue_number": 85,
  "branch": "codex/85-oap-043-a-image-ownership",
  "pr_mode": "CREATE_OR_RESUME",
  "previous_round": null,
  "pr_number": null,
  "allowed_paths": [
    "tests/test_branding.py (owned image build/receipt/cleanup only; app assertions preserved)",
    "tests/test_qualification_image_ownership.py",
    "TESTING.md (image construction provenance qualification only)",
    "oap/active",
    "oap/orders/043-a-image-ownership.md",
    "oap/reports/043-a-image-ownership.md"
  ],
  "forbidden_resources": [
    "Product source/schema/models/migrations/dependencies/runtime/Compose/proxy/permissions/UI/inventory changes",
    "Ownership/foreign protection weakening, arbitrary old-image or label-only adoption, cache pruning/project-wide cleanup",
    "Immutable history/audit rewrite/new OAP machinery",
    "Real exposure/hosts/DNS/TLS/firewall/private data/exports/secrets/lab/Neumann access",
    "Valuable-checkout product tests/reset/clean/forcepush"
  ],
  "requirements": [
    "SAR-031",
    "SAR-032",
    "SAR-045"
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

# 043-a — cached image construction ownership

One purpose: correct ICA F3 qualification image receipt/cleanup while retaining
all real branding/application checks and foreign resource protections.

H: human safe disposable qualification and no-rebuild operator branding.
A: A-10/A-15,SAR-031/032/045. E/I: frozen full ICA cec4ed7 reportSHA
2c148bbb6213a34fddb78299da3b2b0a35a53c03cb825aa6d0c1ec04c73c3305 F3:
canonical warm-cache image refuses Created older than attempt before app startup,
then lacks receipt/cleanup; two owned images verified/cleaned by auditor, cold
qualification passed. ROOT43 image-provenance investigation: layered cached
builds with unique tags/nonces/IID outputs produce distinct immutable IDs while
Created is identical/older on second attempt (1PASS6.16s, exact cleanup).
An initial empty-scratch fixture lacked Created and had different image/config
IDs; it is not a product defect or permission to accept missing metadata.
Base fcaec5c2ee11c4599d714a762ae04e4fb0c67642/PR84 closed83, all5 implementation/
report CI successful/full980 tests. C:D0,DHA_NONE; ownership invariant is settled.

## Acceptance

1. Keep runtime object (container/network/volume) nonce/ID/fresh creation and
   changed-receipt refusal exactly strong. Image content Created is not tag/build
   attempt birth: accept only a known local trusted build with previously-absent
   unique tag, correct nonce, successful generated build-output ID, matching
   immutable image identity and recorded Created. No arbitrary old image,
   labels-only/name-only adoption, foreign tag overwrite or missing/invalid
   metadata. Build output files are owned/local/bounded; refuse malformed/
   stale/symlink or mismatched provenance. Do not generalize to unsupported
   image formats just for the empty-scratch diagnostic.
2. Register exact receipt before later qualification assertions so a failure
   after successful build cleans only that image. No speculative cleanup after
   an early failed build with no proven artifact. Finally must not re-adopt an
   unreceipted foreign image by name or repeat the invalid freshness assumption.
   Revalidate immutable ID/nonce/recorded Created; no forced foreign/tag/cache
   deletion or blanket prune/down. Preserve all existing safety controls.
3. Real Docker warm-cache-repeat regression with distinct owned nonces/tags:
   unchanged layer Created before second attempt must still qualify known build
   output/identity and cleanup. Preserve foreign sentinels/cache/resources.
   Exercise failure after build, early failure without artifact, stale tag/output,
   wrong nonce/ID/changed receipt and creation-race refusal meaningfully; fake
   tests prove helper contracts only, real Docker proves actual metadata/cleanup.
4. Run actual production-shaped same image default then read-only custom branding
   qualification on a warmed host: existing no-rebuild/default/custom/CSS-last/
   malformed-slot fallback/non-root/private-DB/loopback/read-only assertions must
   remain. Do not make tests green by weakening application checks or skipping.
   No app/runtime change beneath the demonstrated pre-start harness boundary.
5. Focused safety tests during edits; all five standard CI jobs at final literal
   implementation and immutable report heads mandatory. No unchanged repeated
   full local suite. Report actual failures/results/resource cleanup/limits;
   fresh FULL47 architecture-to-current-main ICA after this merge remains required,
   not merely finding closure or reuse of old target/audit statuses.

Strongest reason against change: relaxing Created age for arbitrary images could
adopt/delete a foreign cached image. Bind only trusted successful construction
output and previously-absent owned tag/nonce to immutable ID, retain Created
identity revalidation and runtime birth guards, and test negative/failure cleanup
on actual cached Docker. Bounded qualification helper change, no new framework.

## Execution/publication

ROOT directly under human takeover; no coding client. All real product/container
operations use owned sources/minimal role-cleared environment/local Unix Docker
and nonce/ID/creation receipts; never valuable source/unowned deletion. Existing
PG17 ownership exact-ID/nonce checked when needed. No real data/secrets/exposure.

Branch codex/85-oap-043-a-image-ownership CREATE_OR_RESUME issue85; actual PRnumber
retrieved after creation, never guessed. Closes #85 in PRbody. Final head source
review/all5CI then immutable report-only literal firstparent/SELF; verify actual
remote/PR/report identity, requireall5reportCI and protected development merge.
Full independent audit/publication/freshness/quiescence and exact human D2
candidate presentation remain; no deployment authorization or milestone closure.

## Deferred human adjudication
- Decision: NONE
