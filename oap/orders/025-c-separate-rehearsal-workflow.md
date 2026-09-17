<!-- OAP-META
{
 "id": "025-c",
 "round": "c",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "base_sha": "e94d95e985412f9fc2fa27508be6ae36d606c4ce",
 "issue_number": 49,
 "branch": "codex/49-oap-025-a-deployment-qualification",
 "pr_mode": "AMEND",
 "previous_round": "025-b",
 "allowed_paths": [
  ".github/workflows/ci.yml (remove workflow_dispatch trigger + deployment-rehearsal job; keep everything else, incl. the 025-a test-service digest pin)",
  ".github/workflows/deployment-rehearsal.yml (NEW, exactly the ordered content)",
  "oap/orders/025-c-separate-rehearsal-workflow.md",
  "oap/active",
  "oap/reports/025-c-separate-rehearsal-workflow.md"
 ],
 "forbidden_resources": [
  "any change to any file other than the two workflow files listed above",
  "any src/, tests/, data/, migration, dependency, Dockerfile, compose, or docs/ change",
  "any other oap/ file (025-a/025-b orders and reports stay byte-identical; no OAP expansion)",
  "deployment of any kind (the CI rehearsal job is the established exception; no real DNS/TLS/certificates/hosts)",
  "real secrets in Git, the diff, prompts, or logs",
  "more than ONE workflow_dispatch trigger of the new workflow (exactly one, per criterion 3)",
  "any mutating GitHub operation except pushing this branch and updating PR #50's description",
  "merging or auto-merging any PR (merge is strategy's delegated act after exact-head review)",
  "ICA activity or milestone-completion claims",
  "unilaterally declaring the gate-time mechanism 'sufficient' on carry-over evidence without the criterion-3 dispatch evidence (sufficiency is a strategy/human adjudication, recorded in the report as NOT made)",
  "credentials, auth files, sessions, tokens, auth homes"
 ]
}
-->

# 025-c — Separate dispatch-only rehearsal workflow (correction of 025-a/025-b criterion 7)

## Goal

The 025-a/025-b attempt to prove the opt-in full-rehearsal CI job end-to-end
failed four times for reasons outside this repository's bytes. This round
replaces the unreachable conditional job in ci.yml with a SEPARATE minimal
dispatch-only workflow file, so the gate-time rehearsal proof uses a fresh
workflow identity with no stale-definition exposure, and re-runs the single
ordered dispatch to produce the criterion-7 evidence at the new
implementation head. No product bytes change.

## Durable provenance and requirements

- H: 2026-09-17 human deployment-qualification instruction, Section A
  ("determine whether the full rehearsal belongs in CI, a conditional
  deployment CI job, or remains intentionally manual; justify the choice
  from evidence") and Section F (smallest coherent work orders to clear the
  selected internal-alpha gate; truthful evidence; no broad readiness
  re-review or chain of preparatory work orders).
- A: S-06 (first reproducibly failing boundary + smallest separating
  experiment; do not change code below a boundary the failure never reached —
  here the failing boundary IS the dispatch mechanism), S-12 (next defined
  suffix, same branch/PR; H/A/E/I/C provenance), S-13 (prior orders
  immutable), S-16 (skipped checks do not pass; exact-head review), S-17
  (delegated merge only when ordered criteria are met at exact heads), S-19
  (exact commands and results; synthetic evidence only).
- E: strategy-verified facts (re-verify before acting; the 025-a/025-b
  orders and reports under oap/orders|reports are the detailed record):
  - Objective 025 state: PR #50 (issue #49) open; 025-a impl head ccd11d1,
    025-a report head e846b5d, 025-b impl head d963cb4, 025-b report head
    1efa799c352f (branch tip; report-only, first parent d963cb4). Product
    bytes identical across all four heads (only docs/config/workflow bytes
    changed in 025; the rehearsal/stack bytes equal main e94d95e's).
  - FOUR workflow_dispatch runs on this branch, ALL with deployment-rehearsal
    skipped, ALL four standard jobs otherwise green:
    1. 35172286354 @ 01:53:29Z head ccd11d1 (025-a file): triggered with the
       ordered command incl. `-f run_full_rehearsal=true`; REST run object
       `inputs: null` — the CLI value never reached the run's inputs context;
       skip under the 025-a condition `github.event == 'workflow_dispatch' &&
       inputs.run_full_rehearsal`. Same run's test job failed on the known
       oap-harness flake (610/611; green in both PR runs at the same head).
    2. 35175097161 @ 02:37:03Z head d963cb4 (025-b file, event-only
       condition): dispatched 7s after the push (02:36:56Z); skip is
       IMPOSSIBLE under the 025-b bytes (`github.event == 'workflow_dispatch'`
       cannot be false in a dispatch run) — DAG compiled from the stale
       025-a definition.
    3. 35176690731 @ 03:02:55Z head 1efa799: 15 min after the last push;
       skipped (same signature).
    4. 35178580431 @ 03:32:57Z head 1efa799: 45 min after the last push;
       skipped (same signature; job 105065638133; run-level success).
  - Strategy verified via the GitHub contents API that the remote
    .github/workflows/ci.yml at 1efa799 contains the 025-b event-gated job —
    so the skips cannot be explained by the pushed bytes. Root cause
    adjudicated by strategy: GitHub's dispatch file resolution for the ci.yml
    workflow ID is pinned to the pre-025-b (025-a) definition snapshot
    regardless of ref, across 45+ minutes and three newer branch heads.
    First failing boundary = EXTERNAL platform behavior. A fresh workflow
    file (new workflow ID, never dispatched before) has no stale snapshot
    possible.
  - The rehearsal script is unchanged and proven: 025-a local full rehearsal
    at the implementation bytes (rehearsal=ok, exit 0, self-clean), and the
    025-a/025-b dispatch runs' 4 standard jobs green at clean runners.
  - Post-025 ARCHITECTURE.md sha256 (unchanged by 025): 182d9cf924931e846bc7
    965a079482b6753de762af807196ca0b87f8dffdf863.
- I: workflow-file-only change. ci.yml reverts to its standard triggers
  (pull_request + push main) and keeps the 025-a test-service digest pin; the
  unreachable job is removed. The new file makes the gate-time mechanism
  explicit by name and minimal by construction. If the new file's single
  dispatch also skips, that proves a systemic platform defect beyond this
  repo's control; the round then reports the evidence truthfully (PARTIAL)
  and strategy adjudicates whether the carry-over evidence (local full
  rehearsal at byte-identical product bytes + all PR-branch CI green) is
  sufficient for the internal-alpha gate — coding does NOT self-adjudicate.
- C: S-16/S-17 (skipped checks do not pass; exact-head merge), S-19 (exact
  commands/results), SAR-032 (evidence before readiness).

## Current reconciled state and prerequisites

- Worktree on branch codex/49-oap-025-a-deployment-qualification at 025-b
  report head 1efa799c352f (or re-fetch); oap/active = "025-b"; main at
  e94d95e unchanged (verify; if main moved, STOP and report BLOCKED).
- PR #50 open for issue #49; 025-a/025-b orders+reports immutable in the
  branch. This round appends 025-c order+report and updates oap/active to
  "025-c".

## Ordered read set

Standard compact read set, plus: the 025-a report section 7 and 025-b report
section 4 (the full dispatch-run evidence chain), .github/workflows/ci.yml at
1efa799 (on: block + deployment-rehearsal job to be removed).

## Scope and allowed paths

1. .github/workflows/ci.yml — exactly two changes:
   (a) remove `workflow_dispatch:` from `on:` (restore the e94d95e trigger
       block exactly: pull_request, then push branches [main]);
   (b) remove the deployment-rehearsal job (the last job in the file).
   Everything else stays byte-identical, including the 025-a test-service
   digest pin and all four standard jobs.
2. .github/workflows/deployment-rehearsal.yml (NEW) — exactly this content:
   ---
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
   ---
   (No inputs, no conditions, no other jobs, no comments beyond name lines.)
3. Round bytes — oap/orders/025-c-separate-rehearsal-workflow.md (rename from
   the materialized .FINAL source, bytes preserved), oap/active (now
   "025-c"), oap/reports/025-c-separate-rehearsal-workflow.md.

## Non-goals

- No product, test, dependency, docs, compose, or Dockerfile change.
- No local full rehearsal re-run (product bytes byte-identical to 025 heads,
  which 025-a proved by full local rehearsal; the new dispatch run provides
  the new evidence on a clean runner).
- No flake hardening (tests/ scope; separate order if ever selected).
- No OAP expansion, no ICA, no milestone claims, no real deployment, no
  merge, no self-adjudication of gate sufficiency.

## Numbered acceptance criteria

1. The diff between the 025-b report head 1efa799c352f and this round's
   implementation head touches ONLY .github/workflows/ci.yml (exactly the
   two ordered changes), the NEW .github/workflows/deployment-rehearsal.yml
   (exactly the ordered content), and the round bytes. The report shows the
   full diff.
2. Both workflow files parse (yaml.safe_load): ci.yml triggers =
   pull_request + push(main) ONLY, four standard jobs unchanged incl. the
   test-service digest pin, no deployment-rehearsal job; the new file has
   exactly one job with exactly the two ordered steps and no inputs.
3. Exactly ONE workflow_dispatch of the NEW workflow is triggered, after the
   implementation push, with the command `gh workflow run
   deployment-rehearsal.yml --repo ulfe-lmi/slaif-asset-reservation --ref
   codex/49-oap-025-a-deployment-qualification`. The report records: run id,
   head_sha (must equal this round's implementation head, verified from the
   API), and the deployment-rehearsal JOB result: status completed,
   conclusion success, checkout + rehearsal steps actually executed (not
   skipped) — verified from the GitHub jobs API (job id, head_sha).
4. PR #50 CI at this round's exact implementation head: the four standard CI
   jobs plus oap-harness all green, head_sha verified from the API. (If a
   standard job fails on the known oap-harness flake, document exactly and
   show the same job green at the same head elsewhere.)
5. PR #50 description updated with a 025-c section: the four-run root-cause
   chain (run IDs 35172286354 / 35175097161 / 35176690731 / 35178580431,
   inputs:null, 7s/15min/45min stale-resolution timeline, remote blob
   verification), the design decision (separate dispatch-only workflow; new
   workflow identity; ci.yml reverted to standard triggers with the digest
   pin retained), the dispatch-run evidence (criterion 3), and the statement
   that product bytes are unchanged versus 025-a/025-b (diff proof).
6. Report (oap/reports/025-c-separate-rehearsal-workflow.md): report-only
   commit with this round's implementation head as first parent; contains
   the diff (criterion 1), parse evidence (criterion 2), dispatch evidence
   (criterion 3), CI-at-head evidence (criterion 4), PR-description change
   (criterion 5), an explicit statement that gate sufficiency was NOT
   self-adjudicated (it is strategy/human's), and the honest
   implementation-head vs report-head CI separation.
7. If criterion 3 CANNOT be produced (the new workflow's dispatch also
   skips): report PARTIAL with the exact run/job evidence, the complete
   four-plus-one run chain, and the boundary statement (systemic platform
   defect); do NOT push further workarounds (no extra triggers, no file
   churn) and do NOT claim sufficiency.

## Deferred human adjudication

- Decision: NONE
