<!-- OAP-META
{
 "id": "015-b",
 "round": "b",
 "base_sha": "14fc20b1ff52788974fd3f282322afc9d71362f9",
 "issue_number": 29,
 "branch": "codex/29-oap-015-a-simplify-canary",
 "pr_mode": "AMEND",
 "previous_round": "015-a",
 "allowed_paths": [
  "oap/bin/oaplib.py",
  "oap/bin/verify_report.py",
  "tests/oap/",
  "oap/orders/015-b-simplify-canary.md",
  "oap/active",
  "oap/reports/015-b-simplify-canary.md"
 ],
 "forbidden_resources": [
  "product application code under src/, migrations, data/, product tests outside tests/oap/",
  "dependency or tooling version changes (pyproject.toml, uv.lock)",
  "production databases, real lab/Neumann machines, real SmartScheduling data",
  "credentials, auth files, sessions, tokens, auth homes, or copied private exports",
  "DNS/TLS/firewall changes, public exposure, repository visibility or branch-protection changes",
  "any mutating GitHub operation (PR create/close/comment/merge/approve, settings, branch writes)",
  "any other .github/workflows file or CI change",
  "merging or auto-merging any PR",
  "model provider endpoints other than the configured qwen-neumann role profile"
 ]
}
-->

# 015-b — Make operational PR-identity verification work (correction of 015-a)

## Goal

Correction round for objective 015-a (same branch, same PR #30, AMEND). Close
the one gap the 015-a round-trip canary exposed: the operational remote
adapter (`GitRemote` in oap/bin/oaplib.py) stubs PR identity, so
`verify_report.py --pr` cannot PASS against the real remote. Implement
read-only operational PR-identity resolution and prove the full three-check
verification end to end on the real remote. No product behavior change.

## Durable provenance and requirements

- H: in-session human principal approval 2026-09-14 of the simplification and
  its truthful-evidence standard; the executed 015-a round.
- E: private execution receipt
  `agent-homes/coding/receipts/015-a-execution-receipt.md` (post-publication
  verify_report: PASS without --pr, FAIL with --pr 30 because
  `GitRemote.pr()` returns unknown "operational API not configured");
  strategy re-verified the same FAIL on 2026-09-14 at report head
  85b874969223e31ae06618f5a038ec99e22f0208.
- A: OAP-PROTOCOL OP-02 (correction suffix amends the same objective/PR),
  OP-10 (missing remote evidence is BLOCKED, never a local pass).
- C: S-16 (exact-head review must verify remote PR identity), S-12.
Requirements: SAR-033, SAR-034, SAR-035, SAR-037, SAR-038.

## Current reconciled state and prerequisites

- Local worktree is clean on branch codex/29-oap-015-a-simplify-canary at
  report head 85b874969223e31ae06618f5a038ec99e22f0208; remote branch head
  equals it; PR #30 OPEN/MERGEABLE with that head; main still 14fc20b.
- 015-a implementation head 12ef602bac2bbdf027debccaa0766d2637dd84a7 CI:
  quality/test/container PASS, security FAIL (identical pre-existing
  pip-audit baseline, no waiver), oap workflow PASS. Report-head 85b8749 CI:
  same pattern (CI run 34789126330, oap run 34789126294).
- Host has `gh` authenticated (jpers1) and `git`; the operational network
  authorization covers read-only git/GitHub egress for the coding role.

## Ordered read set

Standard compact read set plus the active 015-a order and 015-b order, the
`load_remote_adapter`/`GitRemote` region of oap/bin/oaplib.py,
oap/bin/verify_report.py check 3, the surviving ba28-ba32 report tests, and
`agent-homes/coding/receipts/015-a-execution-receipt.md` (read-only).

## Scope and allowed paths

1. oap/bin/oaplib.py — `GitRemote.pr(repo_root, number)`: resolve via a
   read-only `gh` subprocess: `gh pr view <number> --json
   number,headRefName,headRefOid,state,mergedAt --repo <owner/name>` where
   owner/name is parsed from `git remote get-url origin` in repo_root. Map to
   the same dict shape FixtureRemote uses: number, branch (headRefName), head
   (headRefOid), state ("open"/"closed"; merged when mergedAt non-null),
   merged boolean. Finite timeout. Any missing gh, non-zero exit, timeout,
   unparsable output or missing fields returns
   `{"unknown": True, "reason": <short factual reason>}` — never a
   fabricated identity. No gh mutation verb may ever be constructed.
2. oap/bin/oaplib.py — `GitRemote.pr_for_branch(repo_root, branch)`:
   `gh pr list --state all --json number,headRefName,state,mergedAt --repo
   <owner/name>` (bounded query) and return the matching open-or-merged PR
   dict or None; same unknown-safe error behavior. No other GitRemote method
   changes; `create_pr` and `mark_merged` keep refusing.
3. oap/bin/verify_report.py — check 3: when `--pr` is given and the adapter
   returns an unknown PR identity, report the check as BLOCKED with the
   adapter reason (truthful; neither local pass nor fabricated FAIL), and
   PASS only when the resolved branch/head/state agree with the order.
4. tests/oap: keep all fixture-based tests green. Add one new test file
   (or extend the ba28-ba32 file) that proves the operational parsing path
   with a fake `gh` executable fixture placed on PATH: correct mapping of
   pr(30) and pr_for_branch for a known branch; unknown on non-zero exit /
   timeout / bad JSON; and an assertion that every gh argv used is
   read-only (no create/edit/close/merge/comment/approve verbs or flags).
5. The round bytes for this order (oap/orders/015-b-simplify-canary.md,
   oap/active pointer) and the final report (oap/reports/015-b-simplify-canary.md).

Everything else is protected, including the 015-a order, the 015-a report,
docs/bootstrap/archive/, docs/audit/, all product paths, and CI workflows.
The 015-a report is immutable: do not amend, reword or re-push it.

## Non-goals

- No product change, no dependency change, no CI workflow change.
- No fixing of the pre-existing pip-audit security failure (stays red,
  reported, no waiver).
- No fixing of the reported 015-a residuals (doctor.sh comment,
  .dockerignore line, historical docs) — out of this correction's scope.
- No merge, auto-merge, approval or settings change; no mutation of any
  GitHub state except pushing this branch.
- No new framework, daemon, config file or helper.

## Numbered acceptance criteria

1. The 015-b diff touches only the allowed paths; zero changes outside them;
   the 015-a order and 015-a report bytes are unchanged.
2. `GitRemote.pr`/`pr_for_branch` resolve PR identity read-only via gh with
   finite timeouts and return unknown (never a fabricated value) on any
   failure; no mutating gh command can be constructed (fixture-asserted).
3. verify_report.py check 3 returns PASS when the operational adapter
   resolves a matching open PR, and BLOCKED (truthful reason) when identity
   is unresolvable — never a local pass and never a mismatch-on-unknown FAIL.
4. On this host against the real remote (operational, no fixture adapter),
   `python3 oap/bin/verify_report.py --repo . --id 015-a --pr 30 --head
   85b874969223e31ae06618f5a038ec99e22f0208 --remote origin` returns status
   PASS with all three checks ok; the exact output goes to the private
   execution receipt.
5. The full tests/oap suite passes locally (existing 131 + new
   operational-path test), 0 skipped beyond an explicitly marked
   BLOCKED-skip if any, ruff clean.
6. CI at the new report head: quality, test, container PASS; security shows
   only the identical 20 pre-existing pip-audit findings (no new findings, no
   dependency change); oap workflow PASS.
7. The 015-b report states the 015-a report remains valid and immutable,
   records the criterion-4 operational PASS output, and keeps the truthful
   implementation-CI vs report-head-CI separation.

## Verification

- `env -u OAP_ROLE .venv/bin/python -m unittest discover -s tests/oap -p 'test_*.py'`
- `python3 oap/bin/verify_report.py --repo . --id 015-a --pr 30 --head 85b874969223e31ae06618f5a038ec99e22f0208 --remote origin` (real remote; criterion 4)
- CI at the exact reviewed head per criterion 6.
- Strategy then completes the OP-11 exact-head review of the combined
  015-a+015-b diff (015-a scope already reviewed clean by strategy) and the
  human merges PR #30.

## Negative paths

- Never fabricate a PR number, branch or state; unknown stays unknown.
- Do not re-run or replay the 015-a round; no new objective or renumbering.
- If gh is unavailable at verification time, criterion 4 is BLOCKED and the
  round reports it truthfully; do not paper over with fixture adapters
  (OP-10: fixture adapter never silently selected in operational mode).
- No self-merge, auto-merge, check approval or protection bypass.

## Documentation

No documentation change is required; oap/README.md and the runbook already
describe the slim round. The 015-b report carries the operational evidence.

## Recovery

Interrupted round: same ID 015-b, same branch, issue #29, PR #30; resume from
the current branch head without renumbering; oap/RECOVERY.md state machine
applies; a lost response after remote report means strategy review, not rerun.

## Deferred human adjudication

- Decision: NONE

## Publication and reporting

PR #30 already exists and is amended by new implementation commits; the final
015-b report is a report-only commit with the 015-b implementation head as
first parent; Report publication commit SELF; truthful implementation-CI vs
report-head-CI separation; remote verification receipt in the private home;
exact two-byte response OK; then no further mutation this round. Coding never
merges.
