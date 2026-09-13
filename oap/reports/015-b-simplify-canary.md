<!-- OAP-META
{
 "kind": "report",
 "id": "015-b",
 "order_path": "oap/orders/015-b-simplify-canary.md",
 "order_sha256": "ac8c07ca065e7a7a957dafb7101cfe307313de8c965fe48d400a087c31b75da0",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 29,
 "pr_number": 30,
 "branch": "codex/29-oap-015-a-simplify-canary",
 "implementation_head": "cdc846cbb131f2ca7d936e6329ef1d0f903f1dd6",
 "base_sha": "14fc20b1ff52788974fd3f282322afc9d71362f9",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "cdc846cbb131f2ca7d936e6329ef1d0f903f1dd6",
  "runs": [
   {"run_id": 34790971910, "workflow": "CI", "jobs": {"quality": "success", "test": "success", "security": "failure", "container": "success"}},
   {"run_id": 34790971837, "workflow": "oap", "jobs": {"oap-harness": "success"}}
  ],
  "security_note": "failure limited to the identical pre-existing pip-audit findings of main run 34783895298 (per-ID multiset diff empty); no dependency changes; reported, not fixed, not waived"
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 015-b report — make operational PR-identity verification work (correction of 015-a)

Order digest: ac8c07ca065e7a7a957dafb7101cfe307313de8c965fe48d400a087c31b75da0

Implementation head SHA: cdc846cbb131f2ca7d936e6329ef1d0f903f1dd6

Report publication commit: SELF

**Result: COMPLETE** — order 015-b implemented exactly within `allowed_paths` on the
same branch/PR as 015-a (AMEND). The one gap the 015-a round-trip canary exposed —
`GitRemote.pr()` stubbed PR identity, so `verify_report.py --pr` could not PASS against
the real remote — is closed: the operational adapter now resolves PR identity via fixed
read-only `gh` templates, and the full three-check verification passes end to end on the
real remote (criterion 4 below). No product behavior change.

The 015-a report (`oap/reports/015-a-simplify-canary.md`, digest
`8d05fc89d40cf89b941be9a993ef743d32eb1f6b6a753e641e90946525b05ab9`) **remains valid and
immutable**: its bytes are unchanged by this round, its evidence was verified at
publication time (private receipt of 015-a), and this round did not amend, reword or
re-push it. The 015-a order (digest `08309a4d…`, unchanged) is likewise untouched.

## What changed

Commit `cdc846c` changes exactly five files (all on 015-b `allowed_paths`):

- `oap/bin/oaplib.py` — new read-only `gh` section: `GH_PR_VIEW_FIELDS` /
  `GH_PR_LIST_FIELDS` templates, `gh_owner_name` (parses owner/name from
  `git remote get-url origin`), `gh_readonly` (single read-only `gh` subprocess,
  finite timeout, stdin detached), `gh_pr_identity` (maps one gh PR object to the
  FixtureRemote dict shape; missing/mistyped fields yield unknown, never a
  fabricated value). `GitRemote.pr` now runs
  `gh pr view <n> --json number,headRefName,headRefOid,state,mergedAt --repo
  <owner/name>`; `GitRemote.pr_for_branch` runs
  `gh pr list --state all --json number,headRefName,state,mergedAt --repo
  <owner/name>` and returns the matching open-or-merged PR (open preferred over
  merged over closed) or None. Every failure mode (missing gh, non-zero exit,
  timeout, unparsable output, missing origin/fields, invalid number) returns
  `{"unknown": True, "reason": <short factual reason>}`. `create_pr` and
  `mark_merged` keep refusing; no other `GitRemote` method changed; `FixtureRemote`
  unchanged. The module docstring now records the two read-only gh templates.
- `oap/bin/verify_report.py` — check 3: when the adapter returns an unknown PR
  identity (with or without `--pr`), the check is reported **BLOCKED** with the
  adapter reason — neither a local pass nor a mismatch-on-unknown FAIL (an
  already-failed local check keeps FAIL). The `--pr` path additionally verifies the
  resolved PR head equals the report commit and its state is open; branch
  mismatch/head mismatch/non-open state remain FAIL. Text output labels a blocked
  check `[BLOCKED]` instead of `FAIL`.
- `tests/oap/test_operational_pr.py` — new: 21 tests proving the operational
  parsing path with a fake `gh` executable placed on PATH (mapping of `pr(30)`
  open/merged/closed, `pr_for_branch` hit/absence/open-over-merged preference,
  unknown on non-zero exit / bad JSON / timeout / missing gh / missing origin /
  invalid number, URL-form parsing), plus fixture-asserted read-only argv (exact
  two templates; no create/edit/close/merge/comment/approve verbs or flags), plus
  `verify_report.py` check 3 end to end on a fixture repo with a local bare
  `origin`: PASS with a resolved open PR, BLOCKED (truthful) when gh is absent or
  failing, FAIL reserved for genuine branch/head mismatches.
- `oap/orders/015-b-simplify-canary.md` — this round's order bytes, committed under
  the canonical name (byte-identical to the strategy-placed staging file; digest
  above).
- `oap/active` — exactly `015-b\n` (this round's pointer).

## Numbered acceptance evidence (against the order's 7 criteria)

1. **Diff scope.** The 015-b commit (`85b8749…` → `cdc846c…`) changes exactly the five
   files above, all within 015-b `allowed_paths`. The combined 015-a+015-b diff
   (`14fc20b…` → `cdc846c…`) is 56 files; checked programmatically against the union
   of the 015-a and 015-b `allowed_paths`: **zero out-of-scope paths**. The 015-a order
   and 015-a report bytes are byte-identical between `85b8749…` and `cdc846c…`
   (digests `08309a4d…` / `8d05fc89…` unchanged).
2. **Read-only gh resolution, finite timeouts, no fabrication.** argv is constructed
   only from the two fixed read-only templates with a finite timeout (30 s default;
   the timeout path is exercised at 0.3 s against a sleeping fake gh). Unknown is
   returned for: missing gh, non-zero exit, timeout, unparsable JSON, missing origin,
   unparseable origin URL, missing/mistyped fields, non-positive integer number —
   each asserted with its exact factual reason. No mutating gh command can be
   constructed: the fake-gh argv log is asserted to equal exactly the two templates,
   and every logged argv is scanned for forbidden verbs/flags
   (create/edit/close/merge/comment/approve/ready/lock/unlock/update/delete/remove) —
   none present.
3. **Check 3 semantics.** Fixture-asserted: PASS when the operational adapter resolves
   a matching open PR (branch, head, state all agree); BLOCKED with the adapter
   reason when identity is unresolvable (gh missing, gh failing — both with and
   without `--pr`); FAIL (never BLOCKED) for a genuine branch mismatch or PR-head
   mismatch. Operational: criterion 4 below.
4. **Operational PASS on the real remote.** Executed at the implementation head
   (while `origin/codex/29-oap-015-a-simplify-canary` still equaled the 015-a report
   commit `85b8749…`), with no fixture adapter (`test_mode_adapter: false`):

   Command:
   `python3 oap/bin/verify_report.py --repo . --id 015-a --pr 30 --head
   85b874969223e31ae06618f5a038ec99e22f0208 --remote origin`

   Exact `--json` output:

   ```json
   {
    "id": "015-a",
    "checks": {
     "report_only_changed_path": {
      "ok": true,
      "detail": "changed paths: ['oap/reports/015-a-simplify-canary.md']"
     },
     "implementation_head_first_parent": {
      "ok": true,
      "detail": "12ef602bac2bbdf027debccaa0766d2637dd84a7"
     },
     "remote_head_and_pr_identity": {
      "ok": true,
      "detail": "remote head 85b874969223e31ae06618f5a038ec99e22f0208 at report commit (branch codex/29-oap-015-a-simplify-canary), PR 30 bound"
     }
    },
    "status": "PASS",
    "test_mode_adapter": false
   }
   ```

   Plain form (same command, exit 0): `status=PASS` with all three checks `[ok]`.
   The exact outputs are also preserved in the private execution receipt.
5. **Suite and lint.** `env -u OAP_ROLE python3 -m unittest discover -s tests/oap
   -p 'test_*.py'` → `Ran 152 tests in 33.424s — OK`, 0 skipped (existing 131 + 21 new
   operational-path tests). `uv run ruff check .` → `All checks passed!`;
   `uv run ruff format --check .` → `179 files already formatted`;
   `git diff --check` → clean.
6. **CI at the implementation head `cdc846c…`.** CI run 34790971910: quality
   **success**, test **success**, container **success**, security **failure** — the
   failure is the identical pre-existing pip-audit baseline (see below), no new
   findings, no dependency change. oap run 34790971837: `oap-harness` **success**.
   PR #30 remains OPEN/MERGEABLE with head `cdc846c…`.
7. **015-a report validity and CI separation.** Stated above; the criterion-4
   operational output is recorded in this report; implementation-head CI (observed at
   authoring) and report-head CI are kept in separate sections, as below.

## Commands and exact results (at the implementation head, this host)

| Command | Result |
| --- | --- |
| `env -u OAP_ROLE python3 -m unittest discover -s tests/oap -p 'test_*.py'` | `Ran 152 tests in 33.424s — OK`, 0 skipped |
| `env -u OAP_ROLE python3 -m unittest discover -s tests/oap -p 'test_operational_pr.py'` | `Ran 21 tests in 2.913s — OK` |
| `uv run ruff check .` | `All checks passed!` |
| `uv run ruff format --check .` | `179 files already formatted` |
| `git diff --check` | clean |
| `python3 oap/bin/verify_report.py --repo . --id 015-a --pr 30 --head 85b874969223e31ae06618f5a038ec99e22f0208 --remote origin` | `status=PASS`, all three checks ok, `test_mode_adapter: false` (exact output above) |
| `python3 oap/bin/check_state.py --repo . --strategic-home <strategic home> --json` | `ACTIVE_PENDING`; pointer `015-b` ACTIVE; order FINAL, `pr_mode AMEND`, branch `codex/29-oap-015-a-simplify-canary` (order bytes committed this round validate under the slim parser) |
| `git ls-remote origin codex/29-oap-015-a-simplify-canary` | `cdc846cbb131f2ca7d936e6329ef1d0f903f1dd6` |
| `gh pr view 30 --json state,mergeable,headRefOid,headRefName` | `OPEN`, `MERGEABLE`, head `cdc846c…`, branch `codex/29-oap-015-a-simplify-canary` |

## Privacy, dependencies, DHA, limits

- No credentials, auth material, or private artifacts are contained in or referenced
  by this report (CP-09); the strategic home was inspected read-only
  (`check_state.py`).
- No dependency or tooling version change: `pyproject.toml`, `uv.lock` untouched. No
  product code, migration, data, CI workflow, or documentation change.
- DHA: the order declares `Decision: NONE`; no CRITICAL entry was appended or
  modified. This report-only commit changes no file other than this report.
- No merge, auto-merge, approval, or settings change performed or requested; the only
  remote mutation this round is pushing this branch.

## Implementation head CI (observed at authoring)

Observed at the exact implementation head `cdc846cbb131f2ca7d936e6329ef1d0f903f1dd6`:

- CI run 34790971910: quality **success**, test **success**, container **success**,
  security **failure**.
- oap run 34790971837: `oap-harness` **success**.
- The security failure is the **pre-existing baseline, identical, no waiver**:
  `uv run pip-audit` — "Found 20 known vulnerabilities in 4 packages"
  (django 5.2.15 ×7: PYSEC-2026-2090/2091/2092/3717; djangorestframework
  3.16.1 ×2: PYSEC-2026-3827/3828; pip 26.1.2 ×2: PYSEC-2026-3721; sqlparse
  0.5.5 ×9: PYSEC-2026-3696/3697/3698/3699/3923). Per-ID multiset diff against the
  main baseline run 34783895298 (same 20 findings, same 4 package versions):
  **empty — IDENTICAL_FINDINGS**. This PR changes no dependencies; the failure stays
  open until a separate human-directed action.

## Report head CI

NOT YET OBSERVED AT AUTHORING

The report commit does not exist while this report is being written; nothing about its
CI outcome can be claimed here. Post-publication observations (remote verification,
post-publication `check_state`, report-head CI) go to the private execution receipt,
never to a rewrite of this report (CP-07).

## Uncertainty, blockers, remaining limitations

- No blockers: the round completed its scope.
- By design, still BLOCKED/red and untouched: the pre-existing pip-audit failure (no
  waiver) and the operational doctor gate (unqualified `OAP_AUDIT_MODEL`; merge side
  effects not evidenced) — the correct state while development-merge delegation is
  disabled.
- Observation for strategy (not fixed — `oap/bin/publish_order.py` is not on this
  order's `allowed_paths`): with a degraded operational adapter (gh missing or
  failing), the strategy-side `pr_identity` step would phrase an unknown PR identity as
  "branch already has open PR None; CREATE_OR_RESUME reuses it" (the unknown dict is
  truthy). Cosmetic messaging only; recommend a follow-up order if desired.
- The reported 015-a residuals remain untouched as ordered (stale `doctor.sh`
  comment, `.dockerignore` line, historical docs).
- After this report commit advances the branch, the 015-a report's remote-head check
  targets a historical commit on the same branch; its verification evidence is
  anchored at its publication time (private receipt of 015-a), per CP-07. The
  criterion-4 verification above was executed while the branch head still equaled the
  015-a report commit, and is the ordered verification for this round.

## Next recommendation (not activation)

Strategy performs the OP-11 exact-head review of the combined 015-a+015-b diff at this
report head (015-a scope already reviewed clean by strategy; 015-b scope per the
evidence above), then the human merges PR #30. After merge/acceptance: reconcile
`oap/active` per the recovery protocol, run ICA at the exact merged revision, and
treat M-CONVERSION acceptance as the remaining independent gate. Drafts
016-a..020-a stay unchanged until then.
