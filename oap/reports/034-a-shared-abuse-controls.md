<!-- OAP-META
{
 "kind": "report",
 "id": "034-a",
 "order_path": "oap/orders/034-a-shared-abuse-controls.md",
 "order_sha256": "03cbfb10331aa04b0e382fd3f4335bfe3099588a1697d0223f9387c5b407e36e",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 67,
 "pr_number": 68,
 "branch": "codex/67-oap-034-a-shared-abuse-controls",
 "implementation_head": "2d09a862d0d0b8d763e289292a1f5d841d4c45b6",
 "base_sha": "f8430fa14e0f53339f7c1e1427fe52a3fa56ba7e",
 "result": "PARTIAL",
 "observed_implementation_ci": {
  "observed_head": "2d09a862d0d0b8d763e289292a1f5d841d4c45b6",
  "runs": [
   {
    "run_id": 37229237880,
    "workflow": "CI",
    "jobs": {
     "quality": "success",
     "test": "failure",
     "security": "success",
     "container": "success"
    }
   },
   {
    "run_id": 37229237974,
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

# 034-a — Shared abuse controls (partial)

Implementation head SHA: 2d09a862d0d0b8d763e289292a1f5d841d4c45b6
Report publication commit: SELF

Result: PARTIAL. Direct implementation under the human takeover instruction;
no merge or deployment. PostgreSQL HMAC/fixed-window counters, shared
member/admin login budgets, pre-auth API and account/token budgets,429/503,
bounded SQL/connection waits, cleanup and operator docs are implemented.
Focused integration/settings:120 passed; separate mutation/replay/audit
coupling:1 passed. Real TLS/Gunicorn tests prove worker scaling, forwarding
spoof rejection, multi-token account budgets, valid login and DB failure.

Full owned-source/PG17 run at this head:781 passed/6 failed in651.84s. Exact
CI37229237880 has the same six failures; quality/security/container succeed,
oap37229237974 succeeds. Failed boundaries:

- Three older API-root/schema tests and one proxy-security adapter test need
  real DB fixtures now that every API request uses shared counters. No
  production bypass or weaker response assertion is appropriate.
- The real production body-limit test deliberately points at a dead DB;
  its small login control now correctly returns503. It needs an owned
  migrated PG fixture to retain the original small200/large400 proof.
- The real TLS admin-login fixture uses production static manifests; clean
  checkouts need a test-owned collectstatic before exercising administration.

These are collected for one corrective round on PR68. No old migration,
dependency, reservation authority, scope, owner privacy or inventory changed.
New migration0002_abusebucket depends explicitly on existing0002_response
headers; Django orders the graph by names/dependencies, and fresh owned
migrate/makemigrations-check pass. A setup invocation without explicit owned
env attempted generic dev authentication at foreignlocalhost5432 and was
rejected before data access; all subsequent DB commands use the owned
PG17 environment and no foreign data was read or modified.

Acceptance1–4 implemented with focused evidence;5 incomplete because full
regression fails;6 docs updated. D0/DHA NONE. Strongest reason against merge:
full exact-head checks are not green. Remaining selected milestone, fresh
independent audit and human D2 exposure remain mandatory.
