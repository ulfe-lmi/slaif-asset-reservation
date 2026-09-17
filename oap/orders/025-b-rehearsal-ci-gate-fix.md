<!-- OAP-META
{
 "id": "025-b",
 "round": "b",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "base_sha": "e94d95e985412f9fc2fa27508be6ae36d606c4ce",
 "issue_number": 49,
 "branch": "codex/49-oap-025-a-deployment-qualification",
 "pr_mode": "AMEND",
 "previous_round": "025-a",
 "allowed_paths": [
  ".github/workflows/ci.yml (workflow_dispatch inputs block removed; deployment-rehearsal if-condition changed; nothing else)",
  "oap/orders/025-b-rehearsal-ci-gate-fix.md",
  "oap/active",
  "oap/reports/025-b-rehearsal-ci-gate-fix.md"
 ],
 "forbidden_resources": [
  "any change to any file other than .github/workflows/ci.yml (the 025-a implementation at ccd11d1 stands otherwise byte-identical)",
  "any src/, tests/, data/, migration, dependency, Dockerfile, compose, or docs/ change",
  "any other oap/ file (025-a order and report stay byte-identical; no OAP expansion)",
  "deployment of any kind (the CI rehearsal job and the disposable synthetic rehearsal are the established exceptions; no real DNS/TLS/certificates/hosts)",
  "real secrets in Git, the diff, prompts, or logs",
  "any second or additional workflow_dispatch trigger (exactly one, per criterion 4)",
  "any mutating GitHub operation except pushing this branch and updating PR #50's description",
  "merging or auto-merging any PR (merge is strategy's delegated act after exact-head review)",
  "ICA activity or milestone-completion claims",
  "credentials, auth files, sessions, tokens, auth homes"
 ]
}
-->

# 025-b — Rehearsal CI gate fix: event-gated full-rehearsal job (correction of 025-a criterion 7)

## Goal

025-a's implementation is accepted as correct except one ordered deliverable:
acceptance criterion 7's "end-to-end proof of the new job" was not produced.
The exactly-one permitted workflow_dispatch run (35172286354, head
ccd11d17228aeaacbfd343f33659bb753c027c53) triggered with the exact ordered
command `gh workflow run ci.yml -f run_full_rehearsal=true --ref
codex/49-oap-025-a-deployment-qualification` produced a run whose REST
`inputs` field is **null** — the CLI-supplied input value did not reach the
run's `inputs` context — so the ordered condition
`if: github.event == 'workflow_dispatch' && inputs.run_full_rehearsal`
evaluated false and `deployment-rehearsal` was skipped (zero steps). The
same run's `test` job additionally failed on the pre-existing oap-harness
FIFO-journaling flake (`test_ba26_consumption_journalized`; 610/611), which
is out of scope here (tests/ forbidden) and green in both PR-event runs at
the same head.

This round makes the smallest coherent correction: the
`deployment-rehearsal` job is gated on the event alone (a manual
workflow_dispatch IS the opt-in; the trigger exists solely for the
rehearsal), the unreliable inputs mechanism is removed, and ONE fresh
workflow_dispatch run on the PR branch proves the job end-to-end at the new
implementation head. No product bytes change.

## Durable provenance and requirements

- H: 2026-09-17 human deployment-qualification instruction, Section A:
  "determine whether the full rehearsal belongs in CI, a conditional
  deployment CI job, or remains intentionally manual; justify the choice
  from evidence"; Section F: remediation creates "only the smallest coherent
  work orders needed to clear the selected internal-alpha gate"; the gate
  requires truthful CI evidence (S-16: missing, pending, cancelled, skipped
  or unexecuted checks do not pass).
- A: S-06 (bounded routine engineering; fix the first reproducibly failing
  boundary), S-12 (corrective requirements get the next defined suffix on the
  same branch/PR), S-13 (orders immutable; 025-a stays as-is), S-16
  (skipped checks do not pass; exact-head review), S-17 (delegated merge
  only after the ordered criteria are met at exact heads), S-19 (name exact
  commands and results; synthetic evidence only).
- E: strategy-verified remote facts (2026-09-17, re-query before acting):
  - PR #50 open: base main e94d95e985412f9fc2fa27508be6ae36d606c4ce, head
    codex/49-oap-025-a-deployment-qualification, 025-a implementation head
    ccd11d17228aeaacbfd343f33659bb753c027c53, 025-a report head
    e846b5dc07307e2a95509ca13dcfbf9e686df5c3 (report-only commit, first
    parent ccd11d1; order bytes byte-identical to the published 025-a order,
    sha256 2e4ed0e4a03da4ea3cb810e42c8ccd8ea82aecaaa9db8a0bf2268220192932b4).
  - CI at ccd11d1: run 35172972425 (CI, pull_request) success — quality,
    test (611), security, container all success, deployment-rehearsal
    skipped by event gate; run 35172972426 (oap, pull_request) success
    (oap-harness, 154). CI at report head e846b5d: runs 35173514273 (CI) and
    35173514424 (oap) success, head_sha verified.
  - Run 35172286354 (CI, workflow_dispatch, head ccd11d1): REST run object
    `inputs: null`, run_attempt 1; jobs: quality success, security success,
    container success, test FAILURE (single failure
    tests/oap/test_ba26_27_40_41_wrapper.py::Ba26ZeroIdle::
    test_ba26_consumption_journalized — AssertionError: 'invoked' not found
    in ['control_consumed']; 610 passed, 1 failed, 108.84s),
    deployment-rehearsal SKIPPED (zero steps executed).
  - The 025-a report's claim that "dispatch input values are not exposed by
    the public REST/GraphQL API" is INCORRECT: the REST run object exposes
    `inputs`, and it is null for this run. Strategy verified this directly
    (gh api repos/.../actions/runs/35172286354). Root cause adjudicated by
    strategy: the CLI `-f` value did not reach the run's inputs context, so
    ANY input-referencing condition (including `inputs.x == 'true'`, the
    string-coercion pattern cited in the 025-a report) would still have
    evaluated false in the observed failure mode. Input-based gating is
    therefore unreliable for this job across CLI and UI paths.
  - The post-025-a ARCHITECTURE.md sha256 recorded in the 025-a report:
    182d9cf924931e846bc7965a079482b6753de762af807196ca0b87f8dffdf863
    (unchanged by this round; product bytes unchanged).
  - Local environment as in 025-a (Docker Engine + Compose v2 available).
- I: workflow-file-only change. The dispatch trigger becomes unambiguous:
  every manual dispatch runs the full rehearsal (its sole purpose); the
  opt-in property is the manual trigger itself; per-PR and per-push cost
  stays zero. The new implementation head's product bytes are identical to
  ccd11d1 (diff must prove only ci.yml changed), so all 025-a local and CI
  evidence for product behavior carries over by byte-identity; the fresh
  dispatch run provides the new gate-time CI proof at the new head.
- C: S-16/S-17 (skipped checks do not pass; exact-head merge), S-19 (exact
  commands/results), SAR-032 (evidence before readiness — the gate-time
  proof must actually execute the job).

## Current reconciled state and prerequisites

- Worktree: strategy leaves it on the PR branch after 025-a review; coding
  starts at the 025-a report head e846b5d on branch
  codex/49-oap-025-a-deployment-qualification (or re-fetches it; record the
  actual starting point in the report). oap/active contains "025-a".
- PR #50 open, non-draft, for issue #49. No other open PRs. main unchanged
  (e94d95e) — verify before starting; if main moved, STOP and report
  BLOCKED.
- The 025-a order/report/oap/active bytes are immutable inputs; this round
  appends 025-b order+report and updates oap/active to "025-b".

## Ordered read set

Standard compact read set, plus: the 025-a order (oap/orders/025-a-
deployment-qualification.md, criteria 5 and 7), the 025-a report (sections
5, 6, 7 — especially the concern-A analysis), .github/workflows/ci.yml at
the 025-a implementation head (on: block and deployment-rehearsal job).

## Scope and allowed paths

1. .github/workflows/ci.yml — exactly two changes:
   (a) remove the `inputs:` block under `workflow_dispatch:` (the
       run_full_rehearsal input no longer exists);
   (b) change the deployment-rehearsal job condition to exactly
       `if: github.event == 'workflow_dispatch'`.
   Nothing else in this file changes (the four standard jobs, the test-
   service digest pin, all steps, triggers pull_request/push/workflow_
   dispatch, remain byte-identical).
2. Round bytes — oap/orders/025-b-rehearsal-ci-gate-fix.md (rename from the
   materialized .FINAL source, bytes preserved), oap/active (now "025-b"),
   oap/reports/025-b-rehearsal-ci-gate-fix.md.

## Non-goals

- No product, test, dependency, docs, compose, or Dockerfile change.
- No local full rehearsal re-run is required (product bytes byte-identical
  to ccd11d1, which 025-a proved by full local rehearsal; the fresh
  dispatch run provides the new evidence on a clean runner).
- No fix or hardening of the oap-harness flake (tests/ scope; separate
  future order if ever selected; not a gate blocker while PR-event CI is
  green at the exact head).
- No OAP expansion, no ICA, no milestone claims, no real deployment, no
  merge.

## Numbered acceptance criteria

1. The diff between the 025-a implementation head
   ccd11d17228aeaacbfd343f33659bb753c027c53 and this round's implementation
   head touches ONLY .github/workflows/ci.yml — and within it only the two
   ordered changes (report shows the full diff; no other hunk).
2. The new workflow parses (yaml.safe_load): triggers pull_request, push,
   workflow_dispatch with NO inputs; jobs quality, test, security,
   container unchanged; deployment-rehearsal with
   `if: github.event == 'workflow_dispatch'`.
3. Exactly ONE workflow_dispatch run is triggered, after the implementation
   push, with the command `gh workflow run ci.yml --ref
   codex/49-oap-025-a-deployment-qualification` (no -f flags; none exist).
   The report records: run id, head_sha (must equal this round's
   implementation head, verified from the API), and the deployment-rehearsal
   JOB result: status completed, conclusion success, with its checkout and
   rehearsal steps actually executed (not skipped) — verified from the
   GitHub jobs API (job id, head_sha, steps/conclusion).
4. If any standard job in that dispatch run fails for an out-of-scope
   reason (e.g. the known test_ba26_consumption_journalized flake), the
   report documents it exactly (failed test id, assertion, duration) AND
   shows the same standard job green in a pull_request run at the SAME head
   (run id + head_sha). The deployment-rehearsal job's own success is the
   criterion-3 evidence regardless of the run-level conclusion.
5. PR #50 CI at this round's exact implementation head: the four standard
   CI jobs plus oap-harness all green, head_sha verified from the API.
6. PR #50 description updated with a 025-b section: why the gate changed
   (citing run 35172286354 inputs:null and the strategy root-cause
   adjudication), the dispatch-run evidence (criterion 3), and the statement
   that product bytes are unchanged versus 025-a (diff proof).
7. Report (oap/reports/025-b-rehearsal-ci-gate-fix.md): report-only commit
   with this round's implementation head as first parent; contains the
   diff (criterion 1), parse evidence (criterion 2), dispatch-run evidence
   (criteria 3-4), CI-at-head evidence (criterion 5), PR-description change
   (criterion 6), and an explicit note that report-head CI is observed
   later (separated from implementation-head CI, per 025-a's honest
   convention).
8. DHA outcome: NONE.

## Deferred human adjudication

- Decision: NONE
