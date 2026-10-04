<!-- OAP-META
{
 "kind": "report",
 "id": "034-b",
 "order_path": "oap/orders/034-b-baseline-fixture-closure.md",
 "order_sha256": "3ac29a113bcdd573002bdf40b1240c3a65a14384e9d206e4feb1cf4bd1ff5610",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 67,
 "pr_number": 68,
 "branch": "codex/67-oap-034-a-shared-abuse-controls",
 "implementation_head": "914f0630bdc6ff63f3c8fcf30bbf8dfdc98b6b7a",
 "base_sha": "f8430fa14e0f53339f7c1e1427fe52a3fa56ba7e",
 "result": "PARTIAL",
 "observed_implementation_ci": {
  "observed_head": "914f0630bdc6ff63f3c8fcf30bbf8dfdc98b6b7a",
  "runs": [
   {
    "run_id": 37232565415,
    "workflow": "CI",
    "jobs": {
     "quality": "success",
     "test": "success",
     "security": "success",
     "container": "success"
    }
   },
   {
    "run_id": 37232565401,
    "workflow": "oap",
    "jobs": {
     "oap-harness": "success"
    }
   }
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 034-b — Baseline fixture closure

Implementation head SHA: 914f0630bdc6ff63f3c8fcf30bbf8dfdc98b6b7a
Report publication commit: SELF

Result: PARTIAL pending the final collected review correction. The four API
adapter tests now use real DB fixtures; the production body-limit test uses
an owned migrated DB, preserving small200/large400/CSRF/real Gunicorn checks;
HTTPS administration collects its production manifest in an owned directory.
Focused formerly failing cases:6 passed in13.88s. No protection or assertion
was disabled. Exact implementation CI37232565415/37232565401: all five jobs
SUCCESS; full CI787 passed in368.32s, no skips.

Owned local full suite at the same head:786 passed/1 failed in609.94s.
The token browser test read an empty page immediately after navigation;
focused unchanged retry passed in7.13s. This is a synchronization defect,
not evidence of lost token data. Final review also found the new explicit
OpenAPI create success response incorrectly says200 while actual creation
and replay return201. A single next correction will restore201 contract,
assert it, and wait for the token list before reading it. No merge yet.

All034-a/b shared counter, real proxy/process, expiry/failure and mutation
negative evidence remains applicable. Direct human-authorized implementation
and review are not ICA. No dependency, old migration, reservation authority,
permissions or inventory changed. Counter migration is additive; application
rollback requires keeping its table until matching code is restored. Strongest
objection remains DB contention/NAT interference, bounded and documented by
configurable shared quotas and connection/statement/lock waits. D0/DHA NONE;
real exposure and final independent milestone audit remain separate.
