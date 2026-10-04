<!-- OAP-META
{
 "kind": "report",
 "id": "031-b",
 "order_path": "oap/orders/031-b-gunicorn-regression-review.md",
 "order_sha256": "7da724ebe569d0fcde9d514e2deaf6e0c0f5b7e64baa25f6155cdca11ca6f53a",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 61,
 "pr_number": 62,
 "branch": "codex/61-oap-031-a-gunicorn-idle-connections",
 "implementation_head": "fe29e5640fd35945f3a9a835377aecbf617eb6a6",
 "base_sha": "696b87965920817f1a6b36589562a4af68e75497",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "fe29e5640fd35945f3a9a835377aecbf617eb6a6",
  "runs": [
   {"run_id": 37174172334, "workflow": "CI", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 37174172333, "workflow": "oap", "event": "pull_request", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 031-b report — real-server regression review gaps closed (failure-path cleanup, partial-header settle, sync negative control)

Order digest: `7da724ebe569d0fcde9d514e2deaf6e0c0f5b7e64baa25f6155cdca11ca6f53a`
(committed `oap/orders/031-b-gunicorn-regression-review.md`, strategy-published
order bytes as found in the working tree; no rename/move). Active pointer
`oap/active` = `031-b` + LF (verified by xxd: `3033 312d 620a`, 6 bytes;
`sha256sum`: `c02083d0bb7fb65a294592d7cf907d3f51098f35c7a8e3c150665bc0ff8d262d`).

Implementation head SHA: fe29e5640fd35945f3a9a835377aecbf617eb6a6

Report publication commit: SELF

**Result: COMPLETE** — all four numbered acceptance criteria met. The round
changes exactly one file of the implementation,
`tests/test_gunicorn_responsiveness.py` (startup-failure cleanup and
slow-client sensitivity only), and publishes the round bytes (order + active
pointer). All 031-a configuration, docs, order and report bytes are
preserved. No application, domain, auth, policy, UI, dependency, migration,
runtime-config, workflow, or governance byte changed. This amends PR #62
(same issue 61, same branch); the previous 031-a report remains historical
and was not rewritten. Development merge candidate only; no deployment,
release, ICA or physical-resource consequence is claimed.

## 1. Starting state and E-list reconciliation (verify, do not assume)

Ordered reads completed: root router →
`oap/coding-instructions/AGENTS.md` → `ARCHITECTURE-for-agents.md` →
`OAP-COMMUNICATION-coding-agent.md` → exact active order (pointer
`oap/active` = `031-b` + LF →
`oap/orders/031-b-gunicorn-regression-review.md`, `state: FINAL`,
`pr_mode: AMEND`, `previous_round: 031-a`) → `SECURITY-CORE.md` /
`TESTING-CORE.md` → the order's scoped set: the single ordered
implementation file `tests/test_gunicorn_responsiveness.py` as committed at
the 031-a implementation head. No wildcard or strategic-history loading.
The wrapper had already consumed the control wake-up; it was not consumed
again.

Reconciliation before edit (remote/local, C-06; AMEND round b resumes the
same objective):
- Branch `codex/61-oap-031-a-gunicorn-idle-connections` local = remote =
  `820028778ea2ca5b21bfa1510804bbcd1054d78f` (after
  `git fetch origin --prune`), equal to the order's independently verified
  031-a report head. That commit's first parent is
  `49d176474f09f149d87d8366dae803eda3fd14be`, the 031-a implementation
  head named in the order's E-list.
- PR #62: `state: OPEN`, `headRefOid:
  820028778ea2ca5b21bfa1510804bbcd1054d78f`, head branch = the branch above,
  base `main` (`696b87965920817f1a6b36589562a4af68e75497` = order
  `base_sha` = local/remote `main`), `mergeable: MERGEABLE`,
  `autoMergeRequest: null`; PR body ends with `Closes #61`. One PR for the
  objective; no second PR created or amended.
- Order E-list report-head CI: independently re-observed — runs
  37172719201 (CI) and 37172719204 (oap) at head
  `820028778ea2ca5b21bfa1510804bbcd1054d78f`, both conclusion
  `success` (all five checks).
- Source hashes verified against the order via `sha256sum` in this
  checkout: `ARCHITECTURE.md`
  `8483a070026f382bb9b698e9346f3cb33f7dea44f8190b231431585986ebb17d`,
  `PLAN.md` `d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06`
  (both equal to the order's `source_hashes`).
- Working tree at start: tracked state clean at `8200287` except the
  ordered round bytes — `oap/active` modified (`031-a` → `031-b`) and
  untracked `oap/orders/031-b-gunicorn-regression-review.md`. No
  foreign/dirty files existed to preserve; no reset/clean/stash/force-push
  performed.
- The two exact-source review gaps named in the order were confirmed in
  the committed 031-a test bytes before editing:
  (a) `test_gthread_shutdown_cleans_children_on_failure` called
  `server.stop()` only in the try body — a `wait_ready` failure or an
  assertion failure before it left the finally without stopping the
  server, leaking the owned gunicorn session; (b)
  `test_gthread_serves_promptly_with_partial_header_clients` probed
  immediately after opening the six partial clients, with no settle and no
  held-state assertion before or after probing — a probe racing ahead of
  the blockers occupying the pool would falsely pass, and a held socket
  that had already been answered or closed was not detected. The old-sync
  negative control exercised only the silent-idle shape.

## 2. Acceptance evidence (ordered criteria)

**Criterion 1 — owned subprocess/socket cleanup guaranteed in every
server-using test; stop idempotent; deliberate failure-injection cleanup
proof. PASSED.**
- `GunicornServer.stop()` now tracks completed cleanup:
  `self._stopped` / `self._orphans` are set in `__init__`; a completed
  teardown is never re-executed (later calls return the recorded orphan
  count); `_stopped` is set only after the full bounded teardown
  (SIGTERM → 10 s wait → SIGKILL fallback → 10 s wait → `/proc` orphan
  audit) succeeded, so a mid-teardown failure leaves the stop retryable by
  an outer `finally` instead of silently reporting success. Bounded
  termination/kill/reap and unique loopback ports are unchanged.
- `test_gthread_shutdown_cleans_children_on_failure`: `server.stop()`
  moved into the `finally` block (idempotent, so the happy path still
  teardowns exactly once and its `orphans == 0` assertion is unchanged).
  A readiness failure or an assertion failure before the explicit stop now
  still terminates, force-kills and reaps the owned session.
- New `test_gthread_cleanup_survives_injected_failure`: the server is
  started (2 workers × 4 threads, unique loopback port, dead DB URL),
  readied, two partial-header clients are held and settled; then an
  `AssertionError("injected protected-region failure")` is deliberately
  raised inside the protected try region; the inner `finally` executes the
  bounded teardown and records the orphan count under
  `pytest.raises(AssertionError, match=...)`; the outer `finally` closes
  the held sockets and calls `server.stop()` again (idempotent no-op after
  the completed teardown, real teardown if the injection path itself had
  failed earlier — e.g. at readiness). The test then asserts
  `orphans == 0`: the session audit found no matching gunicorn children.
  This proves the failure path executes cleanup and proves no leak on the
  test's own failure, with no mock and no skipped teardown.
- The other two server-using tests already stopped in `finally`; all five
  server-using tests now have owned cleanup on every exit path.

**Criterion 2 — partial-header settle + held-state proof; real old-sync
partial negative control. PASSED.**
- `test_gthread_serves_promptly_with_partial_header_clients` now applies a
  bounded settle (`PARTIAL_SETTLE_S = 1.5`, one short settle) after
  opening the six partial-header clients so the pool threads actually
  accept and stall on the header reads; it asserts all six are
  `held-open` (non-blocking recv = EAGAIN, no buffered response bytes)
  BEFORE probing, then probes both real anonymous Django endpoints
  (`/health/live`, `/login/`) on fresh connections (must be 200 < 2 s),
  then asserts all six are still `held-open` AFTER probing. The genuine
  keep-alive test (`..._with_held_idle_clients`) and the shipped-command
  pinning test (`test_supported_commands_declare_gthread_baseline`) are
  retained unchanged; the gthread functional tests still run the exact
  parsed shipped flags, and no mock or sleep-only claim is used (the
  settle is bounded and the held-state assertions are real socket-state
  evidence).
- `test_old_sync_configuration_starves_new_connections` is now
  parameterized over both held-client shapes
  (`ids=["silent-idle", "partial-header"]`), exercising the real old sync
  3-worker configuration with six held clients per variant: warm
  `/health/live` + `/login/` (200 asserted) before holding, one bounded
  1.5 s settle, then bounded 1.5 s read-timeout probes (2 attempts × both
  endpoints) that must ALL time out while held (sensitivity proven, not
  asserted), all six held clients verified `held-open`, then close the
  blockers and assert prompt 200 recovery (< 2 s) on both endpoints. The
  new `partial-header` variant is the ordered real old-sync
  partial-header negative control; the existing `silent-idle` variant is
  preserved. No mocks; no workflow change; no pixel/UI/load expansion.

**Criterion 3 — focused local real-server regression + lint/format/type +
diff; exact-head CI all five SUCCESS before COMPLETE. PASSED.**
- Focused real-server regression locally at the implementation bytes:
  `uv run pytest tests/test_gunicorn_responsiveness.py -v --no-cov` →
  7 passed in 46.83 s (real Gunicorn 23.0.0, real Django WSGI app, unique
  loopback ports, dead `DATABASE_URL`/`TEST_DATABASE_URL`, anonymous
  `/health/live` + `/login/` only). All seven: shipped-command baseline
  pin; gthread held-idle prompt serving; gthread partial-header prompt
  serving with before/after held-open proofs; old-sync starvation
  `silent-idle`; old-sync starvation `partial-header`; cleanup-on-failure
  with finally stop; injected-failure cleanup proof (orphans 0).
  After the run: no gunicorn processes remained on the host (pgrep audit),
  and every in-test session audit reported 0 orphan children.
- `uv sync --locked --all-groups` rc 0 (71 packages, lock unchanged);
  `uv run ruff check .` → All checks passed!; `uv run ruff format
  --check .` → 186 files already formatted (the single ordered file was
  ruff-formatted as part of the change); `uv run mypy src` → Success: no
  issues found in 119 source files; `git diff --check` clean.
- Full exact implementation-head CI: all five checks SUCCESS at
  `fe29e5640fd35945f3a9a835377aecbf617eb6a6` before this report was
  written (section 5). The unchanged PostgreSQL/browser/concurrency suites
  ran through the full CI `test` job (618 passed, 0 failed on real
  PostgreSQL 17, including all seven regression tests). No local
  full-suite re-run was performed; no local full-suite success is claimed
  (the 031-a report documented known environmental local-full-suite
  failures in this setup); no unnecessary broad re-runs were made.

**Criterion 4 — normal immutable sequence, same PR `Closes #61`,
review gaps and correction proof recorded. PASSED (to the point of
authoring; publication steps pending at authoring).**
- Same objective, issue 61, one branch
  `codex/61-oap-031-a-gunicorn-idle-connections`, one PR #62
  (`Closes #61` retained); AMEND round b — no renumbering, no new PR, the
  previous 031-a report and order bytes are untouched and remain
  historical.
- Sequence executed: ordered reads → E-list/remote reconciliation →
  exact-source gap confirmation → the single ordered test-file
  correction → focused local verification (section 2, criterion 3) →
  implementation commit `fe29e5640fd35945f3a9a835377aecbf617eb6a6`
  (test file + ordered order/active bytes) → push (PR #62 amended to the
  same head, verified OPEN/MERGEABLE at the new `headRefOid`) → all five
  exact-head checks observed SUCCESS → literal full implementation head
  captured → this report.
- Pending at authoring (not yet successful, not claimed as done): this
  report committed as the only changed file with the implementation head
  as first parent (`Report publication commit: SELF`), push, remote
  verification (private execution receipt per CP-07), exact response OK,
  exit. No further mutation in this round after publication. Coding never
  merges.

## 3. Changed files and scope

Implementation commit `fe29e5640fd35945f3a9a835377aecbf617eb6a6` (first
and only non-report commit of the round; 3 files, +161/−17; first parent
`820028778ea2ca5b21bfa1510804bbcd1054d78f`):
- `tests/test_gunicorn_responsiveness.py` — the only implementation file
  (+91/−16): idempotent `GunicornServer.stop()` with completed-cleanup
  tracking; `test_gthread_shutdown_cleans_children_on_failure` stop in
  `finally`; new
  `test_gthread_cleanup_survives_injected_failure` (deliberate
  protected-region failure, finally teardown, zero-children proof);
  `test_gthread_serves_promptly_with_partial_header_clients` bounded
  settle + all-six `held-open` assertions before and after probing both
  endpoints; old-sync negative control parameterized over
  `silent-idle`/`partial-header`; module docstring updated to describe
  both negative-control shapes and the failure-path cleanup guarantee.
  Test count 5 → 7.
- `oap/orders/031-b-gunicorn-regression-review.md` — new,
  strategy-published order bytes as-is (+69).
- `oap/active` — pointer bytes `031-b` + LF as-is (was `031-a`).

This report commit changes only
`oap/reports/031-b-gunicorn-regression-review.md` (new file), first parent
`fe29e5640fd35945f3a9a835377aecbf617eb6a6`. No CRITICAL register or other
file is touched; the 031-a report was not rewritten; no merged PR was
mutated.

## 4. Commands and results (summary)

| Command (exact) | Result |
| --- | --- |
| `uv run pytest tests/test_gunicorn_responsiveness.py -v --no-cov` (implementation bytes; real Gunicorn 23.0.0) | PASSED (7 passed in 46.83 s: baseline pin, held-idle, partial-header with settle + before/after held-open ×6, old-sync silent-idle, old-sync partial-header, cleanup-on-failure finally stop, injected-failure cleanup orphans 0) |
| post-run host leak audit (`pgrep -af gunicorn`) | PASSED (no gunicorn processes; per-test session audits 0 orphans) |
| `uv sync --locked --all-groups` | PASSED (rc 0, 71 packages, lock unchanged) |
| `uv run ruff check .` | PASSED (All checks passed!) |
| `uv run ruff format --check .` | PASSED (186 files already formatted) |
| `uv run mypy src` | PASSED (no issues in 119 source files) |
| `git diff --check` | PASSED (clean) |
| local full standard suite | NOT RUN (not ordered; no local full-suite success claimed; CI `test` job is the authoritative full result: 618 passed, 0 failed at the exact head) |
| exact-head CI (5 checks) | PASSED (section 5) |

Environment: uv-managed CPython 3.13 (venv Python 3.13.15), pytest 9.1.1,
gunicorn 23.0.0. The regression uses owned disposable resources only:
unique loopback ports, owned subprocesses in their own sessions, owned
sockets, a dead `DATABASE_URL`/`TEST_DATABASE_URL` at `127.0.0.1:1` so no
product database can be contacted; only status codes, latencies and
socket states are observed (no bodies, headers, cookies or CSRF values).

## 5. CI observed before authoring

Observed at authoring time, at implementation head
`fe29e5640fd35945f3a9a835377aecbf617eb6a6` (structured check/job data, not
line-count predicates; `gh run view` headSha equality verified for both
runs):
- CI workflow run 37174172334 (`pull_request`, conclusion `success`):
  `quality` success (job 111353210444), `test` success (job
  111353210488; `618 passed in 151.53s (0:02:31)` on real PostgreSQL 17,
  including all seven `tests/test_gunicorn_responsiveness.py` tests),
  `security` success (job 111353210495), `container` success (job
  111353210486).
- oap workflow run 37174172333 (`pull_request`, conclusion `success`):
  `oap-harness` success (job 111353210429).

Report-head CI is **NOT YET OBSERVED AT AUTHORING**: this report's own
publication commit postdates the observed head, and no check result at the
report commit is claimed here. Post-publication verification observations
belong to the private execution receipt (CP-07), not to this report.

## 6. Security, data, dependencies and local tools

- No credentials, verifiers, peppers, cookies, CSRF, Authorization data,
  raw payloads, private exports or physical locators were read, written or
  logged; the regression captures statuses/latencies/socket states only.
  No auth-home copying, no OS sidecars, no real exposure, no
  DNS/TLS/firewall change, no lab/Neumann/production contact, no real
  secrets or production data.
- No new dependency, no lock change (`uv sync --locked` clean), no
  application/domain/auth/policy/UI/migration/runtime-config/workflow
  byte changed; `SAR-022` preserved (stack/lock unchanged); `SAR-024`
  preserved (loopback binds, private DB, no exposure change); `SAR-025`
  preserved (health views untouched); `SAR-031` preserved (owned
  disposable resources only, explicit bounded cleanup — now guaranteed on
  failure paths); `SAR-032` evidence labels used only where true;
  `SAR-033` history preserved (same branch/PR, no renumbering, no
  merged-PR mutation, prior report historical); `SAR-035`
  private-infrastructure boundary respected; `SAR-038` no
  release/deployment/ICA claim.
- `Decision: NONE` honored: no CRITICAL entry appended, no human
  disposition or gate clearance performed or implied.
- No operational CLAUDE.md/Claude launcher was used or created.

## 7. DHA outcome and unresolved gates

Order declaration: `## Deferred human adjudication` / `- Decision: NONE`.
No CRITICAL entry was appended, no human disposition or gate clearance was
performed or implied, and no D2 boundary was crossed. The only outstanding
gate is strategic review/development merge of PR #62, which belongs to
strategy. Real internet exposure remains a human D2 decision.

## 8. Limitations and recommendation

- The corrected tests strengthen, not expand, the regression's claims:
  responsiveness under six held slow clients (both shapes) remains a
  responsiveness baseline (24 bounded request slots), not a load
  guarantee; proxy buffering/read-timeout/rate controls remain a separate
  selected security objective, and direct-internet Gunicorn is not
  supported (unchanged from 031-a).
- The settle intervals (1.5 s, one per variant) are bounded heuristics for
  loopback scheduling; the held-state assertions (before and after
  probing) are the actual evidence that the blockers occupied the pool,
  and the old-sync parameterized variants are the sensitivity proof that a
  scheduling race in the positive test would be caught. If a future
  environment made the settles flaky, the failure modes are loud
  (asserted `held-open` states / probe timeouts), not silent false
  passes.
- Report-head CI is unobserved at authoring; a failure there routes to a
  strategy suffix, not an amendment of this report.
- No claim is made for later requirements or new milestone readiness; this
  is a development merge candidate against M-INTERNET-UX-PILOT development
  scope.
