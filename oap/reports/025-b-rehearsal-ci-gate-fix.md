<!-- OAP-META
{
 "kind": "report",
 "id": "025-b",
 "order_path": "oap/orders/025-b-rehearsal-ci-gate-fix.md",
 "order_sha256": "9791f141a99621c7f7cc7a1089223df2e3247fb5cc27783648011cfaf2fecdab",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 49,
 "pr_number": 50,
 "branch": "codex/49-oap-025-a-deployment-qualification",
 "implementation_head": "d963cb4feb16cf6227a79c8c19a7f854b3bedc8f",
 "base_sha": "e94d95e985412f9fc2fa27508be6ae36d606c4ce",
 "result": "PARTIAL",
 "observed_implementation_ci": {
  "observed_head": "d963cb4feb16cf6227a79c8c19a7f854b3bedc8f",
  "runs": [
   {"run_id": 35175090402, "workflow": "CI", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success", "deployment-rehearsal": "skipped (event-gated by design on pull_request)"}},
   {"run_id": 35175090387, "workflow": "oap", "event": "pull_request", "jobs": {"oap-harness": "success"}},
   {"run_id": 35175097161, "workflow": "CI", "event": "workflow_dispatch", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success", "deployment-rehearsal": "skipped (zero steps; DAG inconsistent with the pushed workflow bytes — root-cause analysis in section 4; the one permitted dispatch, so criterion 3 is NOT PRODUCED this round)"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 025-b report — Rehearsal CI gate fix: event-gated full-rehearsal job (correction of 025-a criterion 7)

Order digest: `9791f141a99621c7f7cc7a1089223df2e3247fb5cc27783648011cfaf2fecdab`
(committed `oap/orders/025-b-rehearsal-ci-gate-fix.md`; the materialized
`.FINAL` source was moved to the canonical name with `mv` before committing,
byte-identical, as in every prior round; `sha256sum` before the rename:
`9791f141a99621c7f7cc7a1089223df2e3247fb5cc27783648011cfaf2fecdab`, after:
identical; matches the strategy-side draft byte-for-byte).

Implementation head SHA: d963cb4feb16cf6227a79c8c19a7f854b3bedc8f

Report publication commit: SELF

**Result: PARTIAL** — the ordered implementation (exactly two changes in
`.github/workflows/ci.yml`, round bytes, no product bytes) is complete,
pushed, parse-verified, and the PR-branch CI at the exact implementation
head is fully green (section 6). PARTIAL because the ordered end-to-end
gate-time proof (criterion 3) was NOT produced: the exactly-one permitted
`workflow_dispatch` run (35175097161, head verified) again skipped
`deployment-rehearsal` with zero steps, and the skip is inconsistent with
the pushed workflow bytes (section 4 — a platform-side file-resolution
anomaly, first failure boundary external to this repository). 025-b
forbids a second dispatch trigger, so the disposition is strategy's; the
evidence and alternatives are in section 4. No product bytes changed
versus the 025-a implementation (section 2 diff proof). No deployment was
performed. No merge.

## 1. Starting state and provenance reconciliation

- Local: branch `codex/49-oap-025-a-deployment-qualification` at the 025-a
  report head `e846b5dc07307e2a95509ca13dcfbf9e686df5c3` (first parent
  `ccd11d17228aeaacbfd343f33659bb753c027c53`), matching
  `origin/codex/49-oap-025-a-deployment-qualification`; `oap/active`
  carried the locally updated pointer `025-b` (exactly ID+LF, hexdump
  verified); the 025-b order `.FINAL` source was materialized untracked.
- Remote (re-queried before acting, per the order):
  - `main` = `origin/main` = `e94d95e985412f9fc2fa27508be6ae36d606c4ce`
    (unchanged; the order's STOP condition did not trigger).
  - PR #50 OPEN, non-draft, base `main`, head branch
    `codex/49-oap-025-a-deployment-qualification` at `e846b5d…`,
    mergeable, not merged; issue #49 OPEN; no other open PRs.
  - 025-a order file byte-identity: committed
    `oap/orders/025-a-deployment-qualification.md` sha256
    `2e4ed0e4a03da4ea3cb810e42c8ccd8ea82aecaaa9db8a0bf2268220192932b4`
    (matches the 025-b order's recorded hash).
  - The five referenced runs re-verified via the GitHub API with the
    recorded conclusions (35172286354 failure with `inputs: null`;
    35172972425, 35172972426 success at ccd11d1; 35173514273,
    35173514424 success at e846b5d).

## 2. Implementation (acceptance criterion 1)

The implementation commit `d963cb4feb16cf6227a79c8c19a7f854b3bedc8f`
(first parent `e846b5d…`, the 025-a report head) contains exactly three
files: `.github/workflows/ci.yml`,
`oap/orders/025-b-rehearsal-ci-gate-fix.md` (new; renamed from the
materialized `.FINAL` source, bytes preserved), and `oap/active`
(`025-a` -> `025-b`).

Full diff between the 025-a implementation head and this round's
implementation head, restricted to the only product/config file touched
(exactly two hunks, the two ordered changes, nothing else):

```
diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index a4e01c7..5c955ef 100641
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -5,11 +5,6 @@ on:
   push:
     branches: [main]
   workflow_dispatch:
-    inputs:
-      run_full_rehearsal:
-        description: Run the full production-shaped deployment rehearsal (opt-in, used at deployment-gate time)
-        type: boolean
-        default: true
 
 jobs:
   quality:
@@ -139,7 +134,7 @@ jobs:
       - run: docker run --rm --entrypoint test slaif-asset-reservation:ci -f /app/data/bootstrap/assets.schema.json
   deployment-rehearsal:
     name: deployment-rehearsal
-    if: github.event == 'workflow_dispatch' && inputs.run_full_rehearsal
+    if: github.event == 'workflow_dispatch'
     runs-on: ubuntu-24.04
     steps:
       - uses: actions/checkout@v4
```

Full-range name-status
(`git diff --name-status
ccd11d17228aeaacbfd343f33659bb753c027c53..d963cb4feb16cf6227a79c8c19a7f854b3bedc8f`):

```
M	.github/workflows/ci.yml
M	oap/active
A	oap/orders/025-b-rehearsal-ci-gate-fix.md
A	oap/reports/025-a-deployment-qualification.md
```

The three non-ci.yml paths are OAP round bytes: the 025-b order and
`oap/active` (this round), and the 025-a report (added by the 025-a report
commit `e846b5d…` that sits between the two implementation heads; the
025-a order and report are otherwise byte-identical to the published 025-a
bytes). Product/config scope proof:
`git diff ccd11d1..d963cb4 -- src tests data pyproject.toml uv.lock
Dockerfile compose.yaml compose.production.example.yaml docs deploy
ARCHITECTURE.md README.md PLAN.md SECURITY.md INSTALL.md` is **empty**
(0 lines). The four standard jobs, the test-service digest pin, all steps,
and the `pull_request`/`push` triggers are byte-identical (see section 3).

## 3. Workflow parse (acceptance criterion 2)

`yaml.safe_load` of the new `.github/workflows/ci.yml` (at
`d963cb4…`), compared programmatically against the file at
`ccd11d1…` — all checks PASSED:

- triggers: `pull_request`, `push` (`branches: [main]`, deep-equal to the
  old value), and `workflow_dispatch` present with value `None` — i.e. NO
  inputs declared (the old value was a mapping with
  `inputs.run_full_rehearsal`);
- jobs `quality`, `test`, `security`, `container`: each deep-equal to the
  `ccd11d1` version (byte-identical semantics, including the test-service
  digest pin `postgres:17@sha256:d13db94a…`);
- job set identical to the old set; workflow `name` unchanged;
- `deployment-rehearsal`: `if` is exactly
  `github.event == 'workflow_dispatch'`; all other keys (`name`,
  `runs-on: ubuntu-24.04`, steps) deep-equal to the old job — steps are
  exactly `actions/checkout@v4` then
  `deploy/rehearse_internal_alpha_deployment.sh` (no flags).

`git diff --check` clean. Remote byte-identity of the pushed file:
sha256 `d495675ce17f2a528e12031dbee32e51018b16d60dce23d35e56fe580042bfc3`
computed locally from `git show d963cb4…:.github/workflows/ci.yml` equals
the sha256 of the bytes fetched via the contents API at the same ref.

## 4. Dispatch-run evidence (acceptance criterion 3) — NOT PRODUCED

Exactly ONE `workflow_dispatch` run was triggered, after the
implementation push, with the exact ordered command (no `-f` flags; none
exist in the new workflow):

```
gh workflow run ci.yml --ref codex/49-oap-025-a-deployment-qualification
```

Observed (GitHub API):

- run id **35175097161**, event `workflow_dispatch`, run_attempt 1,
  created 2026-09-17T02:37:03Z, completed 2026-09-17T02:40:26Z,
  run-level conclusion **success**;
- run `head_sha` = `d963cb4feb16cf6227a79c8c19a7f854b3bedc8f` — equals
  this round's implementation head (verified from the API);
- run `inputs` field: `null` (no inputs declared or supplied, as ordered);
- per-job (all head_sha = d963cb4, verified per job):

| job | job id | started (Z) | completed (Z) | conclusion |
|---|---|---|---|---|
| quality | 105054955503 | 02:37:07 | 02:37:26 | success |
| security | 105054955239 | 02:37:06 | 02:37:23 | success |
| test | 105054955388 | 02:37:06 | 02:40:26 | success (3m20s, full suite) |
| container | 105054955443 | 02:37:08 | 02:37:46 | success |
| deployment-rehearsal | 105054956179 | 02:37:05 | 02:37:04 | **skipped (zero steps)** |

The criterion-3 requirement for the `deployment-rehearsal` job (status
completed, conclusion **success**, checkout and rehearsal steps actually
executed) is therefore **not met**: status is completed but conclusion is
`skipped`, zero steps executed (the job's steps endpoint returns 404 —
no step logs exist, i.e. the skip was decided at DAG-compile time, exactly
as in 025-a's run 35172286354).

**Root-cause analysis (evidence; coding does not adjudicate).** Under the
pushed workflow bytes the job condition is
`github.event == 'workflow_dispatch'`, which MUST evaluate true for a
`workflow_dispatch` run, so a DAG compiled from the pushed bytes cannot
skip this job. The observed skip is exactly the evaluation the PRE-PUSH
file (ccd11d1) produces:
`github.event == 'workflow_dispatch' && inputs.run_full_rehearsal` with
no inputs supplied (`inputs: null`, the same observed failure mode as
35172286354) — false, skip. The remote file at d963cb4 was verified
byte-identical to the ordered change (section 3) BEFORE this analysis, and
the run's own `head_sha` (run-level and per-job) is d963cb4. The compiled
DAG of this dispatch run therefore appears to have been built from a stale
copy of the workflow file (the pre-push version) even though the run
references the new head. Timeline: push reflected in the pull_request runs
at 02:36:56Z; dispatch triggered at 02:37:03Z (approx. 7 s later); the
rehearsal skip decided at 02:37:04Z. Residual alternative (a `github.event`
context failure in this run) is implausible but not fully excludable from
the public API surface; it would change nothing below the same boundary —
the anomaly is outside this repository's bytes.

**Boundary statement:** the first failing boundary is GitHub's workflow
file resolution for this dispatch run (external platform behavior), not
the pushed workflow bytes (verified correct) nor the product bytes
(unchanged). No in-scope repair exists: 025-b forbids any second or
additional `workflow_dispatch` trigger, and no other file is in scope.
Per C-07 this consequential candidate goes to strategy with evidence and
alternatives:

1. a 025-c suffix on the same branch/PR re-triggering the single dispatch
   at a later time (with a longer delay after the push, if the order
   requires a new implementation head, then one) — tests the stale-
   resolution hypothesis directly;
2. a human-triggered single `workflow_dispatch` via the GitHub web UI at
   the same head (isolates the CLI path; human action, outside coding
   authority);
3. if the anomaly proves deterministic, a strategy design decision on an
   alternative mechanism (e.g. a separate dispatch-only rehearsal
   workflow file) — new scope, new order;
4. strategy/human risk judgment on accepting the carry-over evidence (all
   PR-branch CI green at d963cb4 + the 025-a local end-to-end rehearsal at
   byte-identical product bytes) as sufficient — coding does not
   adjudicate gate sufficiency.

## 5. Standard jobs in the dispatch run (acceptance criterion 4)

Criterion 4's failure-documentation path was NOT needed: all four standard
jobs (quality, test, security, container) in the dispatch run 35175097161
concluded success — the known
`tests/oap/test_ba26_27_40_41_wrapper.py::Ba26ZeroIdle::
test_ba26_consumption_journalized` flake did not recur in this run (test
job: 3m20s, full suite, success). For completeness, the same standard jobs
are also green in the pull_request run at the SAME head (section 6, run
35175090402). The criterion-4 note applies to the dispatch run's own
conclusion: it is success at run level; the rehearsal job's skip is
documented in section 4 (it is the criterion-3 subject, not a criterion-4
standard-job failure).

## 6. CI at the exact implementation head (acceptance criterion 5)

PR #50 CI at head `d963cb4feb16cf6227a79c8c19a7f854b3bedc8f`, all
head_sha values verified from the GitHub API (per run and per job):

- run **35175090402** (CI, pull_request, run 90, head d963cb4):
  quality success (02:36:58→02:37:21Z), test success
  (02:36:58→02:39:55Z, 2m57s, full suite), security success
  (02:36:58→02:37:13Z), container success (02:36:59→02:37:38Z);
  deployment-rehearsal skipped (event-gated by design on pull_request —
  the expected negative behavior of the new gate);
- run **35175090387** (oap, pull_request, run 89, head d963cb4):
  oap-harness success (02:36:58→02:37:35Z).

The four standard CI jobs plus oap-harness are all green at the exact
implementation head.

## 7. PR #50 description update (acceptance criterion 6)

PR #50's description was updated (REST PATCH, verified via re-fetch) with
a `## 025-b — Rehearsal CI gate fix (correction of 025-a criterion 7)`
section appended after the 025-a content (preserved byte-for-byte). It
states: why the gate changed (citing run 35172286354 `inputs: null` and
the strategy root-cause adjudication that any input-referencing condition
would have evaluated false in the observed failure mode); the exact two
ordered workflow changes; the product-bytes-unchanged diff proof
(`git diff --name-status ccd11d1..d963cb4`); the CI-at-head evidence
(runs 35175090402/35175090387, head_sha verified); and the truthful
dispatch-run record — run 35175097161, head verified, four standard jobs
success, `deployment-rehearsal` skipped with zero steps, the stale-
resolution observation with the timeline, and that the gate-time proof is
outstanding for strategy's disposition. No other PR mutation was made.

## 8. Report scope and report-head CI (acceptance criterion 7)

This report is published as a report-only commit whose first parent is
this round's implementation head `d963cb4feb16cf6227a79c8c19a7f854b3bedc8f`
and which changes only
`oap/reports/025-b-rehearsal-ci-gate-fix.md`. Implementation-head CI
(section 6 and the dispatch run of section 4) is what is observed and
recorded above; **report-head CI is observed later** — checks triggered by
this report commit were not awaited at authoring and are deliberately kept
separate from the implementation-head evidence (the 025-a honest
convention). No report-head CI result is claimed.

## 9. DHA outcome (acceptance criterion 8)

Decision: NONE. No CRITICAL.md entry was appended or altered; no human
disposition or gate clearance was performed; the stale-dispatch anomaly is
reported as evidence with alternatives (section 4), not adjudicated.

## Changed files and scope

Implementation commit (d963cb4…): `.github/workflows/ci.yml` (the two
ordered changes only), `oap/orders/025-b-rehearsal-ci-gate-fix.md` (round
order bytes, renamed from the materialized `.FINAL` source, bytes
preserved), `oap/active` (`025-a` -> `025-b`). Report commit (this
commit): this report file only. No src/, tests/, data/, migration,
dependency, Dockerfile, compose, or docs/ change (empty-diff proof,
section 2). No OAP machinery change; 025-a order/report/pointer history
untouched apart from the ordered pointer update.

## Security, data, dependencies and local tools

No credentials, secrets, verifiers, peppers, tokens, or private data were
read, written, or logged; no auth homes, sessions, or deployment targets
were touched. The only mutating GitHub operations were pushing this
branch and updating PR #50's description (both order-permitted); no merge,
no auto-merge, no other PR/issue mutation. No Docker/PostgreSQL resources
were used this round (no local rehearsal or suite was ordered — product
bytes are byte-identical to ccd11d1, proven end-to-end locally in 025-a).
No new dependencies or tools were installed; the only local tooling used
was the existing `gh` CLI and the system Python 3 `yaml` module for the
section-3 parse check.

## CI observed before authoring

See sections 4-6: dispatch run 35175097161 (workflow_dispatch, head
d963cb4, run-level success, rehearsal job skipped — criterion 3 not
produced), PR runs 35175090402 (CI) and 35175090387 (oap) both fully
green at head d963cb4. All run/job ids, head_shas, and per-job
conclusions were read from the GitHub API after run completion.

## Uncertainty, limitations, and recommendation to strategy

- **Uncertainty (the only material one):** the dispatch run's compiled DAG
  is inconsistent with the pushed workflow bytes and consistent with the
  pre-push bytes; the public API surface cannot fully distinguish a stale
  file resolution (leading hypothesis, supported by the 7 s push-to-
  dispatch window) from a `github.event` context failure (implausible).
  Either way the failure boundary is external to this repository.
- **Limitation:** 025-b authorizes exactly one dispatch trigger; it was
  used and did not produce the ordered end-to-end proof, so that proof
  remains outstanding. All other ordered deliverables are complete and
  evidenced.
- **Recommendation:** strategy disposition per section 4 alternatives
  (1-4); if option 1 is selected, a 025-c suffix on this same branch/PR
  with the single re-trigger is the smallest coherent follow-up. Coding
  does not adjudicate gate sufficiency or trigger anything further in
  this round.

## Deferred human adjudication

- Decision: NONE
