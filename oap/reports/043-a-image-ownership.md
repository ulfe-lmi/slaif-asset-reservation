<!-- OAP-META
{
  "kind": "report",
  "id": "043-a",
  "order_path": "oap/orders/043-a-image-ownership.md",
  "order_sha256": "384dd31ae9026d2985cd4e22fc1197d0d72ed24a132f2c85b8993f674589c432",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 85,
  "pr_number": 86,
  "branch": "codex/85-oap-043-a-image-ownership",
  "implementation_head": "ae0c5b9cd8c5f8a6071d078cb1fa25aa3b808950",
  "base_sha": "fcaec5c2ee11c4599d714a762ae04e4fb0c67642",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "ae0c5b9cd8c5f8a6071d078cb1fa25aa3b808950",
    "runs": [
      {
        "run_id": 37508015353,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      },
      {
        "run_id": 37508015412,
        "workflow": "CI",
        "jobs": {
          "security": "success",
          "quality": "success",
          "container": "success",
          "test": "success"
        }
      }
    ]
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# Cached image construction ownership

Implementation head SHA: ae0c5b9cd8c5f8a6071d078cb1fa25aa3b808950
Report publication commit: SELF

ROOT executed this bounded qualification correction under the human takeover;
no coding client restarted. COMPLETE concerns this order, not independent
milestone closure or exposure authorization.

## Acceptance evidence

1. Images are bound to a successful local build, a bounded fresh owned regular
   nofollow IID output, exact immutable image ID, unique nonce and recorded
   Created. The reserved unique name is checked absent before/after construction;
   no tag is assigned, so a racing foreign name cannot be overwritten. Cached
   content Created is accepted only through this construction proof. Runtime
   container/network/volume freshness controls remain unchanged.
2. Receipt registration precedes later name/application assertions. Failure after
   construction cleans the proven immutable ID. Early failure with no artifact
   causes no speculative adoption/deletion. Changed nonce/Created or named image
   references refuse cleanup; no force image deletion or cache pruning.
3. Focused ownership tests: **16 passed in 5.81s**, owned source am_74vzs.
   Fake contracts cover malformed/stale/symlink output, wrong ID/nonce,
   missing/naive Created, named/pre-existing/racing foreign references and
   changed-receipt cleanup. They prove helper contracts only. Real Docker builds
   twice with distinct nonces/IDs on cached content; second Created precedes its
   attempt and matches the first. A deliberate real post-build failure cleans
   only the exact receipted image. Both IDs are absent afterward.
4. Final real production-shaped branding test: **1 passed in 55.87s**, owned
   source zx3snary. Default and read-only custom branding use the same immutable
   image without rebuilding; all original application/CSS-last/fallback/non-root/
   private-DB/loopback/read-only/foreign-sentinel assertions remain. No skip.
   Earlier focused runs: 15 passed in 6.10s; expanded branding/ownership set
   81 passed in 64.89s; final ownership guard run 16 passed as above. Ruff,
   format, mypy (134 source files) and diff checks passed. No repeated unchanged
   full local suite; final exact-head CI supplies the required full checks.
5. Exact implementation CI37508015412 and OAP37508015353 passed all five jobs.
   Full test job112421531858: **996 passed,1 warning in 610.83s**.
   Exact implementation CI is recorded in metadata after independent observation.
   Report-head checks are not yet observed at authoring and remain mandatory.
   Fresh FULL architecture-to-current-main independent audit remains required.

## Scope and limits

Five implementation paths: TESTING.md, tests/test_branding.py,
tests/test_qualification_image_ownership.py and the exact order/active pointer.
No application, runtime/Compose/proxy, schema/migration, dependency, permission,
UI, inventory, architecture/projection/law bytes changed. Test resources used
owned disposable source snapshots, nonce/ID receipts and minimal explicit
role-cleared environments; no valuable-checkout product tests, foreign cleanup,
private data/secrets, real hosts/exposure/DNS/TLS/firewall/lab operations.

The initial ICA F3 failure remains historical evidence in the preserved cec4ed7
report; it is not rewritten or independently reclassified by this correction.
The real warm repeat now demonstrates the previously failing boundary. Empty
scratch images without Created are not accepted solely to satisfy a diagnostic;
the regression uses a real payload layer like the supported application build.

Strongest reason against change: removing an image age guard could adopt/delete
foreign cached content. Construction-only proof, nonce/immutable-ID/Created
revalidation, refusal of named references, unchanged runtime birth guards and
real/fake negative cleanup evidence constrain that risk. No arbitrary old image
is adopted by name/label alone. New independent FULL47 audit, publication,
freshness and final quiescence remain; no real deployment is authorized.

DHA operation: NONE.
