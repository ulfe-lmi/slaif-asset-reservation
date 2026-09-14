<!-- OAP-META
{
 "kind": "report",
 "id": "023-a",
 "order_path": "oap/orders/023-a-fifo-write-flake-fix.md",
 "order_sha256": "d44de19a7ea1b33412766c34f2a537127a4c05d1c743c01a175bde4e66926c7d",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 45,
 "pr_number": 46,
 "branch": "codex/45-oap-023-a-fifo-write-flake-fix",
 "implementation_head": "39bd20c48519bb70a0044c27554661c3d29fce0c",
 "base_sha": "f06aa94b74113dd5ef2268fcc6bc54ccaf0d2d73",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "39bd20c48519bb70a0044c27554661c3d29fce0c",
  "runs": [
   {"run_id": 34815054394, "workflow": "CI", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}}},
   {"run_id": 34815054553, "workflow": "oap", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 023-a report — fifo_write EPIPE retry (test-side FIFO writer fix)

Order digest: d44de19a7ea1b33412766c34f2a537127a4c05d1c743c01a175bde4e66926c7d
(committed `oap/orders/023-a-fifo-write-flake-fix.md`; the materialized
`.FINAL` source was renamed to the canonical name, as in every prior
round — `sha256sum` of both names: d44de19a7ea1b33412766c34f2a537127a4c05d1c743c01a175bde4e66926c7d).

Implementation head SHA: 39bd20c48519bb70a0044c27554661c3d29fce0c

Report publication commit: SELF

**Result: COMPLETE** — `fifo_write` in `tests/oap/oaptestlib.py` now
delivers the full payload with a bounded retry on EPIPE (both the normal
and the `fragment=True` branches), with a backward-compatible `deadline`
keyword (default 30.0s) that raises a FIFO-naming `TimeoutError` on
expiry; two new deterministic regression tests in
`tests/oap/test_fifo_write_retry.py` prove retry-to-delivery under a
simulated receive-window close and bounded failure when no reader ever
returns. No `oap/bin`, `src/`, docs, workflow or dependency bytes were
touched; no existing assertion was weakened; the canary test is
byte-identical.

## Reconciliation at start (C-05/C-06/CP-03)

- Ordered reads: root router → `oap/coding-instructions/AGENTS.md` →
  `ARCHITECTURE-for-agents.md` → `OAP-COMMUNICATION-coding-agent.md` →
  exact active order → `SECURITY-CORE.md`/`TESTING-CORE.md` → ordered
  subtree excerpts only: `tests/oap/oaptestlib.py` (in full),
  `tests/oap/test_roundtrip_canary.py` (in full),
  `oap/bin/oap_launch.py` (coding wait loop and `_handle`, read-only),
  `oap/bin/oaplib.py` (`fifo_send`, `fifo_receive`, lease helpers,
  read-only), `tests/oap/test_ba24_25_fifo.py`,
  `tests/oap/test_ba26_27_40_41_wrapper.py`,
  `tests/oap/test_ba10_11_roles.py`, `tests/oap/test_ba51_52_continuity.py`
  (call-site audit), `.github/workflows/ci.yml`,
  `.github/workflows/oap.yml`, `pyproject.toml` (ruff/mypy/pytest config),
  `src/slaif_reservation/config/settings/test.py` (test DB URL source),
  `oap/reports/022-a-legacy-import-concurrency.md` (report precedent).
- `oap/active` = exactly `023-a` + LF (6 bytes). Wrapper had already
  consumed the control OK; not consumed again.
- Local main = remote `origin/main` =
  f06aa94b74113dd5ef2268fcc6bc54ccaf0d2d73 (= the order's `base_sha`;
  022-a quiescent on top of merged PR #44). Worktree clean except the
  materialized order (untracked `oap/orders/023-a-fifo-write-flake-
  fix.FINAL.md`) and the pointer (untracked `oap/active`). Fresh round:
  no local/remote branch and no PR for issue #45 (verified with
  `git ls-remote origin` and `gh pr list` before creation);
  `pr_mode=CREATE_OR_RESUME` resolved to CREATE. PR #46 (GitHub-assigned
  number, recorded truthfully; issue #45 is the objective issue) on the
  order's exact branch `codex/45-oap-023-a-fifo-write-flake-fix`, base
  `main`.
- Order hash check: committed order file sha256
  d44de19a7ea1b33412766c34f2a537127a4c05d1c743c01a175bde4e66926c7d
  matches the `.FINAL` source (rename preserves bytes; both hashes
  above). DHA declaration: `- Decision: NONE` (no APPEND, no CRITICAL
  change this round).

## Pre-change state (acceptance criterion 1)

Verified by direct source reading at base f06aa94
(identical to the implementation head for `oap/bin` and `src/`, which
are untouched this round), plus the actual CI log.

**The exact CI failure frame (run 34811801450, attempt 1, job `test`).**
From the job log (job id 103874473700, `1 failed, 608 passed in
124.48s`):

```
tests/oap/test_roundtrip_canary.py F                                     [ 81%]
...
    self.assertTrue(_wait(lambda: True, timeout=1.5))  # wrapper settles
    t.fifo_write(control)
>   t.fifo_write(control)  # duplicate wake-ups
    ^^^^^^^^^^^^^^^^^^^^^

tests/oap/test_roundtrip_canary.py:268:
fifo_path = PosixPath('/tmp/canary-4570-39dfb031jnvconwc/home/control.fifo')
data = b'OK', fragment = False

    def fifo_write(fifo_path: Path, data: bytes = b"OK", fragment: bool = False) -> None:
        fd = os.open(str(fifo_path), os.O_WRONLY)
        try:
            if fragment and data:
                os.write(fd, data[:1])
                time.sleep(0.05)
                os.write(fd, data[1:])
            else:
                while data:
>                   n = os.write(fd, data)
                        ^^^^^^^^^^^^^^^^^
E                   BrokenPipeError: [Errno 32] Broken pipe

tests/oap/oaptestlib.py:485: BrokenPipeError
FAILED tests/oap/test_roundtrip_canary.py::RoundTripCanary::test_roundtrip_
canary - BrokenPipeError: [Errno 32] Broken pipe
```

Test line: `test_roundtrip_canary.py:268` — the duplicate wake-up write
in section (g). Frame: `os.write` at `oaptestlib.py:485` inside
`fifo_write`. Third CI occurrence of the same signature (prior: 017-a,
018-a oap runs, attempt 1, both passed on re-run at the same heads).

**The wrapper's 0.5s poll / timeout-continue loop** (`oap_launch.py`
coding wait loop, lines 202–235):

```python
while not stop["flag"]:
    res = oaplib.fifo_receive(
        home / "control.fifo", timeout=0.5, lease_owner=consumer_owner
    )
    ...
    if not res["ok"] and res["code"] == 3:
        if args.once:
            break
        continue
```

`fifo_receive` (oaplib.py:922) opens ONE `O_RDONLY | O_NONBLOCK` fd,
select-polls until the deadline accumulating until EOF, and on expiry
returns `{"ok": False, "code": 3, "error": "timeout before EOF", ...}`
and closes the fd. The wrapper then re-polls immediately in the next
cycle. So a writer whose `os.open(O_WRONLY)` unblocked during a receive
cycle but whose `os.write` only executes after that cycle's 0.5s window
expired (possible under CI runner load — the writer thread is stalled
between the two syscalls) finds the read end gone: the write raises
EPIPE (BrokenPipeError in Python). The pre-fix `fifo_write`
(oaptestlib.py:476–488) had no EPIPE handling: blocking open, then a
write loop, done — the exception escaped into the test.

**The state-based duplicate suppression** (`oap_launch.py` `_handle`,
lines 130–166): a wake-up launches a context only if the durable state
does not already show the same objective invoked without a new round —
journal `invoked` events for the pointer id + a report file
`<oid>-*.md` under `oap/reports/` + no `new_round` journal event after
the last invocation ⇒ `"skip"`. The `control_consumed` journal entry is
written only AFTER a successful receive (the loop `continue`s on code 3
before any journaling). Therefore: (i) a receive-window timeout
consumes nothing and journals nothing; (ii) a wake-up re-delivered in a
LATER cycle is still suppressed when the objective is already
invoked/reported; (iii) EPIPE on a FIFO write implies that session's
data was never consumed as a wake-up (the pipe is torn down when the
last reader closes; the wrapper rejects any incomplete frame as
timeout/invalid-framing), so a full-payload re-delivery cannot
duplicate a wake-up or a `control_consumed` journal event.

**The old `fifo_write` structure** (oaptestlib.py:476–488): blocking
`os.open(O_WRONLY)` (returns only when a reader exists), then
`os.write` loop (or the `fragment=True` branch: `data[:1]`,
`time.sleep(0.05)`, `data[1:]` — same exposure: the second write can
EPIPE during the sleep), `os.close` in `finally`. No EPIPE handling, no
deadline, single attempt.

**Call-site audit — every `fifo_write` usage in tests/oap/** (21 calls,
4 files; re-delivery-safety argument per context):

1. `tests/oap/test_ba24_25_fifo.py:32` `test_ba24_exact_ok` (b"OK" via
   the `_one` helper: one-shot `fifo_receive` consumer, 8s window) —
   framing test. Redelivery safety: single writer, single message; a
   retry only follows a fully torn-down session that consumed no valid
   frame, so the consumer sees at most the one full message; the
   assertion (ok + data) is unchanged.
2. `:37` `test_ba24_fragmented_write` (b"OK", `fragment=True`) — same
   argument; the fix keeps both fragments inside the retried cycle, so
   an EPIPE mid-fragment re-sends both fresh (the consumer would
   otherwise see a one-byte frame and fail with code 4).
3. `:42` `test_ba24_empty_bytes` (b"") — open, no write, close;
   consumer gets 0-byte EOF → code 4, unchanged.
4. `:47` `test_ba24_one_byte` (b"O") — invalid framing code 4,
   unchanged; a retry would resend the same single byte.
5. `:52` `test_ba24_extra_bytes` (b"OKX") — "more than two" code 4,
   unchanged.
6. `:57` `test_ba24_invalid_bytes` (b"XX") — "invalid framing" code 4,
   unchanged.
7. `:111` `test_ba25_mode_must_be_0600` — single b"OK" to a live
   consumer after chmod 0600; single delivery, assertion unchanged.
8. `:125` `test_ba25_multiple_consumers_rejected` — b"OK" consumed by
   the lease owner ("first"); single delivery.
9. `:132` same test, second consumer ("third") after lease release —
   single delivery.
10. `:179` `test_ba25_no_dummy_writer_masks_eof` — b"OKOK" single
    message → "more than two"; single delivery.
11. `:187` same test, sequential message b"OK" → ok; single delivery.
12. `tests/oap/test_roundtrip_canary.py:152` (section (c), single
    wake-up, ACTIVE_PENDING wrapper) — single OK. Redelivery safety:
    an EPIPE means the polling session timed out (code 3, nothing
    journaled, wrapper re-polls); the re-delivered OK is processed
    exactly once, so "exactly one invocation", the
    `control_consumed`-before-`invoked` journal order, and the
    role/cwd/CODEX_HOME assertions are preserved (and the write can
    now no longer die on EPIPE, which previously could drop the sole
    wake-up under load).
13. `test_roundtrip_canary.py:267–268` (section (g), duplicate
    wake-ups, REPORT_PUBLISHED wrapper; 268 is the flaked line) — two
    sequential single OKs. Redelivery safety: suppression is state-
    based (journal `invoked` for 001-a + report present + no
    `new_round`), so a re-delivery in a LATER wait cycle is still
    suppressed; "exactly one total invocation" and "pointer still
    001-a" are preserved — the retry strengthens the contract rather
    than duplicating wake-ups.
14. `tests/oap/test_ba26_27_40_41_wrapper.py:74` `test_ba26_zero_model_
    calls_while_idle` — one wake-up of an idle wrapper; same single-
    delivery argument as (12); "exactly one invocation" preserved.
15. `:105` `test_ba26_consumption_journalized` — one wake-up; a retry
    can only follow a code-3 session that journaled nothing, so
    `control_consumed` still precedes `invoked` exactly once.
16. `:134` `test_ba27_extra_wakeups_do_not_reimplement` (first wake-up
    before the objective is reported) — single delivery; the
    invocation happens exactly once.
17. `:153` same test, the 3× spam loop (objective already reported +
    journaled) — each spam write is a sequential single delivery; any
    EPIPE re-delivery lands in a later cycle and is suppressed by
    state; "must not re-invoke" preserved.
18. `tests/oap/test_ba10_11_roles.py:122` (role: wrapper launched from
    home cwd; one wake-up) — single delivery; exactly-one-invocation
    and the cwd/CODEX_HOME assertions preserved; a lost sole wake-up
    (pre-fix EPIPE) could previously zero the invocation count — the
    retry removes that failure mode.
19. `:195` mirror role test (tiny prompt) — same argument.

(Fifth call-site file: the definition itself at
`tests/oap/oaptestlib.py:476`.)

## The fix (acceptance criterion 2, scope item 1)

`tests/oap/oaptestlib.py::fifo_write` — new signature
`fifo_write(fifo_path, data=b"OK", fragment=False, deadline: float =
30.0)`:

- the open->write->close cycle is wrapped in a bounded retry loop on
  `BrokenPipeError`/`ConnectionResetError` (EPIPE): on the error the fd
  is closed, a 0.05s pause, re-open, and the FULL payload is rewritten
  (never a partial); both the normal branch and the `fragment=True`
  branch are inside the retried cycle (a fragment write that EPIPEs
  mid-fragment re-sends both fragments fresh);
- the open is a bounded `O_WRONLY | O_NONBLOCK` poll on ENXIO (a FIFO
  open without a reader) instead of an unbounded blocking open, so the
  deadline bounds the whole operation — this also mirrors how the
  wrapper's `fifo_receive` opens (non-blocking);
- on deadline expiry a `TimeoutError` naming the FIFO is raised (a
  genuine failure: "no reader for FIFO ... within ..." for the
  open-poll path, "... lost its reader before delivery within ..." for
  the post-EPIPE path, when the deadline is reached at the retry point);
- docstring states the contract: delivers `data` to a reader that
  (re)opens the FIFO; EPIPE means the session was not consumed and the
  write is retried until delivered or the deadline.

Why re-delivery is safe (the wrapper-side argument verified above): a
code-3 receive session consumes and journals nothing; the wrapper
re-polls immediately; duplicate wake-ups are suppressed state-based;
and EPIPE implies the session's bytes were never consumed as a
wake-up, so a full-payload resend cannot duplicate anything.

No `oap/bin` change; no wrapper contract change; no other test file
touched; no assertion weakened (the canary's "exactly one invocation",
"duplicate wake-ups must not launch a second context", pointer/byte and
state-trace assertions are exactly as written).

## New deterministic regression tests (acceptance criterion 2, scope
item 2)

`tests/oap/test_fifo_write_retry.py` (NEW; stdlib unittest, real
temporary POSIX FIFOs, no Django/PG; total added runtime ~2s):

1. `test_retry_delivers_after_receive_window_close` — the reader thread
   mirrors the wrapper's real receive side: (a) opens the read end
   `O_RDONLY | O_NONBLOCK` (unblocking the writer's pending open),
   (b) sleeps 100ms without reading (the wrapper's bounded
   receive-window expiry, scaled to ms), (c) closes, (d) reopens and
   reads to EOF. `fifo_write(fifo, b"OK", deadline=5.0)` must complete
   without exception and the reader must receive exactly `b"OK"` with a
   clean EOF.
2. `test_bounded_failure_when_reader_never_returns` — the reader opens,
   sleeps 100ms, closes and NEVER reopens. `fifo_write(fifo, b"OK",
   deadline=1.5)` must raise `TimeoutError` after the bounded deadline
   (no infinite retry), with a message naming the FIFO, and the first
   write attempt must have actually executed (stall-consumed check),
   proving the EPIPE-retry path — not a bare no-reader timeout — ran
   and was then bounded.

**Determinism mechanism (recorded deviation, see below).** To make the
retry path exercise deterministic rather than load-dependent, each test
wraps the write in a one-shot `OneShotWriteStall`: the process's first
`os.write` call sleeps 150ms before delegating to the real syscall —
exactly the condition the order's evidence frame names ("the wrapper's
0.5s receive window expires after the writer's open has unblocked ...
but before the writer's write executes — possible under CI runner
load"). Only the timing is injected; the EPIPE itself is a genuine
kernel EPIPE on real FIFO descriptors, and the retry logic under test
is the unpatched `fifo_write`. The stall is restored on exit even on
failure, and the reader's `O_RDONLY | O_NONBLOCK` opens match
`fifo_receive`'s real open flags.

**Negative control (the test detects the pre-fix behavior).** Against
the base `fifo_write` (scratch detached worktree at f06aa94, same test
file): with the new signature shimmed in, both tests fail with the
exact CI signature — `BrokenPipeError: [Errno 32] Broken pipe` (test 1:
the writer dies instead of surviving; test 2: the exception escapes
instead of a bounded `TimeoutError`); without the shim, both fail with
`TypeError: fifo_write() got an unexpected keyword argument 'deadline'`.
Against the implementation head: 8/8 consecutive full-file runs OK.

**Recorded deviation from the order's literal test script (D0
mechanics, evidence recorded for strategy review).** The order's
literal reader script — (a) open, (b) sleep ~100ms, (c) close, (d)
immediately reopen and read — cannot deterministically trigger the
retry on EITHER the old or the new code: (i) a plain immediate write
lands inside the 100ms window (the write executes µs after the open
unblocks), so no EPIPE occurs; (ii) if it did land after the close, the
writer's still-open fd keeps the pipe alive, so an immediately-following
reopen re-joins the SAME pipe and reads the buffered bytes — again no
EPIPE; and (iii) a blocking `O_RDONLY` reopen would hang waiting for a
writer that never comes (empirically verified at base: the literal
script hangs; verified structurally from the FIFO/pipe lifetime
semantics). Any deterministic realization of the order's intent
therefore needs (x) a stall between the writer's open unblock and its
write — the order's own named CI mechanism — and (y) a bounded gap
before the (d) reopen (200ms here; lower-bound arithmetic guarantees it
starts after the stalled attempt has EPIPE'd and closed its descriptor,
so the reopen is a fresh session). All other order parameters are kept:
~100ms window, short deadlines (5.0s / 1.5s), exact-payload
assertion, writer-survival assertion, and the total-runtime bound
(~2s << 10s). The alternative — BLOCKED without implementing — was
rejected because the order's intent (prove the retry contract
deterministically) is achievable in-scope and is proven above.

## Gates (acceptance criterion 3)

Local, at implementation head 39bd20c48519bb70a0044c27554661c3d29fce0c
(disposable owned `postgres:17` container `slaif-023a-testdb`,
loopback-only 127.0.0.1:54330, matching `.env`
`TEST_DATABASE_URL`; migrations, bootstrap import (47 assets, 1
excluded SAR-004 entry) and `purge_expired_idempotency_records` applied
to the disposable DB before the operational gates; working tree
identical to the committed tree at that head):

- Focused: `env -u OAP_ROLE uv run python -m unittest discover -s
  tests/oap -p 'test_fifo_write_retry.py'` → **2 passed** (~1.9s),
  PASSED, repeated 8 consecutive times (8/8 OK).
- Focused canary loop: `env -u OAP_ROLE uv run python -m unittest
  discover -s tests/oap -p 'test_roundtrip_canary.py'` → **10
  consecutive focused runs, 10/10 OK**. Recorded truthfully: the
  flake is CI-load-dependent (the writer stall between open and write
  under runner load), so absence of a natural local repro is expected
  and does not fail this criterion — the deterministic negative control
  above reproduces the pre-fix failure on demand instead.
- oap harness full: `env -u OAP_ROLE uv run python -m unittest
  discover -s tests/oap -p 'test_*.py'` → **154 passed** (0 failed, 0
  skipped) in ~34s = 152 baseline + 2 new, PASSED. (First local run
  failed one pre-existing test, `test_ba52_real_reports_orders_history_
  untouched`, because the order had been COPIED instead of renamed from
  its `.FINAL` source, leaving two `023-a-*.md` files for the ACTIVE
  pointer; corrected by the rename (the established prior-round flow —
  "sha256sum of both files before the rename") and the full harness
  then passed; recorded here for the evidence trail.)
- Full: `env -u OAP_ROLE uv run --env-file .env pytest
  --ds=slaif_reservation.config.settings.test` → **611 passed** (0
  failed, 0 skipped) in 183.88s = 609 baseline at the 022-a head + 2
  new retry tests, PASSED. (See Local-environment notes for `OAP_ROLE`.)
- `uv sync --locked --all-groups` PASSED (68 packages checked).
- `uv run ruff check .` PASSED; `uv run ruff format --check .` PASSED
  (185 files).
- `uv run mypy src` PASSED (119 source files, strict).
- `uv run --env-file .env python manage.py check` PASSED (0 issues).
- `uv run --env-file .env python manage.py makemigrations --check
  --dry-run` PASSED (no changes).
- `uv run --env-file .env python manage.py operational_check` PASSED
  (database/migrations/static/bootstrap/idempotency_cleanup_command/
  operational all ok).
- `uv run --env-file .env python manage.py spectacular --validate
  --fail-on-warn` PASSED (rc=0).
- `uv run pip-audit` PASSED (no known vulnerabilities). Note: the first
  attempts hit a transient pypi.org network block from this host
  (ReadTimeout); the retry after recovery passed — recorded
  truthfully.
- `git diff --check` PASSED.

Pre-existing-file byte-identity (proven by diff):
`git diff f06aa94b74113dd5ef2268fcc6bc54ccaf0d2d73
39bd20c48519bb70a0044c27554661c3d29fce0c --name-status` shows exactly
`M tests/oap/oaptestlib.py`; the full implementation commit shows
exactly 4 files — `tests/oap/oaptestlib.py` (65 +/-),
`tests/oap/test_fifo_write_retry.py` (+160 new),
`oap/active` (+1) and
`oap/orders/023-a-fifo-write-flake-fix.md` (+199) — 414 insertions, 11
deletions. `tests/oap/test_roundtrip_canary.py` diff vs base: 0 bytes
(byte-identical). No `src/`, no docs, no dependency, no governance
change.

## CI at the exact implementation head (acceptance criterion 4)

At the exact implementation head 39bd20c48519bb70a0044c27554661c3d29fce0c
(observed after the push of the implementation commit, before this report
was written; PR #46, branch
`codex/45-oap-023-a-fifo-write-flake-fix`):

- CI run 34815054394 (workflow `CI`, pull_request): quality
  **success** (20s), test **success** (3m23s), security **success**
  (17s), container **success** (27s).
- oap run 34815054553 (workflow `oap`, pull_request): oap-harness
  **success** (38s).
- `gh pr checks 46` (observed): all five checks `pass` — container,
  oap-harness, quality, security, test.
- CI test job log (job 103883892944) at that head shows the canary test
  and the new retry tests running and counted in the pass total:
  `tests/oap/test_fifo_write_retry.py .. [ 77%]`,
  `tests/oap/test_roundtrip_canary.py . [ 81%]`, summary line
  `611 passed in 128.04s (0:02:08)` (609 baseline + 2 new).
- PR identity (observed via the repository API): PR #46 open (not
  draft), head `codex/45-oap-023-a-fifo-write-flake-fix` @
  39bd20c48519bb70a0044c27554661c3d29fce0c, base `main` @
  f06aa94b74113dd5ef2268fcc6bc54ccaf0d2d73, mergeable clean.
- Report-head CI: NOT YET OBSERVED AT AUTHORING (the report commit lands
  after this report's content was frozen).

## Strategy-requested re-run at base f06aa94 (acceptance criterion 5)

Observed, not assumed. The failed job's re-run at the same head was
requested by strategy (~2026-09-14 06:10 UTC) while this fix lands.
Observed outcome: run 34811801450's `test` job (job id 103874473700)
FAILED on attempt 1 (the frame above) and PASSED on the re-run — the
run's conclusion is now **success** with all four jobs (quality/test/
security/container) success at the same head
f06aa94b74113dd5ef2268fcc6bc54ccaf0d2d73 (verified via `gh run view
34811801450` and the attempt-1 jobs API). A re-run pass at the same
head confirms the flake character (same bytes, different scheduling).

## Diff scope (acceptance criterion 6)

The diff touches only allowed_paths:
`tests/oap/oaptestlib.py`, `tests/oap/test_fifo_write_retry.py`,
`oap/orders/023-a-fifo-write-flake-fix.md`, `oap/active`
(implementation) plus this report file (report-only commit). The
optional `tests/oap/test_roundtrip_canary.py` deadline touch was NOT
needed (the 30.0s default keeps every existing call site
backward-compatible); it is byte-identical.

## Local-environment notes (evidence-index caveats)

- The coding launcher exports `OAP_ROLE=CODING` in the process
  environment; the path-gated OAP harness test
  `tests/oap/test_ba38_39_tmux_config.py` rejects a strategic launch
  when a conflicting `OAP_ROLE` leaks into its subprocess. Local runs
  therefore used `env -u OAP_ROLE`; CI runs in a clean environment and
  the oap-harness CI job at the implementation head is the authoritative
  harness gate. This is an environment artifact of this launcher, not a
  product or test defect; no OAP harness file other than the allowed
  ones was touched.
- Local evidence used a disposable PostgreSQL 17 container owned by
  this round (loopback only); the container is torn down at round end.
  Authoritative CI evidence is at the exact implementation head.
- Network egress from this host was intermittently degraded during the
  round (pypi.org ReadTimeouts, then transient api.github.com
  connection resets); all gates were re-run until green and CI is
  recorded from the observed runs only.

## Acceptance criteria verdict

1. **MET** — pre-change state recorded above: the exact EPIPE frame and
   test line from CI run 34811801450 (job 103874473700, attempt 1), the
   wrapper's 0.5s poll/timeout-continue loop, the state-based duplicate
   suppression (and why it makes late re-delivery safe), the old
   fifo_write open-then-write structure, and the call-site audit of all
   21 `fifo_write` usages in tests/oap/ with the re-delivery-safety
   argument per context (single wake-up vs duplicate wake-up).
2. **MET** — the `fifo_write` retry is implemented per scope item 1
   (both branches, full-payload resend, parameterized deadline, raise on
   deadline); the new deterministic tests pass and prove (a)
   retry-to-delivery under a simulated receive-window close and (b)
   bounded failure when no reader ever returns; the negative control
   proves they fail against the pre-fix behavior with the exact CI
   signature.
3. **MET** — local evidence at the implementation head: canary 10/10
   consecutive focused runs green (loop and counts recorded; absence of
   a natural local repro recorded truthfully), full pytest 611 passed,
   oap harness 154 passed, ruff check, ruff format --check, mypy,
   makemigrations --check --dry-run, manage.py check, operational_check,
   spectacular --validate --fail-on-warn and pip-audit all green; all
   pre-existing files outside allowed_paths byte-identical (diff
   evidence above).
4. **MET** — CI at the exact implementation head 39bd20c: quality/test/
   security/container (run 34815054394) and oap-harness (run
   34815054553) all success; all five `gh pr checks 46` pass; the CI
   test job log shows the canary test and the two new retry tests
   running and counted in `611 passed in 128.04s`.
5. **MET** — the strategy-requested re-run outcome at f06aa94 recorded
   truthfully: re-run PASS (run 34811801450 all-success at the same
   head), confirming the flake character.
6. **MET** — the diff touches only allowed_paths (implementation commit:
   exactly the four ordered files; report commit: exactly this report).

## Privacy / dependencies / DHA / limits

- No credentials, tokens, peppers, verifiers, passwords, cookies, CSRF
  values, raw request payloads, private exports, physical locators, auth
  homes or sidecar traces appear in the diff, this report, or any log
  artifact; fixtures are synthetic (temp FIFOs, fake client, fixture
  git remotes).
- No new or removed dependencies; `uv.lock` untouched.
- DHA: `Decision: NONE` — no CRITICAL entry created, appended or
  dispositioned by this round.
- Limits: the deterministic tests inject one timing (the write stall)
  to force the runner-load interleaving; everything else — FIFO
  descriptors, EPIPE, retry logic, EOF framing — is the real
  implementation. The literal order test script's deviations are
  recorded with evidence above (D0 mechanics, for strategy review).
  Report-head CI is not observed at authoring and is not claimed. This
  report is evidence, not strategic acceptance; merge remains
  strategy's delegated act after review.
