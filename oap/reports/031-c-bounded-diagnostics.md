<!-- OAP-META
{
 "kind": "report",
 "id": "031-c",
 "order_path": "oap/orders/031-c-bounded-diagnostics.md",
 "order_sha256": "fe9aa786f4e03238cb20269fd1437f8178a660b1f8bfbb5e38d856dc8c94ac25",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 61,
 "pr_number": 62,
 "branch": "codex/61-oap-031-a-gunicorn-idle-connections",
 "implementation_head": "8cf02be0dd897534f4a52a09c41bbac438a1d46c",
 "base_sha": "696b87965920817f1a6b36589562a4af68e75497",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "8cf02be0dd897534f4a52a09c41bbac438a1d46c",
  "runs": [
   {"run_id": 37175041881, "workflow": "CI", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 37175041840, "workflow": "oap", "event": "pull_request", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 031-c report — bounded readiness-failure diagnostics before cleanup (finite log_tail while the server is alive, live-process failure regression)

Order digest: `fe9aa786f4e03238cb20269fd1437f8178a660b1f8bfbb5e38d856dc8c94ac25`
(committed `oap/orders/031-c-bounded-diagnostics.md`, strategy-published
order bytes as found in the working tree; no rename/move). Active pointer
`oap/active` = `031-c` + LF (verified by xxd: `3033 312d 630a`, 6 bytes).

Implementation head SHA: 8cf02be0dd897534f4a52a09c41bbac438a1d46c

Report publication commit: SELF

**Result: COMPLETE** — all three numbered acceptance criteria met. The round
changes exactly one file of the implementation,
`tests/test_gunicorn_responsiveness.py` (bounded failure diagnostics /
startup cleanup only), and publishes the round bytes (order + active
pointer). All 031-a/031-b configuration, docs, orders and report bytes are
preserved. No application, domain, auth, policy, UI, dependency, migration,
runtime-config, workflow, or governance byte changed. This amends PR #62
(same issue 61, same branch); the previous 031-a/031-b reports remain
historical and were not rewritten. Development merge candidate only; no
deployment, release, ICA or physical-resource consequence is claimed.

## 1. Starting state and E-list reconciliation (verify, do not assume)

Ordered reads completed: root router →
`oap/coding-instructions/AGENTS.md` → `ARCHITECTURE-for-agents.md` →
`OAP-COMMUNICATION-coding-agent.md` → exact active order (pointer
`oap/active` = `031-c` + LF →
`oap/orders/031-c-bounded-diagnostics.md`, `state: FINAL`,
`pr_mode: AMEND`, `previous_round: 031-b`, `decision_class: D0`,
`Decision: NONE`) → `SECURITY-CORE.md` / `TESTING-CORE.md` → the order's
scoped set: the single ordered implementation file
`tests/test_gunicorn_responsiveness.py` as committed at the 031-b
implementation head. No wildcard or strategic-history loading. The wrapper
had already consumed the control wake-up; it was not consumed again.

Reconciliation before edit (remote/local, C-06; AMEND round c resumes the
same objective):
- Branch `codex/61-oap-031-a-gunicorn-idle-connections` local = remote =
  `464d54d36ad6f55eb942e50c292bb196c82ed674` (031-b report head). That
  commit's first parent is
  `fe29e5640fd35945f3a9a835377aecbf617eb6a6`, the exact 031-b
  implementation head named in the order's E-list.
- PR #62: `state: OPEN`, `headRefOid:
  464d54d36ad6f55eb942e50c292bb196c82ed674`, head branch = the branch above,
  base `main` (`696b87965920817f1a6b36589562a4af68e75497` = order
  `base_sha` = local/remote `main`), `mergeable: MERGEABLE`,
  `autoMergeRequest: null`; PR body ends with `Closes #61`. One PR for the
  objective; no second PR created or amended.
- E-list report 464d54d verified against the actual remote PR #62:
  report-only first parent `fe29e5640fd35945f3a9a835377aecbf617eb6a6`
  (`git log -1 --format='%H %P' 464d54d`).
- E-list "all five implementation checks success at fe29e56" independently
  re-observed via the GitHub runs API filtered by
  `head_sha=fe29e5640fd35945f3a9a835377aecbf617eb6a6`: CI run
  37174172334 and oap run 37174172333, both conclusion `success`.
- Source hashes verified against the order via `sha256sum` in this
  checkout: `ARCHITECTURE.md`
  `8483a070026f382bb9b698e9346f3cb33f7dea44f8190b231431585986ebb17d`,
  `PLAN.md` `d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06`
  (both equal to the order's `source_hashes`).
- Working tree at start: tracked state clean at `464d54d` except the
  ordered round bytes — `oap/active` modified (`031-b` → `031-c`) and
  untracked `oap/orders/031-c-bounded-diagnostics.md`. No
  foreign/dirty files existed to preserve; no reset/clean/stash/force-push
  performed.
- The exact fault named in the order was confirmed in the committed
  031-b test bytes before editing: the readiness-failure assertion
  messages in
  `test_gthread_shutdown_cleans_children_on_failure` and
  `test_gthread_cleanup_survives_injected_failure`
  (`assert server.wait_ready(), f"server not ready; log tail:\n{server.log_tail()}"`)
  evaluate `log_tail()`, which performed an unbounded
  `self.proc.stdout.read()`, BEFORE the assertion raises and before any
  `finally` teardown runs. If the owned gunicorn process is still alive
  when readiness fails (the strategy-owned reproduction shape: real
  Gunicorn, 1 worker/2 threads, became ready, `log_tail` called on the
  live process in an owned daemon thread did not return within 500 ms,
  stopping the process reaped 0 orphans and terminated the reader), the
  pipe has no EOF and the read blocks indefinitely, holding up the very
  failure path whose job is to clean up. The E-list also records that the
  system-Python attempt failed readiness because that interpreter lacks
  the required application environment (owned cleanup 0) and that the
  successful reproduction used the repo venv interpreter; this round runs
  the identical shape under the repo venv (`uv run`, CPython 3.13,
  Gunicorn 23.0.0). No existing service or database was touched by any
  step.

## 2. Acceptance evidence (ordered criteria)

**Criterion 1 — log diagnostics finite even while Gunicorn is alive.
PASSED.**
- `GunicornServer.log_tail()` is now finite on every exit path: while
  `self.proc.poll() is None` (process alive) it returns the bounded marker
  `LIVE_LOG_MARKER` ("log tail unavailable: gunicorn still running;
  bounded marker, full log readable after bounded teardown") without
  touching the pipe at all — no unbounded `pipe.read` on a potentially
  alive process. Only after the process has exited (pipe at EOF) does it
  read and return the real last-8-lines tail, so stopped startup-failure
  logs (e.g. the `_require_ready` path, which stops first and then builds
  its message from the real tail) remain available. The module docstring
  records the new bounded-diagnostics safety property.
- The existing bounded teardown is unchanged: `stop()` still performs
  finite graceful SIGTERM → 10 s wait → forced SIGKILL → 10 s wait →
  `/proc` orphan audit, stays idempotent, and is retriable on
  mid-teardown failure (031-b behavior preserved).

**Criterion 2 — meaningful live-process failure regression. PASSED.**
- New
  `test_readiness_failure_diagnostics_bounded_while_server_alive`:
  launches the real owned Gunicorn (1 worker/2 threads, unique loopback
  port, dead `DATABASE_URL`/`TEST_DATABASE_URL`, anonymous endpoints only)
  and proves it actually becomes ready.
- Old-behavior sensitivity is demonstrated on the live process through
  bounded thread coordination: an owned daemon reader thread performs the
  old unbounded `stdout.read()`; after a bounded 0.5 s wait the test
  asserts the reader is still blocked (a pipe read without EOF cannot
  return, so this is a deterministic sensitivity proof, not a timing
  guess). The thread is joined after bounded teardown, so the test can
  neither hang nor leave a daemon behind; if the old read had
  unexpectedly returned, the test fails loudly with a sensitivity-check
  message.
- The real failure path is then exercised: the readiness result is forced
  to `False` by fixture injection only (`server.wait_ready =
  lambda: False`; the process, worker and port remain real), and the
  identical real expression
  `assert server.wait_ready(), f"server not ready; log tail:\n{server.log_tail()}"`
  is evaluated inside a `try/finally` whose `finally` runs
  `server.stop()` — the exact same message/assert/finally shape as the
  existing readiness-failure assertions. The fixed `log_tail` returns the
  bounded marker while the process is alive, so the assertion raises
  promptly and the finally teardown runs; the whole path is asserted
  bounded (< 15 s, dominated by the graceful stop) and the session audit
  proves 0 orphan children.
- Post-teardown diagnostics are re-checked: the old-read probe thread
  received EOF and terminates (joined within the bounded deadline), and
  `log_tail()` after the stop is prompt (< 500 ms) and returns the real
  stopped tail. An outer `finally` calls the idempotent `stop()` again,
  so the test itself cannot leak the server on its own failure.
- All seven pre-existing cases are retained unchanged in behavior and
  re-run: shipped-command baseline pin; gthread held-idle prompt serving;
  gthread partial-header prompt serving; old-sync starvation
  `silent-idle`; old-sync starvation `partial-header`;
  cleanup-on-failure with finally stop; injected-failure cleanup proof.
  The new case is a fixture-safety test and is explicitly not a
  substitute for the real six-socket old-sync negatives or the gthread
  positives. Actual count at the implementation bytes: **8 cases**
  (7 retained + 1 new), all executed.

**Criterion 3 — focused local suite + quality gates + exact-head CI +
normal report-only sequence. PASSED (to the point of authoring;
publication steps pending at authoring).**
- Focused Gunicorn suite locally at the implementation bytes (repo venv,
  real Gunicorn 23.0.0, real Django WSGI app):
  `uv run --env-file .env pytest tests/test_gunicorn_responsiveness.py
  --ds=slaif_reservation.config.settings.test -v` → 8 passed in 50.68 s;
  after the ruff-format pass the same file re-ran clean: `... -q
  --no-cov` → 8 passed in 50.03 s. All eight cases are the ones listed in
  criterion 2. Post-run host audit found no remaining gunicorn processes,
  and every in-test session audit reported 0 orphan children.
- `uv run ruff check .` → All checks passed!; `uv run ruff format
  --check .` → 186 files already formatted (the single ordered file was
  ruff-formatted as part of the change; formatting-only diff, no semantic
  change); `uv run mypy src` → Success: no issues found in 119 source
  files; `git diff --check` clean; `uv run --env-file .env python
  manage.py check` → 0 issues; `uv run --env-file .env python
  manage.py makemigrations --check --dry-run` → No changes detected.
- Standard five CI on the exact implementation head
  `8cf02be0dd897534f4a52a09c41bbac438a1d46c`: all SUCCESS before this
  report was written (section 5). The unchanged PostgreSQL/browser/
  concurrency suites ran through the full CI `test` job (619 passed, 0
  failed on real PostgreSQL 17 — 618 at the 031-b head plus the one new
  case — including all eight gunicorn regression tests). No local
  full-suite re-run was performed; no local full-suite success is claimed
  (the CI `test` job is the authoritative full result).
- Sequence executed: ordered reads → E-list/remote reconciliation →
  exact-source fault confirmation → the single ordered test-file
  correction + order/active bytes → focused local verification →
  implementation commit `8cf02be0dd897534f4a52a09c41bbac438a1d46c` → push
  (PR #62 amended to the same head, verified OPEN/MERGEABLE with
  `headRefOid` = the new head) → all five exact-head checks observed
  SUCCESS → literal full implementation head captured → this report.
- Pending at authoring (not yet successful, not claimed as done): this
  report committed as the only changed file with the implementation head
  as first parent (`Report publication commit: SELF`), push, remote
  verification (private execution receipt per CP-07), exact response OK,
  exit. No further mutation in this round after publication. Coding never
  merges.

## 3. Changed files and scope

Implementation commit `8cf02be0dd897534f4a52a09c41bbac438a1d46c` (first
and only non-report commit of the round; 3 files, +170/−1; first parent
`464d54d36ad6f55eb942e50c292bb196c82ed674`):
- `tests/test_gunicorn_responsiveness.py` — the only implementation file
  (+110/−0): bounded `GunicornServer.log_tail()` (finite marker while the
  process is alive; real tail only after the process has exited); new
  bounded constants (`OLD_READ_PROBE_S`, `LOG_TAIL_PROMPT_MS`,
  `READINESS_FAILURE_PATH_MS`, `LIVE_LOG_MARKER`); new
  `test_readiness_failure_diagnostics_bounded_while_server_alive`
  (live-process sensitivity probe via bounded daemon-thread coordination,
  forced readiness-failure through the real message/assert/finally shape,
  0-children and 0-thread proofs, post-stop bounded diagnostics); module
  docstring updated with the bounded-diagnostics property. Test count
  7 → 8.
- `oap/orders/031-c-bounded-diagnostics.md` — new,
  strategy-published order bytes as-is (+59).
- `oap/active` — pointer bytes `031-c` + LF as-is (was `031-b`).

This report commit changes only
`oap/reports/031-c-bounded-diagnostics.md` (new file), first parent
`8cf02be0dd897534f4a52a09c41bbac438a1d46c`. No CRITICAL register or other
file is touched; the 031-a/031-b reports were not rewritten; no merged PR
was mutated.

## 4. Commands and results (summary)

| Command (exact) | Result |
| --- | --- |
| `uv run --env-file .env pytest tests/test_gunicorn_responsiveness.py --ds=slaif_reservation.config.settings.test -v` (implementation bytes; real Gunicorn 23.0.0) | PASSED (8 passed in 50.68 s: baseline pin, held-idle, partial-header, old-sync silent-idle, old-sync partial-header, cleanup-on-failure finally stop, injected-failure cleanup orphans 0, NEW live-process bounded-diagnostics failure regression) |
| same file after ruff-format pass, `... -q --no-cov` | PASSED (8 passed in 50.03 s) |
| post-run host leak audit (`pgrep`) | PASSED (no gunicorn processes remained; per-test session audits 0 orphans) |
| `uv run ruff check .` | PASSED (All checks passed!) |
| `uv run ruff format --check .` | PASSED (186 files already formatted) |
| `uv run mypy src` | PASSED (no issues in 119 source files) |
| `git diff --check` | PASSED (clean) |
| `uv run --env-file .env python manage.py check` | PASSED (0 issues) |
| `uv run --env-file .env python manage.py makemigrations --check --dry-run` | PASSED (No changes detected) |
| local full standard suite | NOT RUN (not ordered; no local full-suite success claimed; CI `test` job is the authoritative full result: 619 passed, 0 failed at the exact head) |
| exact-head CI (5 checks) | PASSED (section 5) |

Environment: uv-managed CPython 3.13 (repo venv), pytest 9.1.1,
gunicorn 23.0.0, Django 5.2. The regression uses owned disposable
resources only: unique loopback ports, owned subprocesses in their own
sessions, owned sockets, a dead `DATABASE_URL`/`TEST_DATABASE_URL` at
`127.0.0.1:1` so no product database can be contacted; only status
codes, latencies, socket states and bounded log tails are observed (no
bodies, headers, cookies or CSRF values).

## 5. CI observed before authoring

Observed at authoring time, at implementation head
`8cf02be0dd897534f4a52a09c41bbac438a1d46c` (structured check/job data from
`gh pr checks` / `gh run list`; headSha equality verified for both runs):
- CI workflow run 37175041881 (`pull_request`, conclusion `success`):
  `quality` success (job 111355803008), `test` success (job
  111355802900; `619 passed in 161.49s (0:02:41)` on real PostgreSQL 17,
  including all eight `tests/test_gunicorn_responsiveness.py` tests; the
  FATAL password lines in that log are the expected dead-`DATABASE_URL`
  logs of the regression's owned subprocesses, not test failures),
  `security` success (job 111355803130), `container` success (job
  111355803099).
- oap workflow run 37175041840 (`pull_request`, conclusion `success`):
  `oap-harness` success (job 111355802755).

Report-head CI is **NOT YET OBSERVED AT AUTHORING**: this report's own
publication commit postdates the observed head, and no check result at the
report commit is claimed here. Post-publication verification observations
belong to the private execution receipt (CP-07), not to this report.

## 6. Security, data, dependencies and local tools

- No credentials, verifiers, peppers, cookies, CSRF, Authorization data,
  raw payloads, private exports or physical locators were read, written or
  logged; the regression captures statuses/latencies/socket states and
  bounded log tails only. No auth-home copying, no OS sidecars, no real
  exposure, no DNS/TLS/firewall change, no lab/Neumann/production
  contact, no real secrets or production data.
- No new dependency, no lock change, no application/domain/auth/policy/
  UI/migration/runtime-config/workflow byte changed; `SAR-022` preserved
  (stack unchanged); `SAR-024` preserved (loopback binds, no exposure
  change); `SAR-025` preserved (health views untouched); `SAR-031`
  preserved (owned disposable resources only, explicit bounded cleanup —
  now also finite on the live-process failure path); `SAR-032` evidence
  labels used only where true; `SAR-033` history preserved (same
  branch/PR, no renumbering, no merged-PR mutation, prior reports
  historical); `SAR-035` private-infrastructure boundary respected;
  `SAR-038` no release/deployment/ICA claim.
- `Decision: NONE` honored: no CRITICAL entry appended, no human
  disposition or gate clearance performed or implied.
- No operational CLAUDE.md/Claude launcher was used or created.

## 7. DHA outcome and unresolved gates

Order declaration: `## Deferred human adjudication` / `- Decision: NONE`.
No CRITICAL entry was appended, no human disposition or gate clearance was
performed or implied, and no D2 boundary was crossed. The only outstanding
gate is strategic review/development merge of PR #62, which belongs to
strategy. Real internet exposure remains a human D2 decision
(M-INTERNET-UX-PILOT development scope; real exposure is not authorized
by this round).

## 8. Limitations and recommendation

- The fix bounds diagnostics, not the server: a readiness failure with a
  live process now yields the bounded marker plus real log tail after
  teardown, but the reason for the readiness failure itself is still
  diagnosed from the post-teardown tail; this round does not add
  structured startup-failure classification.
- The 0.5 s sensitivity wait and the 500 ms / 15 s bounds are bounded
  heuristics for loopback scheduling; the sensitivity proof is
  deterministic in shape (a pipe read without EOF cannot return while the
  owned process group is alive), and the failure-mode if an environment
  ever made these flaky is a loud test failure, not a silent false pass.
- This is a fixture-safety test: it complements, not replaces, the real
  six-socket old-sync negative controls and the gthread positives, which
  remain the responsiveness/sensitivity evidence; responsiveness under
  held slow clients remains a baseline (24 bounded request slots), not a
  load guarantee (unchanged from 031-a/031-b).
- Report-head CI is unobserved at authoring; a failure there routes to a
  strategy suffix, not an amendment of this report.
- No claim is made for later requirements or new milestone readiness; this
  is a development merge candidate against M-INTERNET-UX-PILOT development
  scope.
