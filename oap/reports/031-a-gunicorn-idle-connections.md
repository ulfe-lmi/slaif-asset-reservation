<!-- OAP-META
{
 "kind": "report",
 "id": "031-a",
 "order_path": "oap/orders/031-a-gunicorn-idle-connections.md",
 "order_sha256": "225e4a3e608436ac784c04cf4472c4868646b7915cfb4a59176ae5e1e268370a",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 61,
 "pr_number": 62,
 "branch": "codex/61-oap-031-a-gunicorn-idle-connections",
 "implementation_head": "49d176474f09f149d87d8366dae803eda3fd14be",
 "base_sha": "696b87965920817f1a6b36589562a4af68e75497",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "49d176474f09f149d87d8366dae803eda3fd14be",
  "runs": [
   {"run_id": 37172106393, "workflow": "CI", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 37172106401, "workflow": "oap", "event": "pull_request", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 031-a report — Gunicorn idle-connection starvation reproduced and fixed (gthread baseline)

Order digest: `225e4a3e608436ac784c04cf4472c4868646b7915cfb4a59176ae5e1e268370a`
(committed `oap/orders/031-a-gunicorn-idle-connections.md`, strategy-published
order bytes as found in the working tree; no rename/move). Active pointer
`oap/active` = `031-a` + LF (verified by xxd: `3033 312d 610a`, 6 bytes;
`sha256sum`: `a5c866c15ff53ff85ab4fe214de6eef278517ec2565a6f55827667263f1fe109`).

Implementation head SHA: 49d176474f09f149d87d8366dae803eda3fd14be

Report publication commit: SELF

**Result: COMPLETE** — all six numbered acceptance criteria met. The round
changes exactly the three supported Gunicorn command lines (sync pool to
gthread baseline: 3 workers, 8 threads, 5 s keep-alive, 30 s worker timeout;
binds and production log flags unchanged), adds one new real-server
regression test file, adds the ordered documentation paragraphs, and
publishes the round bytes (order + active pointer). No application, domain,
auth, policy, UI, migration, dependency, inventory, workflow, or canonical
governance byte changed. This is a development merge candidate only; no
deployment, release, ICA or physical-resource consequence is claimed.

## 1. Starting state and E-list reconciliation (verify, do not assume)

Ordered reads completed: root router → `oap/coding-instructions/AGENTS.md` →
`ARCHITECTURE-for-agents.md` → `OAP-COMMUNICATION-coding-agent.md` → exact
active order (pointer `oap/active` = `031-a` + LF →
`oap/orders/031-a-gunicorn-idle-connections.md`, `state: FINAL`) →
`SECURITY-CORE.md` / `TESTING-CORE.md` → the order's scoped set:
`Dockerfile`, `compose.yaml`, `compose.production.example.yaml`,
`tests/test_operational_hardening.py` (no Gunicorn command assertions
present), `INSTALL.md`, `TESTING.md`, `docs/deployment.md` Gunicorn/worker
references, `.github/workflows/ci.yml` + `oap.yml`, `src/slaif_reservation/config/{urls,views,wsgi}.py`,
`config/settings/{base,test,local}.py`, `web/views.py` `HumanLoginView`,
`pyproject.toml` (gunicorn>=23,<24 already a production dependency), and the
installed Gunicorn 23.0.0 worker sources
(`workers/sync.py`, `workers/gthread.py`, `http/message.py`,
`http/unreader.py`, `http/parser.py`, `config.py`) to verify behavior against
actual Gunicorn 23 before choosing or asserting anything. The wrapper had
already consumed the control wake-up; it was not consumed again.

Reconciliation before edit:
- Local `main` = `696b87965920817f1a6b36589562a4af68e75497` = order
  `base_sha`; `git fetch origin --prune` ⇒ `origin/main` at the same SHA.
- Source hashes verified against the order via `sha256sum` in this
  checkout: `ARCHITECTURE.md`
  `8483a070026f382bb9b698e9346f3cb33f7dea44f8190b231431585986ebb17d`,
  `PLAN.md` `d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06`
  (both equal to the order's `source_hashes`).
- `governance_revision` `14fc20b1ff52788974fd3f282322afc9d71362f9` resolves
  to a repository commit (the OAP conversion merge).
- `gh issue view 61`: open ("031: Reproduce and fix Gunicorn
  idle-connection starvation"), matches the order. `pr_number` null and no
  remote `codex/61*` or `031*` ref existed (`git ls-remote` inspected; newest
  PR was #60) → CREATE mode of CREATE_OR_RESUME; one new PR #62 was opened.
- Working tree at start: clean tracked state at base; only untracked round
  bytes `oap/active` and `oap/orders/031-a-gunicorn-idle-connections.md`.
  No reset/clean/stash/force-push performed; no unrelated local changes
  existed to preserve.
- Foreign-fix search limits (order provenance E, bounded local search, no
  probing/modification of any other host or deployment): local git branches,
  worktrees, stash, unpublished refs, ignored filenames, and dangling
  runtime-commit subjects were inspected — no foreign threaded Gunicorn fix
  found locally. A structural local Docker inspection found no current
  target product container. If a foreign change is discovered later, it is
  to be preserved and its identity reported; none was seen.
- Verified against actual Gunicorn 23.0.0 (installed, from source): the
  sync worker accepts into a blocking socket and blocks in the request
  parse read (`Request.__init__` → `Message.parse` →
  `SocketUnreader.chunk` = plain `recv`), so a silent or partial-header
  client pins that worker until disconnect or the arbiter's 30 s worker
  timeout; sync responses force `Connection: close`. The gthread worker
  accepts in a worker event loop (notifying the arbiter continuously),
  serves requests in a pool thread (a stalled header read occupies one
  pool thread until the client sends or disconnects), and parks idle
  keep-alive connections in the event loop with the configured keep-alive
  timeout. Defaults: `worker_connections` 1000 (so
  `max_keepalived = 1000 − 8 = 992` ≥ 1, no warning), `timeout` 30,
  `keepalive` 2. This analysis is the basis for both the reproduction and
  the accepted baseline; it is a source reading, not a substitute for the
  real-server evidence below.

## 2. Acceptance evidence (ordered criteria)

**Criterion 1 — independent reproduction BEFORE any tracked-config edit.
PASSED.** Disposable source copy at `/tmp/oap031a/repro` (tar copy of the
base tree, `.venv`/`.git` excluded; own `uv sync --locked --all-groups`,
gunicorn 23.0.0; synthetic test settings via
`DJANGO_SETTINGS_MODULE=slaif_reservation.config.settings.test`; dead
`DATABASE_URL`/`TEST_DATABASE_URL` at `127.0.0.1:1` so no product database
could be contacted — the anonymous `/health/live` and `/login/` GETs are
proven DB-free, verified with a dead-DB Django test-client probe before the
repro). Real installed Gunicorn, real Django WSGI app, unique loopback
port, old supported production config `--workers 3` (sync pool).
Measured, safe evidence only (statuses/latencies/socket states; no bodies,
headers, cookies, CSRF):
- Variant `silent-idle-6` (two independent runs): warm
  `/health/live` 200 @ 1.7 ms / 1.4 ms, `/login/` 200 @ 117.5 ms / 75.9 ms.
  6 simultaneous silent TCP clients held. Probes on fresh connections with
  1.5 s bounded read timeouts: all 4 attempts (both endpoints × 2) timed
  out — 1501.6/1502.6/1502.2/1501.8 ms and 1502.1/1501.6/1501.9/1502.2 ms
  across the two runs. All 6 held connections measured `held-open`
  (non-blocking recv = EAGAIN) during probing. After closing the 6
  blockers, recovery: `/health/live` 200 @ 2.8 ms / 1.8 ms, `/login/`
  200 @ 56.1 ms / 6.6 ms. Server exit 0, orphan children 0 (both runs).
- Variant `partial-header-3 + silent-3` (partial client = request line +
  one header, no blank-line terminator, then stalled): same result — warm
  200s (1.5 ms / 511.6 ms), all 4 bounded probes read-timeout @
  1501.5–1502.9 ms with all 6 connections `held-open`, recovery 200s @
  2.2 ms / 11.4 ms, exit 0, orphans 0.
- Mechanism (matches the Gunicorn 23 source reading): 3 workers each block
  in the request read on one held client; the remaining held clients and
  every new connection queue in the listen backlog, so new probes are
  starved for the whole hold period (≫ 1.5 s client timeouts); recovery is
  immediate once blockers disconnect. No mocked worker or toy application
  was used; no existing DB or service was needed or touched (foreign
  127.0.0.1:5432 never used).

**Criterion 2 — gthread in all three supported defaults, proposed baseline
verified against actual Gunicorn 23. PASSED (proposed = final).**
- `Dockerfile` `CMD`: `gunicorn slaif_reservation.config.wsgi:application
  --bind 0.0.0.0:8000 --workers 3 --threads 8 --keep-alive 5 --timeout 30`.
- `compose.yaml` app `command`: same flags (was `--workers 2` sync).
- `compose.production.example.yaml` app `command`: same flags plus the
  unchanged `--access-logfile - --error-logfile -` (was `--workers 3` sync).
- Rationale (documented in `docs/deployment.md` §5): 3 workers × 8 threads
  = 24 request slots; six slow clients can occupy one full worker's thread
  pool while the rest keep serving; existing 3-worker process isolation and
  bounded DB-connection demand retained; standard 30 s worker timeout
  preserved explicitly. Baseline accepted as proposed after the real-server
  verification below — no count raising or app-code change was needed.
- Scope documented: responsiveness baseline for the supported
  reverse-proxied shape; not a load guarantee and not direct-internet
  authorization. Binds exactly unchanged (container-internal
  `0.0.0.0:8000`; host publication remains loopback only in both Compose
  files — rendered config re-checked after the edit: app port
  `127.0.0.1:8000→8000`, user `10001:10001`). No new dependencies or
  infrastructure.

**Criterion 3 — durable real-server regression. PASSED (new
`tests/test_gunicorn_responsiveness.py`, 5 tests, ~30 s).**
- Launches the real installed Gunicorn (`sys.executable -m gunicorn`,
  23.0.0 in the venv) with the real Django routes (`/health/live`,
  `/login/`) on unique loopback ports; finite setup (30 s readiness
  deadline with bounded probes), request (2–3 s bounded reads), and cleanup
  (SIGTERM → 10 s → SIGKILL → reap, whole process session) limits; owned
  subprocess/socket cleanup in `finally` even after failures, with an
  orphan-child check.
- Reads and asserts the effective supported commands (parsed Dockerfile
  `CMD` JSON array; parsed Compose app commands via PyYAML): all three must
  declare bind `0.0.0.0:8000`, workers 3, threads 8, keep-alive 5, timeout
  30; production example must keep its log flags. Reverting any default to
  sync fails this test — verified in the disposable copy by reverting the
  Dockerfile there: `test_supported_commands_declare_gthread_baseline`
  failed (1 failed in 0.21 s). The gthread functional tests run the exact
  parsed shipped flags, not a monkeypatched config string.
- 6 held keep-alive idle clients (full request, complete response drained,
  connection kept) → both endpoints 200 < 2 s on fresh connections, and the
  held sockets verified still open (EAGAIN) during probes; 6 partial-header
  clients (stalled header block) → both endpoints 200 < 2 s.
- Old-sync negative control inside the suite: real `--workers 3` sync
  server, 6 held silent clients, 2 bounded 1.5 s probe attempts per
  endpoint must ALL time out (sensitivity proven, not merely asserted),
  held states verified, then prompt 200 recovery after the blockers close.
- Runs automatically in the existing CI `test` job via the standard
  `uv run pytest` (verified: CI log line
  `tests/test_gunicorn_responsiveness.py .....`); no workflow change;
  all 4 CI jobs plus `oap-harness` preserved.
- No precious `.env`/`deploy` paths: the child gets a dead DB URL and
  explicit env; no global signal or container cleanup; no DB required.

**Criterion 4 — local + exact-head verification. PASSED.**
- New regression locally: `uv run --env-file .env pytest
  --ds=slaif_reservation.config.settings.test
  tests/test_gunicorn_responsiveness.py -v --no-cov` → 5 passed in 30.21 s
  (real Gunicorn 23.0.0). Note: the first focused run (before the
  implementation commit) exposed a harness artifact in the new test itself —
  a kept client's single `recv` left response tail bytes buffered, so the
  held-connection check misread its own response; fixed by draining the
  complete response (headers + Content-Length body) before holding. All
  runs after the fix: 5/5 (also 5/5 inside the disposable full-suite run).
- Full standard suite in the disposable checkout
  (`/tmp/oap031a/repro`, fresh `uv sync`, owned isolated PostgreSQL 17
  container — same digest-pinned `postgres:17` image as the Compose files —
  on loopback-only `127.0.0.1:55432` with synthetic dev credentials and an
  anonymous volume): `uv run pytest` → 612 passed, 4 failed in 429.69 s
  (0:07:09). All 4 local failures are environmental to that disposable
  local setup, not code defects (same-head CI `test` job: 616 passed, 0
  failed): (a) `test_rehearsal_generated_env_remains_ignored` — the tar
  copy excludes `.git`, so the test's own `git check-ignore` exits 128
  "not a git repository" (captured in the log); (b)
  `tests/oap/test_ba38_39_tmux_config.py::test_ba39_strategic_same_prerequisites`
  — the executor context exports `OAP_ROLE=CODING`; the strategic launcher
  fixture correctly refuses a conflicting role (reproduced: `{"ok": false,
  "step": "role", "error": "conflicting OAP_ROLE=CODING; refusing"}`);
  `oap-harness` PASSED at the implementation head in CI (job 111346991515);
  (c) two `tests/browser/test_human_mvp_browser.py` chromium tests — empty
  page content after in-test navigation on this host only (the rest of the
  browser suite passed in the same local run; CI's `test` job with a fresh
  chromium install is green at this head).
- Lock/lint/format/mypy/diff at the implementation head:
  `uv sync --locked --all-groups` rc 0 (Resolved 71 packages, no lock
  change); `uv run ruff check .` → All checks passed!; `uv run ruff format
  --check .` → 186 files already formatted; `uv run mypy src` → Success: no
  issues found in 119 source files; `git diff --check` clean; `uv run
  --env-file .env python manage.py check` → 0 issues; `manage.py
  makemigrations --check --dry-run` → No changes detected (expected
  RuntimeWarning: local `.env` points at a non-running dev port
  54330 — no local dev DB was started, and the foreign 5432 was never
  used).
- Existing runtime/config tests: included in the disposable full-suite run
  (e.g., `tests/test_operational_hardening.py`, `tests/test_settings.py`,
  `tests/test_health.py` — all green there); no existing test asserted the
  old Gunicorn command, so no command-assertion update was necessary
  (none was made). No migration or application-domain edit.
- Build/production Compose checks (local, Docker 29.1.3):
  `docker compose config --quiet` OK; `docker compose -f
  compose.production.example.yaml config --quiet` OK; `deploy/rehearse_internal_alpha_deployment.sh
  --config-only` OK; rendered production app healthcheck still carries
  `X-Forwarded-Proto: https` (CI guard condition); rendered app port
  `127.0.0.1:8000→8000` and user `10001:10001` unchanged; `docker build`
  rc 0; image `Config.User` = `10001:10001`; image `Config.Cmd` = the new
  gthread baseline; all 5 static/bootstrap files present in the image.
- Full current-head standard CI: observed at the exact implementation head
  (section 5), including the full product/browser/restore suites on real
  PostgreSQL 17 — thread-concurrency preservation rests on those real
  race/rollback/browser/restore results, not mock DB claims.

**Criterion 5 — documentation. PASSED.**
- `docs/deployment.md` §5: new "Gunicorn worker pool" subsection —
  worker/thread/keepalive/timeout rationale, the measured failure mode,
  troubleshooting note, the new regression invocation, and the retained
  mandatory boundary (loopback-only publication, exclusive HTTPS reverse
  proxy with buffering/read-timeout duties, direct-internet Gunicorn not
  supported). The existing unsupported-public warning and all other content
  are untouched.
- `INSTALL.md`: exactly one Gunicorn concurrency paragraph (section 1),
  cross-referencing `docs/deployment.md` §5. README untouched.
- `TESTING.md`: Gunicorn regression command and required-evidence note
  only (section T-02).
- No old objective/ICA chronology in operator prose.

**Criterion 6 — one issue/branch/PR; exact sequence; CI before COMPLETE.
DONE (to the point of authoring; publication steps pending at authoring).**
- Same issue 61, one branch `codex/61-oap-031-a-gunicorn-idle-connections`,
  one PR #62 (`Closes #61`), CREATE mode; no other PR mutated.
- All 5 implementation-head checks observed SUCCESS before this report was
  written (section 5); no pending/skipped/cancelled/missing check counted
  as pass.
- Sequence executed: ordered reads → reproduction (negative control first,
  no tracked config touched) → implementation (3 command lines) + durable
  test + docs + round bytes → implementation commit
  `49d176474f09f149d87d8366dae803eda3fd14be` → push → PR #62 created
  BEFORE this report → CI observed at the exact head → literal full
  implementation head captured → this report.
- Pending at authoring (not yet successful, not claimed as done): this
  report committed as the only changed file with the implementation head as
  first parent (`Report publication commit: SELF`), push, remote
  verification (private execution receipt per CP-07), exact response OK,
  exit. No further mutation in this round after publication. Coding never
  merges.

## 3. Changed files and scope

Implementation commit `49d176474f09f149d87d8366dae803eda3fd14be` (first and
only non-report commit of the round; 9 files, +598/−2):
- `Dockerfile` — Gunicorn default `CMD` line only (sync `--workers 2` →
  gthread baseline, 1 line).
- `compose.yaml` — app Gunicorn `command` only (sync `--workers 2` → gthread
  baseline).
- `compose.production.example.yaml` — app Gunicorn `command` only (sync
  `--workers 3` → gthread baseline; log flags preserved).
- `tests/test_gunicorn_responsiveness.py` — new durable real-server
  regression (5 tests).
- `docs/deployment.md` — +57 (Gunicorn worker pool subsection).
- `INSTALL.md` — +14 (one Gunicorn concurrency paragraph).
- `TESTING.md` — +15 (regression command/evidence).
- `oap/orders/031-a-gunicorn-idle-connections.md` — new, strategy-published
  order bytes as-is.
- `oap/active` — new, pointer bytes `031-a` + LF as-is.

This report commit changes only
`oap/reports/031-a-gunicorn-idle-connections.md` (new file), first parent
`49d176474f09f149d87d8366dae803eda3fd14be`. No CRITICAL register or other
file is touched; no prior report was rewritten; no merged PR was mutated;
the foreign-fix search found nothing to preserve.

## 4. Commands and results (summary)

| Command (exact) | Result |
| --- | --- |
| repro driver (disposable copy, old sync `--workers 3`, 6 silent idle held) | PASSED-as-expected (all 4 bounded probes read-timeout @ ~1501.6–1502.6 ms; held-open ×6; recovery 200 @ 2.8/56.1 ms and 1.8/6.6 ms across two runs) |
| repro driver (disposable copy, 3 partial-header + 3 silent held) | PASSED-as-expected (all 4 bounded probes read-timeout @ ~1501.5–1502.9 ms; held-open ×6; recovery 200 @ 2.2/11.4 ms) |
| `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test tests/test_gunicorn_responsiveness.py -v --no-cov` (implementation head) | PASSED (5 passed in 30.21 s, real Gunicorn 23.0.0) |
| disposable-copy sensitivity check (Dockerfile reverted to sync there) | PASSED-as-expected (baseline pin test fails: 1 failed in 0.21 s) |
| full standard suite, disposable checkout + owned isolated PG17 container | 612 passed, 4 failed in 429.69 s — all 4 diagnosed environmental (section 2, criterion 4); same-head CI: 616 passed |
| `uv sync --locked --all-groups` | PASSED (rc 0, 71 packages, lock unchanged) |
| `uv run ruff check .` / `uv run ruff format --check .` | PASSED (All checks passed! / 186 files already formatted) |
| `uv run mypy src` | PASSED (no issues in 119 source files) |
| `uv run --env-file .env python manage.py check` | PASSED (0 issues) |
| `uv run --env-file .env python manage.py makemigrations --check --dry-run` | PASSED (No changes detected) |
| `git diff --check` | PASSED (clean) |
| `docker compose config --quiet` / production variant | PASSED |
| `deploy/rehearse_internal_alpha_deployment.sh --config-only` | PASSED (config-only=ok) |
| rendered production compose (healthcheck guard, ports, user) | PASSED (X-Forwarded-Proto: https retained; 127.0.0.1:8000→8000; 10001:10001) |
| `docker build` + image user/Cmd/static checks (Docker 29.1.3) | PASSED (rc 0; User 10001:10001; Cmd = gthread baseline; 5/5 files present) |
| exact-head CI (5 checks) | PASSED (section 5) |

Environment: uv-managed CPython 3.13 (venv Python 3.13.15), gunicorn
23.0.0, Docker 29.1.3, Playwright 1.60.0 (chromium rev 1223, locally
cached), host Postgres 16 cluster on 127.0.0.1:5432 present but never used
(owned isolated PG17 container used for the local full suite).

## 5. CI observed before authoring

Observed at authoring time, at implementation head
`49d176474f09f149d87d8366dae803eda3fd14be` (structured check/job data, not
line-count predicates):
- CI workflow run 37172106393 (`pull_request`, conclusion `success`):
  `quality` success (job 111346991681), `test` success (job 111346991793;
  `616 passed in 153.08s (0:02:33)` on real PostgreSQL 17, including
  `tests/test_gunicorn_responsiveness.py` — all 5 new tests), `security`
  success (job 111346991799), `container` success (job 111346991795).
- oap workflow run 37172106401 (`pull_request`, conclusion `success`):
  `oap-harness` success (job 111346991515).

Report-head CI is **NOT YET OBSERVED AT AUTHORING**: this report's own
publication commit postdates the observed head, and no check result at the
report commit is claimed here. Post-publication verification observations
belong to the private execution receipt (CP-07), not to this report.

## 6. Security, data, dependencies and local tools

- No credentials, verifiers, peppers, cookies, CSRF, Authorization data,
  raw payloads, private exports or physical locators were read, written or
  logged; repro and tests capture statuses/latencies/socket states only
  (the `/login/` response headers, which would carry CSRF cookies, were
  never recorded). `gh` used its normal host authentication only.
- No production/lab/Neumann/SmartScheduling contact, no real deployment, no
  DNS/TLS/firewall/public-exposure action, no private host mounts. Public
  exposure remains forbidden and untouched.
- Owned disposable runtime resources (all cleaned or owned):
  `/tmp/oap031a/` (source copy, driver, logs, rendered compose JSON),
  `slaif031a-pg` postgres:17 container + its anonymous volume (removed via
  `docker rm -fv` with that explicit identity after the local suite), and
  the locally built image `slaif-asset-reservation:ci-031a`. No destructive
  cleanup on unknown volumes or real env/secrets; the foreign
  127.0.0.1:5432 PG16 cluster was never connected to.
- One execution slip, honestly recorded: a `docker rm slaif031a-pg` issued
  prematurely (while the local suite was still running) silently failed
  because the container was still running — the suite therefore completed
  against its intended database; the container was removed afterwards by
  explicit identity with its volume.
- No new dependencies (gunicorn was already a locked production
  dependency; `uv.lock` unchanged); no workflow change; no migration.
- `SAR-022` preserved (stack/lock unchanged); `SAR-024` preserved
  (loopback binds, private DB, no exposure change); `SAR-025` preserved
  (health views untouched); `SAR-031` preserved (owned disposable
  resources only, explicit cleanup); `SAR-032` evidence labels used only
  where true; `SAR-033` history preserved (new branch/PR, no
  renumbering, no merged-PR mutation); `SAR-035` private-infrastructure
  boundary respected; `SAR-038` no release/deployment/ICA claim.

## 7. DHA outcome and unresolved gates

Order declaration: `## Deferred human adjudication` / `- Decision: NONE`.
No CRITICAL entry was appended, no human disposition or gate clearance was
performed or implied, and no D2 boundary was crossed. The only outstanding
gate is strategic review/development merge of PR #62, which belongs to
strategy. Internet abuse controls, default policy, landing/admin/UI/help/
theming and a fresh ICA are the selected next work per the order — not
waived, not started, not claimed complete here.

## 8. Limitations and recommendation

- The gthread baseline is a responsiveness baseline (24 bounded request
  slots; verified under 6 held idle and 6 partial-header clients), not a
  load guarantee. Threading does not defeat an arbitrary slow-client flood:
  a stalled header read still occupies one pool thread until the client
  sends or disconnects, and beyond ~24 concurrent slow clients new
  requests can queue again. Proxy buffering/read-timeout/rate controls
  remain a separate selected security objective; direct-internet Gunicorn
  is not supported.
- The reproduction and regression exercise the anonymous
  `/health/live` + `/login/` GET boundary only, as ordered; DB-backed
  routes are not exercised by this test (and do not need to be for the
  worker-occupancy property).
- The 4 local full-suite failures were diagnosed as environmental (section
  2, criterion 4); the same-head CI `test` job is the authoritative full
  result (616 passed, 0 failed).
- Report-head CI is unobserved at authoring; a failure there routes to a
  strategy suffix, not an amendment of this report.
- No claim is made for later requirements or new milestone readiness; this
  is a development merge candidate against M-INTERNET-UX-PILOT development
  scope, with real exposure remaining a human D2 decision.
