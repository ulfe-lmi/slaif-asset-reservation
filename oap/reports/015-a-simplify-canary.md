<!-- OAP-META
{
 "kind": "report",
 "id": "015-a",
 "order_path": "oap/orders/015-a-simplify-canary.md",
 "order_sha256": "08309a4db20c73f3ccd29183b14169bb8cda81feb7a6e9c2dcce1b75d7f1eab9",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 29,
 "pr_number": 30,
 "branch": "codex/29-oap-015-a-simplify-canary",
 "implementation_head": "12ef602bac2bbdf027debccaa0766d2637dd84a7",
 "base_sha": "14fc20b1ff52788974fd3f282322afc9d71362f9",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "12ef602bac2bbdf027debccaa0766d2637dd84a7",
  "runs": [
   {"run_id": 34788565005, "workflow": "CI", "jobs": {"quality": "success", "test": "success", "security": "failure", "container": "success"}},
   {"run_id": 34788565010, "workflow": "oap", "jobs": {"oap-harness": "success"}}
  ],
  "security_note": "failure limited to the identical pre-existing pip-audit findings of main run 34783895298 (per-ID multiset diff empty); no dependency changes; reported, not fixed, not waived"
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 015-a report — simplify the Concentrated OAP orchestration layer (round-trip canary)

Order digest: 08309a4db20c73f3ccd29183b14169bb8cda81feb7a6e9c2dcce1b75d7f1eab9

Implementation head SHA: 12ef602bac2bbdf027debccaa0766d2637dd84a7

Report publication commit: SELF

**Result: COMPLETE** — order 015-a implemented exactly within `allowed_paths`; the
executed round is the M-CONVERSION round-trip canary, proven by
`tests/oap/test_roundtrip_canary.py` on a fixture repo with explicit fake adapters
and a real temporary POSIX FIFO, and by this round's own remote publication.

## What changed

One governance-only round (no product behavior change):

- `ci.yml`: removed the `sha256sum -c MANIFEST.sha256` step and the oap harness
  step from the product quality job (other quality steps unchanged).
- New `.github/workflows/oap.yml`: `oap-harness` job (ubuntu-24.04, Python 3.13,
  `python3 -m unittest discover -s tests/oap -p 'test_*.py' -v`), path-gated to
  `oap/**`, `tests/oap/**`, and the workflow file itself, for both
  `pull_request` and `push` (push: `main`).
- `oap/bin/oaplib.py` + `oap/bin/publish_order.py`: slim final order schema —
  exactly 9 meta fields (`id`, `round`, `base_sha`, `issue_number`, `branch`,
  `pr_mode`, `previous_round`, `allowed_paths`, `forbidden_resources`) plus the
  DHA body declaration (10 total) — enforced by the publisher; the slim parser
  accepts published superset orders (including this 25-field order) with
  `pr_number`/`state` normalization defaults so protected `check_state.py`
  keeps working; two recoverable writes, dry-run zero-write, pointer atomicity,
  role/activation guards and the superset `pr_number` binding path unchanged.
- `oap/bin/verify_report.py`: verification reduced to exactly three checks —
  `report_only_changed_path`, `implementation_head_first_parent`,
  `remote_head_and_pr_identity` (`--pr` optional; missing remote evidence
  returns BLOCKED, never a local pass).
- `oap/bin/oap_doctor.py`: only `structural` + `operational` dimensions
  (setup/governance-identity/adoption removed); the operational gate still
  blocks on merge side effects (not evidenced) and an unqualified
  `OAP_AUDIT_MODEL`.
- Byte-identical moves (17 `R100` renames): `MANIFEST.sha256`,
  `oap/governance/{MANIFEST.json,DISTILLATION-MAP.md,CONTEXT-BUDGET.md}`,
  `oap/bootstrap-sources.lock.json`,
  `oap/bin/{check_governance.py,oap_materialize.py,bootstrap-two-agent-oap.sh}`,
  `oap/COMPLETENESS.md`,
  `oap/templates/{STRATEGIC-REVIEW-CHECKLIST.md,HANDOFF-TEMPLATE.md}` to
  `docs/bootstrap/archive/` (with new `ARCHIVE-NOTE.md`); `oap/audit/*` to
  `docs/audit/`. `oap/bin/check_ica.py` stays.
- `tests/oap`: deleted BA files whose sole subject is removed machinery (ba00,
  ba02, ba03, ba06, ba07, ba12, ba14); trimmed/updated surviving suites to the
  slim schema; added `test_roundtrip_canary.py`.
- Docs to the slim round: `oap/coding-instructions/TESTING-CORE.md` (TC-04),
  `TESTING.md`, `oap/README.md` (this round named the first operational round
  and the round-trip canary), `docs/OAP-RUNBOOK.md`.
- Round bytes: `oap/orders/015-a-simplify-canary.md` (immutable, digest above)
  and `oap/active` (exactly `015-a\n`) committed with the implementation; this
  report is the report-only commit on top.

Commit `12ef602`: 53 files changed, 1157 insertions(+), 1828 deletions(-).
One incidental mode change: `oap/bin/verify_report.py` gained a shebang
(`#!/usr/bin/env python3`) and the executable bit (100644 → 100755); the file
is on the order's `allowed_paths` and the change is cosmetic.

## Numbered acceptance evidence (against the order's 11 criteria)

1. **Product bytes unchanged.** Base-to-head diff checked file-by-file against
   the order's `allowed_paths`: result `SCOPE_OK`, zero out-of-scope paths;
   zero changes under `src/`, `data/`, migrations, product tests outside
   `tests/oap/`, `pyproject.toml`, `uv.lock`. All 17 renames are `R100`
   (byte-identical).
2. **MANIFEST.sha256 deleted with references removed.** Moved byte-identical to
   `docs/bootstrap/archive/MANIFEST.sha256`; the verification step is gone from
   `ci.yml`; references removed from `TESTING.md` and
   `oap/coding-instructions/TESTING-CORE.md`; `ARCHIVE-NOTE.md` documents the
   archive. No manifest regeneration (no manifest file exists outside the
   archive). Residual references, not fixed (outside the order's reference
   removal list or protected): stale line in `.dockerignore`, historical
   pre-concentration documents (`BOOTSTRAP_INSTRUCTIONS.md`,
   `docs/BOOTSTRAP-SOURCES.md`, `docs/bootstrap/1/`), generic `MANIFEST` entry
   in `.gitignore`, and the immutable order text itself.
3. **Product CI quality job no longer runs the oap harness.** `ci.yml` quality
   job otherwise unchanged; `oap.yml` runs the harness path-gated as specified.
   Observed at the implementation head: `oap/oap-harness` SUCCESS (run
   34788565010).
4. **Slim schema, 10 fields, superset accepted.** Publisher enforces the 10
   fields; `test_ba18_superset_order_accepted` parses this 25-field order as a
   valid superset and the suite is green (131/131).
5. **Verification = exactly the three checks.** The rewritten verifier performs
   exactly `report_only_changed_path`, `implementation_head_first_parent`,
   `remote_head_and_pr_identity` (asserted by the surviving ba28–32 tests and
   the canary). Remote PASS for this round requires the report commit to
   exist, so `verify_report.py` is executed against the real remote only after
   publication; its result is recorded in the private execution receipt, not
   here (CP-07). The required remote evidence already exists at authoring:
   PR #30 open, `origin/codex/29-oap-015-a-simplify-canary` at the
   implementation head, report commit parentage by construction (first parent
   is the implementation head).
6. **Doctor dimensions.** Local runs (command section): structural OK;
   operational BLOCKED with exactly the ordered reasons (unqualified
   `OAP_AUDIT_MODEL`; active order present). Setup/governance-identity/adoption
   dimensions are gone.
7. **Byte-identical archive.** All 17 renames `R100`; `oap/bin/check_ica.py`
   remains and still validates an ICA request fixture (ba46–48 suite green, no
   skips).
8. **Round-trip canary test.** `test_roundtrip_canary.py` passes
   (1 test OK, 1.4 s, real temp POSIX FIFO, real `oap_launch.py` wrapper,
   explicit fake client/remote adapters, finite timeouts) and proves:
   (a) dry-run zero writes (snapshot-equal); (b) immutable order bytes,
   pointer exactly `b"001-a\n"`, journal `order_written` before `signaled`,
   consumer received exactly `b"OK"`; (c) one control OK ⇒ exactly 1
   invocation (`OAP_ROLE=CODING`, correct cwd/CODEX_HOME, prompt "already
   consumed", journal `control_consumed` < `invoked`), clean SIGTERM;
   (d) fake coding round commits order/pointer, creates the PR **before**
   report composition, appends a report-only commit whose first parent equals
   the implementation head; (e) verifier PASS with exactly the three checks;
   (f) state trace ACTIVE_PENDING → REPORT_PUBLISHED → INACTIVE after pointer
   clear; (g) two duplicate wake-ups ⇒ still exactly 1 invocation total.
9. **Surviving suite.** 131 tests, OK, 0 skipped (command section); the 7
   deleted BA files are gone; no test references a removed helper (suite green,
   ruff clean).
10. **Documentation.** TC-04/TESTING.md/oap/README.md/OAP-RUNBOOK.md updated to
    the slim round with no stale references to removed files; `oap/README.md`
    names 015-a the first operational round and the round-trip canary.
11. **Measured canary evidence (this round, real remote):**
    - Wrapper single consumption, this round's durable journal
      (`workorders/state.json`, read-only): `order_written` (order sha256
      `08309a4d…`, matching the committed order bytes) → `control_consumed`
      (ts 1789337992.9096) → `invoked` (ts 1789337992.9654); exactly one
      control OK consumed before exactly one invocation.
    - Exact FIFO OK bytes: `4f4b` (two ASCII `OK`, no LF) — asserted in the
      canary test on the real temp FIFO; the final response signal of this
      round is sent only after verified remote publication (CP-07), hence not
      claimable inside this report.
    - Real PR number: **30** (created before report composition;
      `headRefOid` = implementation head; state OPEN; MERGEABLE).
    - Literal implementation head: see the `Implementation head SHA:` line
      above; `origin` branch head and PR head verified at that object.
    - Report-head CI: see `## Report head CI` — not observed at authoring.
    - Security baseline: see below — identical, pre-existing, no waiver.

## Commands and exact results (at the implementation head, this host)

| Command | Result |
| --- | --- |
| `env -u OAP_ROLE .venv/bin/python -m unittest discover -s tests/oap -p 'test_*.py'` | `Ran 131 tests … OK`, 0 skipped |
| `env -u OAP_ROLE .venv/bin/python -m unittest discover -s tests/oap -p 'test_roundtrip_canary.py' -v` | `Ran 1 test in 1.402s OK` |
| `.venv/bin/ruff check .` / `.venv/bin/ruff format --check .` | `All checks passed!` / `178 files already formatted` |
| `git diff --check` | clean |
| `python3 oap/bin/check_state.py --repo . --strategic-home <strategic home> --json` | `ACTIVE_PENDING`; pointer `015-a` ACTIVE; order `state=FINAL`, `pr_number=null` (slim normalization default; the real remote PR #30 exists and was verified via `gh`/`git ls-remote` — the operational remote API is unconfigured on this host, so `check_state` reports the fixture-note rather than a remote read; the fixture adapter is never selected silently, OP-10) |
| `python3 oap/bin/oap_doctor.py --level structural …` | `[structural] OK` |
| `python3 oap/bin/oap_doctor.py --level operational …` | `[operational] BLOCKED` — `OAP_AUDIT_MODEL not qualified`; `active order present; reconcile before a new operational session` (both ordered for this round) |
| `git ls-remote origin codex/29-oap-015-a-simplify-canary` | `12ef602bac2bbdf027debccaa0766d2637dd84a7` |
| `gh pr view 30 --json headRefOid,state,mergeable` | head `12ef602…`, `OPEN`, `MERGEABLE` |

## Privacy, dependencies, DHA, limits

- No credentials, auth material, or private artifacts are contained in or
  referenced by this report (CP-09); the strategic home was inspected
  read-only for the journal evidence.
- No dependency or tooling version change: `pyproject.toml`, `uv.lock`
  untouched.
- DHA: the order declares `Decision: NONE` (decision_class D0); no CRITICAL
  entry was appended or modified; no `Decision: APPEND` occurred. This
  report-only commit changes no file other than the report.
- No model/provider calls, no lab/Neumann access, no product data touched.
- No merge, auto-merge, approval, or settings change performed or requested;
  delegation remains disabled, so the human merges after strategy review.

## Implementation head CI (observed at authoring)

Observed at the exact implementation head
`12ef602bac2bbdf027debccaa0766d2637dd84a7`:

- CI run 34788565005: quality **success**, test **success**, container
  **success**, security **failure**.
- oap run 34788565010: `oap-harness` **success**.
- The security failure is the **pre-existing baseline, identical, no waiver**:
  `uv run pip-audit` — "Found 20 known vulnerabilities in 4 packages"
  (django 5.2.15 ×7: PYSEC-2026-2090/2091/2092/3717; djangorestframework
  3.16.1 ×2: PYSEC-2026-3827/3828; pip 26.1.2 ×2: PYSEC-2026-3721; sqlparse
  0.5.5 ×9: PYSEC-2026-3696/3697/3698/3699/3923). Per-ID multiset diff against
  main baseline run 34783895298 (same 20 findings, same 4 package versions):
  **empty — IDENTICAL_FINDINGS**. This PR changes no dependencies; the
  failure stays open until a separate human-directed action.

## Report head CI

NOT YET OBSERVED AT AUTHORING

The report commit does not exist while this report is being written; nothing
about its CI outcome can be claimed here. Post-publication observations
(verify_report result, post-publication `check_state`, report-head CI) go to
the private execution receipt, never to a rewrite of this report (CP-07).

## Uncertainty, blockers, remaining limitations

- No blockers: the round completed its scope.
- By design, still BLOCKED/red and untouched: operational doctor gate
  (unqualified audit model; merge side effects not evidenced — this is the
  correct state while development-merge delegation is disabled) and the
  pre-existing pip-audit failure.
- Known residuals reported, not fixed (protected or out of scope):
  `oap/bin/doctor.sh` stale dimension comment; `.dockerignore` stale
  `MANIFEST.sha256` line; historical MANIFEST mentions in pre-concentration
  documents listed under acceptance item 2.
- `check_state.py` remote section on this host reflects the unconfigured
  operational remote API (see command table); remote identity was instead
  verified directly via `gh` and `git ls-remote`.

## Next recommendation (not activation)

Strategy performs the OP-11 exact-head review of the full diff at the
implementation head and this report commit (ordered scope, strongest concrete
reason not to merge, combined risk, jobs at the exact heads), then the human
merges PR #30. After merge/acceptance: reconcile `oap/active` per the
recovery protocol, run ICA at the exact merged revision, and treat
M-CONVERSION acceptance as the remaining independent gate. Drafts 016-a..020-a
stay unchanged until then.
