<!-- OAP-META
{
 "kind": "report",
 "id": "035-b",
 "order_path": "oap/orders/035-b-default-policy-review-closure.md",
 "order_sha256": "4a76eb305296657e552a9344d042055811c4990b2cd9e13ebce0b5b091c154f0",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 69,
 "pr_number": 70,
 "branch": "codex/69-oap-035-a-default-policy",
 "implementation_head": "f0497500fc889b5a223a5e5375f4ca2f9f633d8b",
 "previous_implementation_head": "a4c577722a6a5960bb73e2a01d78f178bcc8a295",
 "base_sha": "0a81b931a11e6598540c2a6071b1e99ee895499e",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "f0497500fc889b5a223a5e5375f4ca2f9f633d8b",
  "runs": [
   {
    "run_id": 37242655171,
    "workflow": "CI",
    "jobs": {
     "quality": "success",
     "test": "success",
     "security": "success",
     "container": "success"
    }
   },
   {
    "run_id": 37242655135,
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

# 035-b — Default-policy review closure

Implementation head SHA: f0497500fc889b5a223a5e5375f4ca2f9f633d8b
Report publication commit: SELF

Result: COMPLETE for the 035-b bounded acceptance (the single collected
corrective review round); development only, no deployment, no milestone
closure. Same objective/branch/base and PR #70 (issue #69) as 035-a, AMEND
mode; all 035-a acceptance and source/runtime bytes retained.

| Criteria | Final evidence |
|---|---|
| 1. Overlap-limit wording | Source semantics unchanged: a booking is rejected when the existing intersecting blocking count is >= 8 (`concurrent_count >= max_concurrent_per_principal` in `_enforce_policy`); stored cap 8 and every other default value intact. QUICKSTART step 7, INSTALL fresh step 9 and docs/human-ui now state that a new booking requires FEWER THAN 8 existing blocking records intersecting the proposed interval (8 or more existing intersecting records rejects it; the new record would be the 8th), still contrasted as a proposed-interval overlap count, not a maximum simultaneous-occupancy sweep. No source change. |
| 2. Race evidence | The timing-flaky barrier race was replaced by three deterministic event-gated orderings in tests/test_default_policy.py: (a) initializer-first — the configured global writer starts only after the initializer committed and is rejected by full_clean's active-global duplicate (specific non-field constraint error); (b) initializer-first interleaving — event gating holds the writer between validation and save while the initializer commits in between, so the final insert is rejected by the named `reservation_policy_one_active_global` unique constraint (verified via the DB error's `diag.constraint_name`); (c) configured-writer-first — the initializer starts only after the operator-global commit and must be a no-op. Only those two specific expected active-global conflicts are accepted; any other worker error is recorded and re-raised on the main thread (no silent thread exceptions, no broad `except Exception`). Bounded 30 s waits/joins, no fixed sleeps. Each ordering asserts the exact preserved row values and the single coupled creation audit (default actor NULL; configured actor = staff). Evidence: 18 passed in the focused file (owned PG17; three consecutive runs 5.27/5.26/5.36 s). The strategy-selected 150 ms probe failure (uncaught active-global ValidationError at literal a4c, then missing worker outcome `KeyError: 'global'`) is now deterministically covered by (a) and (b). |
| 3. Successor coverage wording | docs/governance/DEFAULT-POLICY-PROJECTION-REVIEW.md now reads "the other 46 clauses and sections" (one of the 47 SAR clauses changed by 035-a). Canonical ARCHITECTURE.md, ARCHITECTURE-for-agents.md and PLAN.md bytes remain exactly unchanged from 035-a (no diff this round); no hash churn, no machinery change. |
| 4. Evidence identity | oap/reports/035-a-default-policy.md preserved byte-identical. Its criterion-4 statement "Full owned suite at implementation head: 796 passed + 7 failures" is hereby superseded: that run was a pre-commit working-copy/untracked-snapshot run (the 5 https_boundary failures were exactly the untracked-snapshot artifact), not at the literal implementation SHA. Final full-suite evidence is literal-head CI: a4c5777 803 passed (388.52 s) and f049750 805 passed (416.63 s). No local full-suite pass is claimed in this round. Root fresh isolated pilot probes unchanged: preceding 5205296 (1 pass, 12.12 s) and candidate a4c (1 pass, 11.68 s) on separate owned DBs. Earlier local failures (wall-clock-time-sensitive chromium pilot path; oap-harness tmux prerequisite) are retained honestly as local-environment/time-sensitive observations, not product claims; CI at both exact heads passed. No machinery edit or CI bypass resulted from local OAP role/environment failures. |
| 5. Evidence order / CI | Focused corrected tests/docs first, then the full required exact-head CI: 5/5 jobs SUCCESS at f049750 (below). The 035-a report-head CI at 124bff0 (CI run 37241423210, oap run 37241423182) completed success and was neither cancelled nor waived. |

No application/initializer/domain/settings/schema/migration/dependency/
inventory/permission/network/branding source change; no token-scope, audit
or exclusion-constraint semantics change. Changed files, all within ordered
allowed paths: QUICKSTART.md, INSTALL.md, docs/human-ui.md,
docs/governance/DEFAULT-POLICY-PROJECTION-REVIEW.md,
tests/test_default_policy.py, oap/active, and the newly published
oap/orders/035-b-default-policy-review-closure.md (order bytes).

Commands and results (coding checkout; owned PG17 loopback via the 033-b
receipt; OAP_ROLE cleared in product-test child environments):
- Focused before: `uv run --env-file <033-b tests.env> pytest --ds=slaif_reservation.config.settings.test tests/test_default_policy.py -q` => 16 passed (4.82 s).
- Focused after: same command => 18 passed; three consecutive runs (5.27/5.26/5.36 s).
- Neighboring: same pytest over tests/test_operational_hardening.py tests/test_reservations_services.py tests/test_reservations_concurrency.py tests/test_migrations.py tests/test_default_policy.py => 107 passed (38.24 s).
- Quality gates: `uv run ruff check .` (all checks passed), `uv run ruff format --check .` (200 files), `uv run mypy src` (127 files, no issues), `manage.py check` (0 issues), `manage.py makemigrations --check --dry-run` (no changes detected), `manage.py spectacular --validate --fail-on-warn` (ok), `uv run pip-audit` (no known vulnerabilities), `git diff --check` (clean).

CI observed before authoring (exact implementation head f049750):
- CI run 37242655171: quality success, test success (805 passed, 416.63 s), security success, container success.
- oap run 37242655135: oap-harness success.
Prior exact-head CI (035-a implementation head a4c5777, observed in 035-a,
unchanged): CI run 37240318468 quality/test/security/container success
(803 passed, 388.52 s); oap run 37240318561 oap-harness success.
This publication commit's report-head CI is NOT YET OBSERVED AT AUTHORING;
publication checks go to the private execution receipt, never a rewrite of
this report.

Security, data, dependencies: no credentials, verifiers, peppers or private
data in this report; owned nonce-labeled loopback PG only; no real
deployment/exposure/DNS/TLS; no dependency or lock change; the only
publication is the Git development push to the existing private branch.

DHA: NONE (order declares `Decision: NONE`, retained). Coding did not merge,
self-approve or enable auto-merge; the development merge gate and the fresh
isolated all-47 ICA at the exact merged revision remain separate.

Remote identity verified at authoring: PR #70 OPEN and MERGEABLE on
ulfe-lmi/slaif-asset-reservation, headRefOid =
f0497500fc889b5a223a5e5375f4ca2f9f633d8b (= implementation head), base main
@ 0a81b931a11e6598540c2a6071b1e99ee895499e.
