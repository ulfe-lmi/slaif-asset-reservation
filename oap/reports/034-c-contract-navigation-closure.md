<!-- OAP-META
{
 "kind": "report",
 "id": "034-c",
 "order_path": "oap/orders/034-c-contract-navigation-closure.md",
 "order_sha256": "47a6c099e8556ccd1b80503fd2215acdc12377da4cb598c1847945500cac21f4",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 67,
 "pr_number": 68,
 "branch": "codex/67-oap-034-a-shared-abuse-controls",
 "implementation_head": "5205296eaa620e7c164d2075c2d25f3c1b51280d",
 "base_sha": "f8430fa14e0f53339f7c1e1427fe52a3fa56ba7e",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "5205296eaa620e7c164d2075c2d25f3c1b51280d",
  "runs": [
   {
    "run_id": 37236687886,
    "workflow": "CI",
    "jobs": {
     "quality": "success",
     "test": "success",
     "security": "success",
     "container": "success"
    }
   },
   {
    "run_id": 37236687662,
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

# 034-c — Shared abuse-control closure

Implementation head SHA: 5205296eaa620e7c164d2075c2d25f3c1b51280d
Report publication commit: SELF

Result: COMPLETE for034-a/b/c bounded acceptance; no deployment or milestone
closure. Direct human-authorized implementation/review is not independent ICA.

| Criteria | Final evidence |
|---|---|
| Login | Common source30 and normalized identity10 attempts/300s for member/admin; real TLS valid/invalid login, route/case quota sharing and recovery; no account flags/password changed. |
| API | Source1200, owner600, token300/60s; invalid/missing bearer bounded pre-auth, multi-token owner budget, stable429/503/correlation/Retry-After/no-store; idempotent replay and denied mutation/audit coupling tested. |
| Shared storage | Atomic real PG UPSERT,30 concurrent attempts/12 connections allow exactly5, real1/3-worker TLS tests and spoof negatives; scoped HMAC/no raw identities, saturated counts;5s connection default/1s lock/2s statement bounds. |
| Expiry/failure | Fixed windows recover, expired-only bounded cleanup/default dry-run CLI; actual unavailable DB denies protected paths503 while liveness works; held-row timeout/recovery. |
| Compatibility | Formerly DB-free API tests use real fixtures, body test retains real Gunicorn/CSRF/small200/large400, production admin manifest owned. Schema creation retains actual201 with429/503; browser token navigation waits on rendered heading without removing secrecy/revoke assertions. |
| Checks/docs | All five final implementation jobs SUCCESS; full CI787 passed/no skips436.82s. Docs/config/ADR explain rates/NAT/fixed-window bursts/cleanup/fail-closed and perimeter limits. |

Final exact-head runs37236687886/37236687662 execute locked install, lint/
format/types/diff, real PG migrations/check/schema/operational commands, full
pytest including browsers/concurrency/restore/Gunicorn/HTTPS, pip-audit,
Compose renders/non-root image build/static checks, and OAP harness. Focused
schema/browser correction:11 passed in8.09s. Final owned local full run is
PENDING at authoring, not claimed successful; exact implementation CI supplies
the full-suite pass. Prior b local786 passed/1 timing failure and unchanged
retry1 pass are retained as failures/retry evidence, not rewritten. Earlier
034-a six fixture failures were corrected together in b; its immutable PARTIAL
report remains. Prior report b exact-head checks subsequently all succeeded.

No dependency, old migration, reservation authority, token scope, inventory
or permission change. Additive AbuseBucket table migration preserves existing
schema/history. Application rollback keeps this table until matching code is
restored. Strongest objection: shared counters can add DB contention/NAT
interference and are not distributed DDoS immunity. Atomic bounded work and
configurable documented rates mitigate this selected application control;
operator perimeter protection/host trust remain required. Remaining default
policy/UI/theme/final qualification/fresh independent all47 ICA are not covered
by this objective. D0/DHA NONE; real exposure remains the human D2 boundary.
