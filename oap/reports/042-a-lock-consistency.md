<!-- OAP-META
{
  "kind": "report",
  "id": "042-a",
  "order_path": "oap/orders/042-a-lock-consistency.md",
  "order_sha256": "6c23b97adde33e8c93cb1a850a87b265e141f9c1294a9e36089fe3a805a34c14",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 83,
  "pr_number": 84,
  "branch": "codex/83-oap-042-a-lock-consistency",
  "implementation_head": "23e3f1844d69d4b9d2a51aa24f8a1c04fa96fe12",
  "base_sha": "3f153a97cc4d0377abbc08cdd9d8d2c03849e1a3",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "23e3f1844d69d4b9d2a51aa24f8a1c04fa96fe12",
    "runs": [
      {
        "run_id": 37401813443,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "test": "success",
          "security": "success",
          "container": "success"
        }
      },
      {
        "run_id": 37401813468,
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

# PostgreSQL domain/import lock consistency

Implementation head SHA: 23e3f1844d69d4b9d2a51aa24f8a1c04fa96fe12
Report publication commit: SELF

Result: COMPLETE for bounded lock consistency correction. ROOT directly executed
and reviewed under the human takeover; no coding client restarted. Not independent
closure, release/exposure authorization or a declaration of milestone completion.

## Changed boundary

Principal/asset data mutexes use PostgreSQL FOR NO KEY UPDATE: other data writers
and domain mutex holders still exclude one another, while FK KEY SHARE checks
can proceed. Cancel/release lock the authoritative reservation only, rather than
implicitly locking its joined owner. Admission/owner/staff/counter/policy/time/
exclusion/lifecycle/audit checks are unchanged.

Atomic import batches serialize at the existing LegacyImportRecord table using
SHARE ROW EXCLUSIVE before domain locks. All mapped candidate principals are
locked by primary key before all candidate assets, before per-record policy
processing. Input/report order is retained. Advisory overlap queries use the
asset mutex without later reservation/blackout row locks; current-state/key/hash/
policy/blackout/history revalidation remains. The041 insert-specific integrity
classification/complete rollback behavior is preserved.

## Actual PostgreSQL evidence

- New nine-case suite uses separate real connections, acquired SQL locks,
  owned backend pg_stat_activity lock waits and bounded events/joins; persistence
  is not mocked. Same-principal import/booking both orderings, multi-owner batch/
  booking, staff cancel/release/import, staff joined-owner/batch acquisition,
  reversed same-key batches, FK references/data mutex updates and policy-target
  retarget/booking are exercised with actual audit/domain/provenance accounting.
- Literal pre-fix3f153 application bytes were restored ONLY in an owned clone,
  leaving the valuable source unchanged. **9 failed,14.10s**: eight actual
  PostgreSQL deadlock-detected failures plus a blocked FK reference deadline.
  All threads were bounded and connections reaped. Old comparison pnsqryt1.
- Changed code: **9 passed,4.24s** in mdxwlord. Final focused preservation suite
  (lock order, legacy integrity/import/concurrency, reservation services and
  concurrency): **106 passed,17.17s**, ma8kcbmw. Covers existing counters,
  blackout/exclusion/lifecycle/history/idempotency and actual audit/record fault
  rollback. Early formatting errors corrected; final Ruff/mypy134/diff passed.
- Related-writer diagnosis first used an invalid rootless GPU policy target,
  which correctly failed model validation. Only the synthetic fixture was
  changed to a valid machine; its genuine policy FK/booking40P01 then reproduced.
  No validation was relaxed or product fix made beneath that first boundary.
- At literal final implementation head, CI37401813443 quality/test/security/
  container and OAP37401813468 oap-harness all SUCCESS. Testjob112070467970:
  **980 passed,1 warning,614.39s**. Full standard PostgreSQL/browser/proxy/TLS/
  abuse/Gunicorn/policy/recovery/branding/governance suite, pip-audit and actual
  container/production-render/static checks ran. No unchanged full local suite
  was repeated; exact final CI supplied it.

Primary compatibility contracts: [PostgreSQL17 locking](https://www.postgresql.org/docs/17/explicit-locking.html)
and [Django5.2 queryset locks](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update).
Actual database races and data-writer/FK tests qualify their use here.

## Scope and remaining gate

Seven implementation paths: two domain/import service files, real regression
module, existing test pause-seam guidance, TESTING navigation and ordered active/
order. No schema/models/migrations/dependencies/permissions/API meaning/UI/
inventory/runtime configuration/architecture/projection/law changes. All local
product operations used owned disposable sources/PG17/minimal explicit role-
cleared environments and exact cleanup; no real exports/data/secrets/hosts/
DNS/TLS/firewall/lab activity. Current lock design review covers actual create,
cancel/release, policy, blackout and import writers.

Strongest reason against merge: bulk prelocking/serialization extends contention
for mapped users/assets, and weakened locking could lose data/counter exclusivity
or produce another cycle. Actual independent user/asset UPDATE waits, successful
FK checks, stable counter/exclusion tests, all adapter invariants unchanged and
old-negative/new-positive real races address the demonstrated boundary. Large
real migration/cutover capacity is not qualified or authorized by synthetic tests.

The prior full independent audit remains immutable evidence for cec4ed7. Its F3
warm-cache image creation-provenance/cleanup finding is still a separate required
round. After all repairs, fresh FULL architecture-to-current-main ICA is mandatory;
repair-queue closure is insufficient. Optional readiness observation O1 is not
new scope. Report-head CI is not yet observed at authoring and remains mandatory
before conditional expected-head development merge. No real exposure authorized.

DHA operation: NONE.
