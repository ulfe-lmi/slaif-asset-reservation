<!-- OAP-META
{
  "kind": "report",
  "id": "048-c",
  "order_path": "oap/orders/048-c-deterministic-verification-clock.md",
  "order_sha256": "c42d8f896de93a360e273cdc32e2af26fd6c9661f8879a4bc5f42a4c3bdae536",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 99,
  "pr_number": 100,
  "branch": "codex/99-oap-048-a-authorization-foundation",
  "implementation_head": "e4888930dab1d10b3585b1b1796ddcdf64342136",
  "base_sha": "1baffe27a66609944f4d7b8e5c12dc69dfaa00b9",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "e4888930dab1d10b3585b1b1796ddcdf64342136",
    "runs": [
      {
        "run_id": 39065594094,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      },
      {
        "run_id": 39065594175,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "success",
          "container": "success",
          "test": "success"
        }
      }
    ]
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 048-c — deterministic fake construction timestamp for required CI

Implementation head SHA: e4888930dab1d10b3585b1b1796ddcdf64342136
Report publication commit: SELF

COMPLETE for the 048-c deterministic verification clock (D0,
verification-only). Same objective 48, issue 99, SAME branch
`codex/99-oap-048-a-authorization-foundation`, SAME PR #100 (AMEND; body
updated via structured REST with a concise 048-c verification note,
`Closes #99` retained), original main base
`1baffe27a66609944f4d7b8e5c12dc69dfaa00b9`, started from frozen 048-b
report head `59380287b1e12ad89af2e76d86cf51a14bccc21a` (implementation
`f6eca5b1f91dfa57640fe04aa1e31a27c93ec2cd`). The only non-order/pointer
change is the fake construction fixture in
`tests/test_qualification_image_ownership.py` plus one deterministic
regression in the same file. The normal FULL CI at the implementation
head is fully green (1116 passed). No merge, no auto-merge, no CRITICAL
mutation, no deployment, no real DB/data/exposure operation, no
application code change.

## Demonstrated blocking boundary (recap)

CI run 39062814291 (head f6eca5b, attempts 1-2, each 1114 passed /
1 failed) failed `test_cached_created_requires_actual_construction_proof`
because the simulated build left the IID file with an uncoordinated
filesystem timestamp measured 36 microseconds (attempt 1:
1792266034.944909 < 1792266034.9449453) and 350 microseconds (attempt 2:
1792266708.6291215 < 1792266708.6294715) behind the wall clock the
unchanged helper (`tests/test_branding.py` `_OwnedDocker.build_image`)
sampled just before, so a fresh output was misclassified stale. These
attempts are recorded here as HISTORICAL evidence only; no retroactive
PASS is claimed for them.

## Acceptance evidence (order items 1-5)

1. **Fake IID timestamps are deterministic; helper untouched.**
   - `tests/test_qualification_image_ownership.py` only:
     `simulated_build` now takes `clock` (default: coarse 1-second
     wall-referenced logical tick, exact float) and
     `legacy_wall_mtime`; a `_LogicalTime` shim replaces the branding
     module's `time` binding only, so the helper's sampled `started` and
     the fake build's IID file stamp come from the same controlled clock.
     Successful simulated builds explicitly stamp the IID file with
     `os.utime` from that clock — deliberately fresh, consistent with the
     sampled start, independent of real filesystem/wall coordination.
   - `tests/test_branding.py` byte-identical to 048-b (SHA-256
     `a30ad41ef6fad44cfa729d8426dcd1f134888e54ad5c4f11c2a5af1ee5bfe816`
     at the implementation head); no host/system clock change; no
     sleeps/tolerances/probability loops; no assertion weakening; no
     catch/skip of the failure.
2. **Protections retained and skew regression proven deterministically.**
   - New
     `test_skewed_clock_rejects_legacy_fixture_and_accepts_fixed_fixture`:
     under one deliberately skewed logical clock (wall + 1 s), a legacy
     wall-timestamped output (timestamp pinned to the real wall at fixture
     setup, so the skew is provable with no probability loop) is refused
     as `"stale image construction output"` with zero adoption/cleanup,
     while the fixed fixture satisfies the full positive construction
     contract (build, remember receipt, exact cleanup of the constructed
     ID).
   - Existing protections all retained and passing: the deliberate
     `stale` fault (mtime 1, older than the controlled start), plus
     symlink (`O_NOFOLLOW`), malformed ID, wrong-id, wrong-nonce,
     missing/naive Created, named-image, foreign-tag race,
     no-unproven-cleanup and changed-receipt refusals.
   - The unchanged real Docker warm-cache test
     (`test_real_warm_cache_repeat_and_post_build_failure_cleanup`) keeps
     real time and ran in CI (real Docker available) as part of the 17/17
     file pass below.
3. **Everything else byte-identical to 048-b.**
   - Non-report implementation diff at `e488893` touches exactly
     `tests/test_qualification_image_ownership.py` (+ committed order/
     pointer bytes); `git status` clean afterwards. All application,
     runtime, authorization, user-field, migration, Group/permission,
     engine, proxy, dependency, inventory, docs code identical to 048-b;
     earlier 048-a/b orders and reports untouched.
4. **Bounded local runs (owned Python 3.13.14 copy, owned resources).**
   - Owned temp root `~/codex-work/slaif-auth-048-922064` (0700) source
     copy synced with the changed test file; owned synthetic PostgreSQL 17
     container (receipt CID `7680db038ece…`, loopback port) env only.
   - `env -u OAP_ROLE .venv/bin/python -m pytest -v --deselect
     tests/test_qualification_image_ownership.py::test_real_warm_cache_repeat_and_post_build_failure_cleanup
     tests/test_qualification_image_ownership.py` → PASSED 16 passed,
     1 deselected (1.86 s); repeated 3x (`-q --no-cov`) → PASSED 16
     passed each (0.10/0.10/0.09 s), demonstrating determinism.
   - `env -u OAP_ROLE python3 -m unittest discover -s tests/oap -p
     'test_*.py'` → PASSED: Ran 160 tests, OK (36.1 s).
   - `.venv/bin/ruff check .` → PASSED ("All checks passed!");
     `.venv/bin/ruff format --check .` → PASSED (227 files already
     formatted); `git diff --check` → PASSED (clean).
   - No local full pytest, no operational/rehearsal/HTTPS/Gunicorn/
     restore/visual tests, no new dependencies; the real warm-cache case
     was deselected locally and ran in CI instead.
5. **Publication.**
   - Non-report work (order `oap/orders/048-c-deterministic-verification-clock.md`,
     pointer `oap/active` = `048-c` + fixture) committed as
     `e4888930dab1d10b3585b1b1796ddcdf64342136` and pushed; PR #100
     amended in place (no new PR/issue). PR body updated via structured
     REST (`gh api … pulls/100 --input`): concise 048-c verification note
     (deterministic fake IID timestamps; actual ownership validation,
     runtime and authorization semantics unchanged; `tests/test_branding.py`
     byte-identical); `Closes #99` retained.
   - Normal FULL CI observed at the implementation head
     `e4888930dab1d10b3585b1b1796ddcdf64342136`:
     - CI run 39065594175: quality success (19 s), security success
       (16 s), container success (31 s), test success (9 m 14 s). Test
       log: `tests/test_qualification_image_ownership.py` 17/17 dots and
       `1116 passed, 1 warning in 487.63s (0:08:07)` — the single warning
       is the pre-existing `test_product_entry.py` DATABASES-override
       `UserWarning`, unrelated to this change.
     - oap run 39065594094: oap-harness success (42 s).
   - This report is the only file changed in the publication commit,
     whose first parent is the implementation head; report-head checks
     are NOT YET OBSERVED at authoring and are separate from the
     implementation CI above.

## Limits / uncertainties

- Report-head CI not observed at authoring (must run before any
  conditional merge; a report-head failure goes to a next strategy
  suffix, not a rewrite of this report).
- Local verification used the mocked cases only (real Docker warm-cache
  deselected locally); the real construction proof ran in CI at the
  implementation head.
- Target gate unchanged: authorization foundation for continued
  development only; the complete selected authorization milestone still
  requires its ordered enforcement/read-only interfaces, qualification
  and a fresh independent ICA at the exact merged revision. No
  deployment, no audit claim, no ICA acceptance.
