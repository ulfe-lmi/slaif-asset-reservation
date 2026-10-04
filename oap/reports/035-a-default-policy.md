<!-- OAP-META
{
 "kind": "report",
 "id": "035-a",
 "order_path": "oap/orders/035-a-default-policy.md",
 "order_sha256": "1353838c0311e77c8a88ba836cbed3f1ae1242501f1c9c0978940dbde3a5b4a1",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 69,
 "pr_number": 70,
 "branch": "codex/69-oap-035-a-default-policy",
 "implementation_head": "a4c577722a6a5960bb73e2a01d78f178bcc8a295",
 "base_sha": "0a81b931a11e6598540c2a6071b1e99ee895499e",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "a4c577722a6a5960bb73e2a01d78f178bcc8a295",
  "runs": [
   {
    "run_id": 37240318468,
    "workflow": "CI",
    "jobs": {
     "quality": "success",
     "test": "success",
     "security": "success",
     "container": "success"
    }
   },
   {
    "run_id": 37240318561,
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

# 035-a — Fresh-install default reservation policy

Implementation head SHA: a4c577722a6a5960bb73e2a01d78f178bcc8a295
Report publication commit: SELF

Result: COMPLETE for 035-a bounded acceptance; development only, no
deployment, no milestone closure. Direct implementation is not independent
ICA; the fresh isolated all-47 ICA at the exact merged revision remains
required.

| Criteria | Final evidence |
|---|---|
| 1. Trusted command | New `initialize_default_policy` command (reservations app; dedicated `initialization.py`); registered as required in `config/operational.py`; mandatory immediately after migrate in QUICKSTART step 3, INSTALL section 5 step 7 and section 9 upgrade note, both rehearsal scripts and CI. No HTTP route, no AppConfig/worker startup call, no data migration (`makemigrations --check --dry-run`: no changes). No allow_system staff bypass added to `create_policy`. |
| 2. Exact defaults / no-op | Only when NO policy rows exist: active global `default` (asset NULL; 1..2880 min; START horizon 7d; lead 0; cutoff 0; purpose optional; no operating-hour window; 50 upcoming / 8 proposed-interval overlap per principal across assets and tokens). Any prior configuration (active/inactive, global/specific) => no writes, no audit, no reactivation. Proven by 16 real-PG tests including exact-defaults, active-global, inactive-global, asset-specific, repeat. |
| 3. Atomicity / races | Single EXCLUSIVE-mode PostgreSQL table lock serializes absence+insert against ordinary policy inserts and concurrent initializers; active-global unique constraint retained. 4-thread concurrency => exactly 1 policy + 1 audit; races vs configured-specific and vs active-global insertion preserve every pre-existing row with coupled per-row creation audits. Audit coupling uses existing `reservation_policy.created`, actor NULL, source admin, fresh correlation, safe metadata; audit failure rolls back policy + audit (tested). |
| 4. Real PG + Docker | Focused: 16 passed (`tests/test_default_policy.py`, owned PG17, incl. real accepted booking, duration/horizon/lead/upcoming-50/overlap-8 limits, start-at-now). Neighboring suites: 105 passed. Full owned suite at implementation head: 796 passed + 7 failures all analyzed (below). Fresh owned Docker rehearsal from a tracked-file snapshot at the implementation head (shipped commands, pinned postgres:17, loopback 34490): migrate, init created, init repeat skipped, sanitized bootstrap 47/47, synthetic administrator, real accepted booking, psql-level assertions (policy row exact defaults; 1 policy audit actor NULL; 1 confirmed reservation + audit) — `fresh-rehearsal=ok`, owned cleanup verified. Shipped internal-alpha full rehearsal (real Docker, project/port/image nonce-owned, loopback 18090): initializer `status=created` after migrate, `operational_check=ok` (new command required), app started non-root, health/login/API-auth checks, `rehearsal=ok`; boundary rehearsal suite 10 passed (382.83s). |
| 5. Operator docs | QUICKSTART (init in step 3; step 7 now documents actual defaults, upgrade no-op, `/manage/` management), INSTALL (fresh step 7 + step 9 defaults; upgrade section no-op + explicit empty-upgrade init; troubleshooting), `docs/deployment.md` Migrations (initializer is deliberate, not a migration), `docs/human-ui.md` (default values in create-reservation behavior). Manual fresh-policy prerequisite replaced; priority/ambiguity fail-closed retained. No work-ledger or Internet/production qualification claim. |
| 6. Governance | Exact A-15 paragraph replacement applied (old paragraph starts "A supported fresh initialization path", ends "real booking."); exact compact SAR-041 clause; projection header carries the ACTUAL post-amendment full-source SHA-256 `f8a8df265d4dd452969d4bee874045c8f8a8261f9c87c96ba4c049a7dddf320d`. All SAR-001-040/042-047 clauses and sections byte-identical (clause-level diff); PLAN.md unchanged (`b19219e2...`). Successor mapping/context review at `docs/governance/DEFAULT-POLICY-PROJECTION-REVIEW.md`; historical 032 coverage preserved. Measured: projection 19979 <= 20000 bytes; routine read set 34902 <= 50000 bytes; wider sum 41897 <= 50000; no truncation. |
| 7. Checks / PR / report | Quality gates at implementation head: ruff check/format, mypy, check, makemigrations --check, spectacular --validate --fail-on-warn, pip-audit, git diff --check all clean. Five exact-head CI jobs SUCCESS (run 37240318468: quality/test/security/container; run 37240318561: oap-harness). PR #70 opened for issue #69 with Closes #69. Coding did not merge. |

Local full-suite failures (7) and their disposition: five
`tests/test_https_boundary.py` failures occurred only in the pre-commit
owned run because the boundary rehearsal builds its image from a
git-tracked snapshot while the new files were still untracked locally;
after commit/fetch/align at the implementation head the suite passed
10/10 (382.83s). `test_pilot_path.py::test_integrated_pilot_path_shared_state_across_surfaces[chromium]`
reproduced identically on clean base 0a81b93 (wall-clock time-sensitive
availability-display assertion; fails at 23:58/23:59/00:28 local, passes
in the CI test job at the implementation head) — pre-existing, outside
035-a allowed paths, not amended. `tests/oap/test_ba38_39_tmux_config.py::
Ba39OperationPrereqs::test_ba39_strategic_same_prerequisites` reproduced
identically on clean base (launcher print-only prerequisite in this
environment); the dedicated oap-harness CI job at the implementation head
passed. No in-scope defect remains unfixed at the implementation head.

No model/schema/dependency/inventory change; no old migration touched;
no token scope, permission, audit or exclusion-constraint change. The
initializer is additive application code plus operator-path/docs updates.
Strongest objection: a default policy could undo deliberate disabling —
mitigated by preserving ANY prior policy configuration (no writes/audit/
reactivation), explicit trusted operator invocation only, and the
serialized absence/rollback/upgrade-negative proofs above. Real exposure
remains the human D2 boundary; SAR-041 stays UNPROVEN until the fresh
isolated all-47 ICA at the exact merged revision. D0/DHA NONE.
