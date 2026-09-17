<!-- OAP-META
{
 "kind": "report",
 "id": "025-c",
 "order_path": "oap/orders/025-c-separate-rehearsal-workflow.md",
 "order_sha256": "4278f6581e2a1b1acefce681428ac7449f5a2afc9cd6df36a62da1a6d8dc2876",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 49,
 "pr_number": 50,
 "branch": "codex/49-oap-025-a-deployment-qualification",
 "implementation_head": "23e9d42013b26ed880430ed6cf9cb8ebb6543e59",
 "base_sha": "e94d95e985412f9fc2fa27508be6ae36d606c4ce",
 "result": "PARTIAL",
 "observed_implementation_ci": {
  "observed_head": "23e9d42013b26ed880430ed6cf9cb8ebb6543e59",
  "runs": [
   {"run_id": 35180066758, "workflow": "CI", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 35180066774, "workflow": "oap", "event": "pull_request", "jobs": {"oap-harness": "failure (known pre-existing flake test_ba26_consumption_journalized; documented in section 5)"}},
   {"run_id": null, "workflow": "deployment-rehearsal (new)", "event": "workflow_dispatch", "jobs": {"NOT CREATED": "dispatch endpoint 404 for a branch-only workflow file; 12 attempts, zero runs; boundary statement in section 4; criterion 3 NOT PRODUCED"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 025-c report — Separate dispatch-only rehearsal workflow (correction of 025-a/025-b criterion 7)

Order digest: `4278f6581e2a1b1acefce681428ac7449f5a2afc9cd6df36a62da1a6d8dc2876`
(committed `oap/orders/025-c-separate-rehearsal-workflow.md`; the materialized
`.FINAL` source was moved to the canonical name with `mv` before committing,
byte-identical, as in every prior round; `sha256sum` after the rename:
`4278f6581e2a1b1acefce681428ac7449f5a2afc9cd6df36a62da1a6d8dc2876`).

Implementation head SHA: 23e9d42013b26ed880430ed6cf9cb8ebb6543e59

Report publication commit: SELF

**Result: PARTIAL** — the ordered implementation (exactly two changes in
`.github/workflows/ci.yml`, the new dispatch-only
`.github/workflows/deployment-rehearsal.yml`, round bytes; no product bytes)
is complete, pushed, parse-verified, and the PR description is updated.
Criterion 3 is NOT PRODUCED, and cannot be produced from this branch state:
the ordered single dispatch of the NEW workflow could not even be created —
GitHub's dispatch endpoint returns HTTP 404 for a workflow file that exists
only on a feature branch (12 attempts, zero runs, positive/negative
filename-resolution controls; boundary statement in section 4). Per the
order's criterion 7 this round reports the evidence truthfully (PARTIAL),
pushes no further workarounds, and does not claim gate sufficiency.
Criterion 4 is not fully met at the exact implementation head: the four
standard jobs are green, but the oap-harness job failed on the known
pre-existing flake `test_ba26_consumption_journalized` (documented exactly
in section 5; no rerun was initiated, as it is a mutating GitHub operation
outside this order's permitted list).

## 1. Starting state and provenance reconciliation

- Branch `codex/49-oap-025-a-deployment-qualification` at 025-b report head
  `1efa799c352f97fed99dc9a81afbe6522bce0e21`, local == remote (verified via
  `git rev-parse` and the GitHub branches API before any edit).
- `main` at `e94d95e985412f9fc2fa27508be6ae36d606c4ce`, unchanged locally and
  on `origin/main` after `git fetch` (the order's STOP condition did not
  trigger).
- PR #50 OPEN for issue #49, head = 025-b report head 1efa799, MERGEABLE.
- `oap/active` already held exactly `025-c` + LF (wrapper-updated from
  `025-b`; the one-line change is part of the round bytes); the materialized
  order source `oap/orders/025-c-separate-rehearsal-workflow.FINAL.md` was
  untracked in the worktree and was renamed to the canonical name with
  `mv` (bytes preserved; digest above). No other local modifications.
- The 025-a/025-b orders and reports are byte-identical to their committed
  state (untouched by this round).

## 2. Implementation (acceptance criterion 1)

Commit `23e9d42013b26ed880430ed6cf9cb8ebb6543e59` (message "025-c: separate
dispatch-only rehearsal workflow (correction of 025-a/025-b criterion 7)"),
pushed to the same branch; PR #50 head advanced to it (AMEND mode).

`git diff --name-status 1efa799c352f97fed99dc9a81afbe6522bce0e21..23e9d42013b26ed880430ed6cf9cb8ebb6543e59`
touches ONLY the ordered paths:

```
M	.github/workflows/ci.yml
A	.github/workflows/deployment-rehearsal.yml
M	oap/active
A	oap/orders/025-c-separate-rehearsal-workflow.md
```

Full diff of `.github/workflows/ci.yml` (exactly the two ordered changes):

```diff
diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index 5c955ef..e7fcf32 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -4,7 +4,6 @@ on:
   pull_request:
   push:
     branches: [main]
-  workflow_dispatch:

 jobs:
   quality:
@@ -132,10 +131,3 @@ jobs:
       - run: docker run --rm --entrypoint test slaif-asset-reservation:ci -f /app/staticfiles/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js
       - run: docker run --rm --entrypoint test slaif-asset-reservation:ci -f /app/data/bootstrap/assets.yaml
       - run: docker run --rm --entrypoint test slaif-asset-reservation:ci -f /app/data/bootstrap/assets.schema.json
-  deployment-rehearsal:
-    name: deployment-rehearsal
-    if: github.event == 'workflow_dispatch'
-    runs-on: ubuntu-24.04
-    steps:
-      - uses: actions/checkout@v4
-      - run: deploy/rehearse_internal_alpha_deployment.sh
```

New file `.github/workflows/deployment-rehearsal.yml` (exact ordered
content, 244 bytes, blob `14a31c3d571c11d918ac0dc0da9fe9f8fe7e2e6c` on the
remote branch head, verified via the contents API):

```yaml
name: deployment-rehearsal

on:
  workflow_dispatch:

jobs:
  deployment-rehearsal:
    name: deployment-rehearsal
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - run: deploy/rehearse_internal_alpha_deployment.sh
```

Round bytes: `oap/active` is now `025-c` + LF (diff `-025-b +025-c`);
`oap/orders/025-c-separate-rehearsal-workflow.md` is the materialized order
source, renamed byte-identically (digest
`4278f6581e2a1b1acefce681428ac7449f5a2afc9cd6df36a62da1a6d8dc2876`).

Byte-equality proofs (programmatic, at the implementation head):
- the new `ci.yml` equals the 1efa799 `ci.yml` minus exactly the
  `workflow_dispatch:` trigger line and exactly the trailing
  `deployment-rehearsal` job block (asserted on raw bytes);
- the resulting `on:` block is byte-identical to the e94d95e trigger block
  (`pull_request`, then `push` branches `[main]`);
- the 025-a test-service digest pin line
  `image: postgres:17@sha256:d13db94ae661d517c5ed57c509a578d5ea64aae639871ba25294f4f42d83de28`
  is byte-identical to the 1efa799 version and present;
- no src/, tests/, data/, migration, dependency, Dockerfile, compose, or
  docs/ byte changed (diff name-status above).

## 3. Workflow parse (acceptance criterion 2)

Both files parse with `yaml.safe_load` (PyYAML, local Python 3.13):

- `.github/workflows/ci.yml`:
  - triggers = exactly `pull_request` + `push` (branches `[main]`); no
    `workflow_dispatch`;
  - jobs = exactly the four standard jobs (`quality`, `test`, `security`,
    `container`); no `deployment-rehearsal` job; no `if:` on any job;
  - step counts unchanged: quality 7, test 14, security 5, container 11;
  - the test-service image is exactly the pinned
    `postgres:17@sha256:d13db94ae661d517c5ed57c509a578d5ea64aae639871ba25294f4f42d83de28`.
- `.github/workflows/deployment-rehearsal.yml`:
  - triggers = exactly `workflow_dispatch` with NO inputs (parsed value
    `None` — bare key, no `inputs:`/`branches:`/`tags:` sub-keys);
  - exactly one job (`deployment-rehearsal`), `runs-on: ubuntu-24.04`, no
    `if:`/condition;
  - exactly two steps: `{uses: actions/checkout@v4}` then
    `{run: deploy/rehearse_internal_alpha_deployment.sh}`;
  - no comments, no other jobs.

## 4. Dispatch-run evidence (acceptance criterion 3) — NOT PRODUCED; dispatch could not be created

After the implementation push (branch head 23e9d42 live at ~03:56:48Z, as
evidenced by the pull_request runs' created_at), the exact ordered dispatch
was attempted:

```
gh workflow run deployment-rehearsal.yml --repo ulfe-lmi/slaif-asset-reservation --ref codex/49-oap-025-a-deployment-qualification
```

→ HTTP 404 (`https://api.github.com/repos/ulfe-lmi/slaif-asset-reservation/actions/workflows/deployment-rehearsal.yml`).
The raw REST equivalent —
`POST /repos/ulfe-lmi/slaif-asset-reservation/actions/workflows/deployment-rehearsal.yml/dispatches`
with body `{"ref": "codex/49-oap-025-a-deployment-qualification"}` —
returned HTTP 404 at 04:01:23Z and again on ten attempts
04:02:17Z–04:11:10Z (~5.5–14.5 min after the push). **Twelve dispatch
attempts in total, all HTTP 404, and no run was ever created** — the runs
endpoint for this workflow (`GET .../actions/workflows/
deployment-rehearsal.yml/runs`) returns 404 as well, and the branch's run
list contains no `workflow_dispatch` run for it. (Every 404 is a
non-creating rejection; no duplicate or extra dispatch was triggered.)

Positive/negative controls (all via the GitHub REST API):

| probe | result |
|---|---|
| file present on branch head 23e9d42 (contents API) | present; blob `14a31c3d571c11d918ac0dc0da9fe9f8fe7e2e6c`, 244 bytes |
| `main`'s `.github/workflows/` listing | only `ci.yml`, `oap.yml` |
| `GET /actions/workflows/ci.yml` (filename resolution) | 200 — id 300051766, active |
| `GET /actions/workflows/deployment-rehearsal.yml` (filename resolution) | 404 |
| `GET /actions/workflows` (repository workflow registry) | only `ci.yml` (300051766) and `oap.yml` (357392690) |

The controls exclude token/scope/repo-path defects: the same filename
resolution succeeds for `ci.yml` and fails only for the branch-only file.

**Complete four-plus-one run chain** (runs 1–4 strategy-verified, detailed
in the 025-a report section 7 and the 025-b report section 4):

1. run 35172286354 @ 01:53:29Z, head ccd11d1 (025-a file): REST `inputs:
   null` despite the ordered `-f run_full_rehearsal=true`; the 025-a
   condition `github.event == 'workflow_dispatch' &&
   inputs.run_full_rehearsal` evaluated false → rehearsal skipped (zero
   steps).
2. run 35175097161 @ 02:37:03Z, head d963cb4 (025-b file, event-only
   condition): dispatched 7 s after the 02:36:56Z push; a skip is IMPOSSIBLE
   under the 025-b bytes → DAG compiled from the stale 025-a definition.
3. run 35176690731 @ 03:02:55Z, head 1efa799 (15 min after last push):
   skipped, same signature.
4. run 35178580431 @ 03:32:57Z, head 1efa799 (45 min after last push):
   skipped, same signature (job 105065638133, run-level success).
5. 025-c attempt @ 23e9d42: **not created** — dispatch endpoint 404
   (section 4 above).

**Boundary statement (evidence; adjudication is strategy/human's, NOT
coding's).** GitHub resolves `workflow_dispatch` identity (workflow
registry, filename lookup, dispatch endpoint) from the repository's
DEFAULT-branch workflow registry; the dispatch endpoint's `ref` parameter
selects the ref to RUN, not the source of the workflow definition. A
workflow file that exists only on a feature branch is therefore not
dispatchable by any API/CLI path, however fresh its workflow identity.
This is an external platform behavior and is a different, EARLIER boundary
than the 025-a/025-b stale-resolution anomaly: there a run was created and
its DAG compiled from a stale snapshot; here the dispatch event itself is
rejected and no run exists (nothing can skip). The 025-c design correctly
removed the stale-snapshot exposure (a fresh workflow identity has no stale
snapshot possible) but could not anticipate this default-branch identity
boundary.

Per the order's criterion 7: no further workarounds were pushed — no
extra triggers, no file churn, no push of the workflow to `main` (outside
the allowed paths), and no claim of gate sufficiency. Alternatives for
strategy/human are listed in section 10.

## 5. CI at the exact implementation head (acceptance criterion 4)

All head_sha values verified from the GitHub API (per run and per job),
head = `23e9d42013b26ed880430ed6cf9cb8ebb6543e59`:

- run **35180066758** (CI, pull_request, PR #50):
  - quality: success (job 105070082484, 03:56:51→03:57:11Z);
  - test: success (job 105070082698, 03:56:51→03:59:36Z, full 611-test
    suite);
  - security: success (job 105070082722, 03:56:51→03:57:06Z);
  - container: success (job 105070082694, 03:56:51→03:57:22Z).
  All four standard jobs GREEN.
- run **35180066774** (oap, pull_request): oap-harness job 105070082618
  **failure** (03:56:52→03:57:32Z): `Ran 154 tests in 31.862s — FAILED
  (failures=1)`, the single failure being the known pre-existing flake
  `tests/oap/test_ba26_27_40_41_wrapper.py::Ba26ZeroIdle::
  test_ba26_consumption_journalized` —
  `AssertionError: 'invoked' not found in ['control_consumed']` (line 115).
  This is the same flake family recorded as 025-a candidate concern B
  (and the 023-a FIFO flake family). No `tests/` or `oap/bin` byte changed
  in this round (forbidden by the order; a flake fix would need a dedicated
  order). At this SAME head, the same test executed and PASSED inside the
  CI `test` job's full 611-test product suite (job 105070082698, success).

Criterion 4 is therefore not fully met: the four standard jobs are green
but oap-harness is not green at this head, and no second oap run exists at
this head. Per the order's permitted mutating-operation list ("pushing this
branch and updating PR #50's description" only), NO rerun of the failed
job was initiated; whether a rerun is permitted to cure a flake at a fresh
head is a boundary question for strategy (see section 10).

## 6. PR #50 description update (acceptance criterion 5)

PR #50's description was updated (body length 13915 → 20149 characters,
verified via the REST API after the change) with a new section
`## 025-c — Separate dispatch-only rehearsal workflow (correction of
025-a/025-b criterion 7)` containing: the four-run root-cause chain (run
IDs 35172286354 / 35175097161 / 35176690731 / 35178580431, `inputs: null`,
the 7 s / 15 min / 45 min stale-resolution timeline, remote-blob
verification); the design decision (separate dispatch-only workflow, fresh
workflow identity, `ci.yml` reverted to the standard e94d95e triggers with
the 025-a digest pin retained); the dispatch evidence exactly as in section
4 of this report (404 chain, controls, boundary statement); the
product-bytes-unchanged statement with the `git diff --name-status` proof
(1efa799..23e9d42); the CI-at-head status including the oap-harness flake;
and the unchanged merge-gate note.

Note on method: `gh pr edit --body-file` failed with a GraphQL
"Projects (classic) is being deprecated" error (`projectCards`); the
update was performed with the REST equivalent `PATCH
/repos/ulfe-lmi/slaif-asset-reservation/pulls/50` carrying the full body —
the same authorized operation ("updating PR #50's description").

## 7. Report scope (acceptance criterion 6)

This report is published as a report-only commit whose first parent is this
round's implementation head `23e9d42013b26ed880430ed6cf9cb8ebb6543e59` and
which changes ONLY
`oap/reports/025-c-separate-rehearsal-workflow.md`. It contains the diff
(section 2), parse evidence (section 3), dispatch evidence (section 4),
CI-at-head evidence (section 5), the PR-description change (section 6), the
explicit statement below, and the honest implementation-head vs report-head
CI separation (section 9).

**Gate sufficiency was NOT self-adjudicated.** Whether the carry-over
evidence (the 025-a full local rehearsal at byte-identical product bytes +
the green PR-branch standard jobs) is sufficient for the internal-alpha
gate is a strategy/human adjudication. This report makes no such claim,
and the dispatch-run proof (criterion 3) was NOT produced this round.

## 8. DHA outcome (acceptance criterion — DHA declaration)

Decision: NONE. No `CRITICAL.md` entry was appended or altered; no human
disposition, gate clearance, or sufficiency claim was performed.

## Changed files and scope

At the implementation head (vs 025-b report head 1efa799):
`.github/workflows/ci.yml` (M — exactly the two ordered changes),
`.github/workflows/deployment-rehearsal.yml` (A — exact ordered content),
`oap/orders/025-c-separate-rehearsal-workflow.md` (A — materialized order
source, byte-identical rename), `oap/active` (M — `025-b` → `025-c`). The
final report commit changes only
`oap/reports/025-c-separate-rehearsal-workflow.md`, with the implementation
head as first parent. No other file (including CRITICAL.md) changed in any
round commit.

## Security, data, dependencies and local tools

No secrets, verifiers, peppers, credentials, or private data entered Git,
this report, the PR description, or logs. No deployment of any kind
performed; no DNS/TLS/certificates/hosts; no lab/Neumann/production
contact; no real exports. No dependency changes (uv.lock untouched); no
product code touched. Local tools: git, Python 3.13 with PyYAML (parse
checks), gh CLI (read APIs + the ordered publication operations: one branch
push, the PR #50 description update, and the ordered single-dispatch
attempt — CLI plus raw-REST retries, all non-creating 404s). No OS
sidecars. The rehearsal script was NOT re-run locally (ordered non-goal:
product bytes are byte-identical to the 025 heads, which 025-a proved by
full local rehearsal).

## CI observed before authoring

See section 5 (implementation head `23e9d42`): CI run 35180066758 all four
standard jobs success; oap run 35180066774 oap-harness failure on the known
flake `test_ba26_consumption_journalized`. Report-head CI is NOT YET
OBSERVED AT AUTHORING: this report commit becomes the new PR head, and its
checks have not run (and are not claimed) at authoring. Later publication
verification goes to the private execution receipt, not to a report
rewrite.

## Uncertainty, limitations, and recommendation to strategy

- The dispatch of the new workflow could not be created from this branch
  state (default-branch identity boundary, section 4). Residual
  uncertainty is minimal and does not change the boundary: the controls
  (positive `ci.yml` resolution, negative branch-only resolution,
  registry listing, file presence on the branch) cover the available API
  surface. The web UI dispatch menu is built from the same default-branch
  registry (consistent with the observed API behavior) and would
  therefore likely be subject to the same boundary; the UI was not
  exercised this round (no browser work in scope).
- oap-harness flaked at the implementation head (section 5). The flake is
  pre-existing, unrelated to this diff, and already recorded (023-a
  family; 025-a candidate concern B); a dedicated order is required to
  harden it.
- Alternatives for strategy/human (evidence-backed; none performed by
  coding):
  1. an order amending this branch/PR (or the gate-merge preparation) to
     place `.github/workflows/deployment-rehearsal.yml` on the default
     branch so its dispatch identity resolves, then the single ordered
     dispatch at the resulting head;
  2. strategy/human risk judgment on accepting the carry-over evidence
     (025-a full local rehearsal at byte-identical product bytes; all
     standard PR-branch jobs green at every 025 head; oap-harness flake
     documented) as sufficient for the internal-alpha gate — coding does
     not adjudicate;
  3. a dedicated order to harden the
     `test_ba26_consumption_journalized` flake (tests/ scope).

## Deferred human adjudication

- Decision: NONE
