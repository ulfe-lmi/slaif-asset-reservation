<!-- OAP-META
{
  "kind": "report",
  "id": "050-c",
  "order_path": "oap/orders/050-c-report-identity-binding.md",
  "order_sha256": "ca66251e23d668227993192bd9af1fd8e9853fdb15bad58920ada5f8c3a6a802",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 103,
  "pr_number": 104,
  "branch": "codex/103-oap-050-a-management-authority",
  "implementation_head": "d9d5dd10e12fec6a37dbd7e63545f0aa4a83b16a",
  "base_sha": "b873f4cf1071bded044ba456625b0ced355407a8",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "d9d5dd10e12fec6a37dbd7e63545f0aa4a83b16a",
    "runs": [
      {
        "run_id": 39090504796,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "success",
          "container": "success",
          "test": "success"
        }
      },
      {
        "run_id": 39090504759,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1207 passed, 1 warning in 600.25s (0:10:00)",
    "warning": "tests/test_product_entry.py:568 UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unrelated)",
    "oap_harness_summary": "Ran 160 tests in 31.282s / OK"
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING",
  "prior_binding_supplement": {
    "prior_report_commit": "2ae6c3ea24a320018137d04426282dc12cb9bbff",
    "prior_report_path": "oap/reports/050-b-operator-authorization-guide.md",
    "prior_order_path": "oap/orders/050-b-operator-authorization-guide.md",
    "prior_order_sha256": "f3abb5bdd9ceb83264b6bc2ce3d39b5a45c5779286e1333e9b5084420a9921af",
    "prior_report_head_ci": {
      "run_id": 39089469880,
      "workflow": "CI",
      "conclusion": "failure",
      "failed_job": "test",
      "failure": "FAILED tests/oap/test_ba26_27_40_41_wrapper.py::Ba26ZeroIdle::test_ba26_consumption_journalized - AssertionError: 'invoked' not found in ['control_consumed'] (1 failed, 1206 passed, 1 warning in 502.49s)",
      "other_jobs": {
        "quality": "success",
        "security": "success",
        "container": "success"
      },
      "oap_run_id": 39089469912,
      "oap_conclusion": "success"
    }
  }
}
-->

# 050-c — execution report: reliable complete publication evidence

Implementation head SHA: d9d5dd10e12fec6a37dbd7e63545f0aa4a83b16a
Report publication commit: SELF

## Identity and result

COMPLETE for order 050-c (D0, publication evidence only) on the same
issue #103 / PR 104 (AMEND) / branch
`codex/103-oap-050-a-management-authority`, base main
`b873f4cf1071bded044ba456625b0ced355407a8` unchanged; started at the
exact 050-b report commit
`2ae6c3ea24a320018137d04426282dc12cb9bbff`. Order
`oap/orders/050-c-report-identity-binding.md` (state FINAL; current file
digest sha256
`ca66251e23d668227993192bd9af1fd8e9853fdb15bad58920ada5f8c3a6a802`,
computed from the published bytes, not a Git object ID). All eight order
`source_hashes` were recomputed from file bytes and match exactly. No
merge, no auto-merge, no self-approval, no CRITICAL mutation, no
deployment, no real user/data/DB/host/secret work.

Prior binding supplement: the published 050-b report (commit
`2ae6c3ea24a320018137d04426282dc12cb9bbff`, path
`oap/reports/050-b-operator-authorization-guide.md`) carried no OAP-META
block and no order digest, and as an immutable published report cannot
be rewritten. Its order is
`oap/orders/050-b-operator-authorization-guide.md` with actual blob
sha256
`f3abb5bdd9ceb83264b6bc2ce3d39b5a45c5779286e1333e9b5084420a9921af`
(recomputed and matching). Earlier 050-a/b order and report bytes remain
immutable and untouched.

## Acceptance evidence

1. **BA26 wait repair — PASSED.**
   `tests/oap/test_ba26_27_40_41_wrapper.py::test_ba26_consumption_journalized`
   now reads one atomic `state.json` journal snapshot and waits until
   BOTH `control_consumed` and `invoked` event kinds are observed in that
   same read before leaving the loop; the existing 10s deadline, both
   presence assertions, the control_consumed-before-invoked ordering
   assertion, the fake client/process cleanup and all other negative
   cases are unchanged, and `oap_launch.py`/FIFO/client/runtime were not
   touched (no helpers, no framework, no increased sleeps or timeouts,
   no weakened or skipped assertions, no retry-until-green). The root
   cause matches the actual 050-b report-head CI failure 39089469880
   (`AssertionError: 'invoked' not found in ['control_consumed']`): the
   runtime journals the two events as separate durable atomic writes.
2. **Complete report identity metadata — PASSED.** This report begins
   with a complete `OAP-META` block consistent with the prior 050-a
   format; every required key was parsed and value-checked privately
   before commit (kind, id, order_path, order_sha256, repo,
   issue_number, pr_number, branch, implementation_head, result,
   observed_implementation_ci, report_head_ci, base_sha).
   `order_sha256` is the current published 050-c order digest (not
   borrowed from 050-b); `implementation_head` is the actual literal new
   non-report HEAD; `report_head_ci` is NOT YET OBSERVED AT AUTHORING.
3. **Prior binding and CI record — PASSED.** The metadata supplement
   carries the missing 050-b binding; the actual 050-b report-head CI
   run 39089469880 failure (test job: 1 failed, 1206 passed, 1 warning
   in 502.49s; quality/security/container success; oap run 39089469912
   success) and the current-head repair are recorded accurately above.
4. **Git delta and publication structure — PASSED at commit.** The
   implementation commit changes exactly the BA26 wait condition, the
   050-c order file and `oap/active`; every other byte is identical to
   `2ae6c3ea24a320018137d04426282dc12cb9bbff`. This report is the only
   file changed by the final commit, whose first parent is the
   implementation head. Remote publication verification is recorded in
   the private receipt; report-head CI is separate and NOT YET OBSERVED
   AT AUTHORING.

## Changed files and scope

- `tests/oap/test_ba26_27_40_41_wrapper.py` — wait condition only
  (+8/-2 lines); all other test logic byte-identical.
- `oap/orders/050-c-report-identity-binding.md` — exact published order
  (state FINAL).
- `oap/active` — `050-b` -> `050-c`.

No product, docs, model, migration, asset, API, settings, dependency,
deploy, proxy, production or OAP-helper changes; no CRITICAL change.
`git diff --name-status 2ae6c3e..d9d5dd1` lists exactly those three
paths (119 insertions, 3 deletions in total).

## Commands and results

- Focused stdlib file, OAP_ROLE unset:
  `python3 -m unittest discover -s tests/oap -p 'test_ba26_27_40_41_wrapper.py' -v`
  -> PASSED, `Ran 6 tests in 11.461s / OK`, including
  `test_ba26_consumption_journalized`.
- `ruff check` and `ruff format --check` on the changed file (local
  pre-check; authoritative in the CI quality job): all checks passed /
  1 file already formatted.
- sha256sum of the eight order `source_hashes`: all match. PASSED.
- `git diff --stat 2ae6c3e..d9d5dd1`: 3 files, 119(+)/3(-). PASSED.
- Local product/browser/FULL OAP harness/rehearsal/container/restore/
  Gunicorn/HTTPS: NOT RUN by order; the 1207-test product evidence and
  all runtime/PG/browser/docs evidence are reused by byte identity and
  re-observed in the full normal CI at the exact implementation head.

## CI observed before authoring

At implementation head `d9d5dd10e12fec6a37dbd7e63545f0aa4a83b16a`:

- CI run **39090504796** (workflow `CI`): quality success, security
  success, container success, test success — summary
  `1207 passed, 1 warning in 600.25s (0:10:00)`; the single warning is
  the pre-existing `UserWarning: Overriding setting DATABASES...` in the
  intentional DB-unavailable negative test
  `tests/test_product_entry.py::test_error_rendering_is_safe_when_db_is_unavailable`,
  unrelated to this round.
- oap run **39090504759** (workflow `oap`): oap-harness success —
  `Ran 160 tests in 31.282s / OK`.

All five required implementation-head checks observed PASS. The prior
050-b report-head failure (run 39089469880, test job 1 failed /
1206 passed) is recorded as superseded by this repair; it was neither
waived nor blindly rerun. Report-head CI at this publication commit is
**NOT YET OBSERVED AT AUTHORING**; it is observed separately outside the
model. Later publication verification goes to the private receipt.

## Security, data, dependencies and local tools

No secrets, credentials or private data in this report or the change; no
real users, data, databases, hosts, secrets, exposure, DNS, TLS or
firewall work; no deployment. Tools used: git, gh (run watch/logs),
python3 (focused unittest and JSON metadata check), sha256sum, repo
`.venv` ruff. No new dependencies; no lockfile change. No merge, no
auto-merge, no delegation.

## DHA outcome and unresolved gates

Deferred human adjudication outcome per the order: **Decision: NONE**.
No CRITICAL entry appended, no gate cleared, no adjudication requested
or performed by coding.

## Limitations and recommendation

- Report-head CI not yet observed at authoring; strategy performs the
  frozen-head review and the required report-head CI.
- This evidence-only round costs one full CI cycle without feature
  change, by design; the delta is one test wait condition plus
  publication records.
- Bearer `reservations:read_all`/issuance and the fresh independent
  closure at the exact merged revision remain separate follow-up scope;
  no merge, release, deployment or self-certification is made here.
