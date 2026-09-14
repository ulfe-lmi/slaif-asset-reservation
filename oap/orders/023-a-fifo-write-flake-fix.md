<!-- OAP-META
{
 "id": "023-a",
 "round": "a",
 "base_sha": "f06aa94b74113dd5ef2268fcc6bc54ccaf0d2d73",
 "issue_number": 45,
 "branch": "codex/45-oap-023-a-fifo-write-flake-fix",
 "pr_mode": "CREATE_OR_RESUME",
 "previous_round": null,
 "allowed_paths": [
  "tests/oap/oaptestlib.py",
  "tests/oap/test_fifo_write_retry.py",
  "tests/oap/test_roundtrip_canary.py (only if a deadline parameter is required at a call site; prefer not touching)",
  "oap/orders/023-a-fifo-write-flake-fix.md",
  "oap/active",
  "oap/reports/023-a-fifo-write-flake-fix.md"
 ],
 "forbidden_resources": [
  "any change under oap/bin/ (the wrapper and oaplib FIFO contract are sound and stay untouched; this fix is test-helper-side only)",
  "any change under src/ (no product changes)",
  "any change to tests other than the allowed tests/oap/ paths (all other test files byte-identical)",
  "any weakening, skipping, or loosening of an existing assertion to make a test pass",
  "any change under docs/, deploy/, data/, .github/, or other oap/ files (no workflow or helper-contract changes)",
  "new dependencies or removed dependencies",
  "deployment of any kind; real/production databases; real lab/Neumann machines",
  "credentials, auth files, sessions, tokens, auth homes",
  "DNS/TLS/firewall changes, public exposure, repository visibility or branch-protection changes",
  "any mutating GitHub operation except pushing this branch and opening this objective's PR",
  "merging or auto-merging any PR (merge is strategy's delegated act after review)",
  "ICA activity, milestone completion claims, canary re-design, or work from other drafts/objectives",
  "model provider endpoints other than the configured qwen-neumann role profile"
 ]
}
-->

# 023-a — Fix the test_roundtrip_canary BrokenPipeError flake in the
# test-side FIFO writer

## Goal

The required CI test job failed at main f06aa94 (run 34811801450,
test_roundtrip_canary) on the known pre-existing BrokenPipeError flake —
its third CI occurrence after 017-a and 018-a (both passed on re-run at
the same heads). This is a defect in the OAP test harness's FIFO writer,
not the product or the wrapper: `fifo_write` in tests/oap/oaptestlib.py
performs a blocking `os.open(O_WRONLY)` and then `os.write`; the coding
wrapper polls `oaplib.fifo_receive(timeout=0.5)`, so if the wrapper's
0.5s receive window expires after the writer's open has unblocked (the
wrapper was the reader) but before the writer's write executes — possible
under CI runner load — the wrapper closes the read fd and the write
raises BrokenPipeError (EPIPE) at oaptestlib.py:485. The fix makes
`fifo_write` delivery robust with a bounded retry; it adds a
deterministic regression test for the retry path; it changes nothing in
oap/bin, src/, or any product byte.

## Durable provenance and requirements

- H: in-session human principal instruction 2026-09-14 — continue the
  autonomous loop; "keep cheap, reliable mechanisms"; a required CI gate
  that flakes is a concrete operational failure warranting repair (not
  OAP expansion).
- E: main = f06aa94b74113dd5ef2268fcc6bc54ccaf0d2d73 (022-a quiescent;
  the quiesce commit changed only oap/active). CI run 34811801450 at that
  head: quality/container/security success, test FAILED at
  tests/oap/test_roundtrip_canary.py::RoundTripCanary::test_roundtrip_
  canary — BrokenPipeError, frame tests/oap/oaptestlib.py:485
  (os.write inside fifo_write), test line
  test_roundtrip_canary.py:268 (the duplicate wake-up write in section
  (g)). Prior same-signature occurrences: 017-a and 018-a oap runs
  (attempt 1, passed on re-run). Source-verified at base (verify, do not
  assume): oap_launch.py coding loop calls
  `oaplib.fifo_receive(home/"control.fifo", timeout=0.5, lease_owner=...)`;
  on `code == 3` (timeout) it `continue`s (re-polls); on a successful
  receive it classifies durable state and `_handle` suppresses duplicate
  wake-ups ("same objective already invoked without a new round" ->
  "skip": report exists for the order id and no new_round journal event
  after the last invocation). `fifo_write` (oaptestlib.py:476-488) opens
  O_WRONLY (blocking until a reader exists) then loops os.write; no EPIPE
  handling. `fifo_receive` (oaplib.py:922) accumulates until EOF (writer
  close) under the lease.
- A: S-06 (routine failing test = bounded engineering repair, not a
  CRITICAL entry), S-12 (proof-sized objective), S-19 (name the exact
  failing boundary; fake FIFO tests prove harness contracts only — this
  round proves exactly that contract, and nothing product), S-15 (report
  boundary), S-16/S-17 (exact-head review; delegated merge).
- C: SAR-034 (Codex-only role separation preserved: no wrapper contract
  change), SAR-037 (canonical governance preserved: oap/bin untouched).

## Current reconciled state and prerequisites

- Base main (local and remote): f06aa94b74113dd5ef2268fcc6bc54ccaf0d2d73.
  Worktree clean on main; `oap/active` absent (INACTIVE).
- The failed job's re-run was requested at the same head by strategy
  (2026-09-14 ~06:10 UTC) to restore green main while this fix lands;
  record the re-run's observed outcome truthfully in the report (either
  outcome is acceptable; a re-run pass confirms the flake character, a
  re-run failure strengthens it).
- Fresh round: no local/remote branch codex/45-oap-023-a-fifo-write-flake-
  fix, no PR for issue #45 (verify with git ls-remote and gh before
  creation); pr_mode CREATE_OR_RESUME resolves to CREATE. PR number is
  GitHub-assigned; record it truthfully.
- Known facts (verify, do not assume): the duplicate wake-up section (g)
  of test_roundtrip_canary starts wrapper2 in REPORT_PUBLISHED state,
  writes two consecutive OKs, and asserts exactly one total invocation
  in the fake log and pointer still 001-a; the wrapper's suppression is
  state-based (journal + report glob), so a duplicate OK delivered in a
  LATER wait cycle is still suppressed — retry-until-delivered therefore
  preserves (and strengthens) the test's contract; EPIPE on a FIFO write
  implies the session's data was never consumed (the pipe is torn down
  when the last reader closes), so a re-delivery cannot duplicate a
  wake-up; the `fragment=True` branch (two os.write calls with a 0.05s
  sleep) has the same exposure and must be covered by the retry.

## Ordered read set

Standard compact read set, plus: tests/oap/oaptestlib.py (fifo_write,
fifo_consumer_thread, and the FIFO fixture helpers in full),
tests/oap/test_roundtrip_canary.py (in full — especially section (g) and
every fifo_write call site), oap/bin/oap_launch.py (coding wait loop and
_handle duplicate suppression — read-only), oap/bin/oaplib.py
(fifo_receive, fifo_send, lease helpers — read-only), and the other
tests/oap/ files that call fifo_write (call-site audit).

## Scope and allowed paths

1. tests/oap/oaptestlib.py — harden `fifo_write`: wrap the
   open->write->close cycle in a bounded retry loop on
   BrokenPipeError/ConnectionResetError (EPIPE). On retry: close the fd,
   sleep ~0.05-0.1s, re-open and rewrite the FULL payload (never a
   partial). Deadline parameter (default 30.0s; keyword, backward
   compatible); on deadline expiry raise (genuine failure, with a
   message naming the FIFO). Both the normal and the `fragment=True`
   branches must be inside the retried cycle (a fragment write that EPIPEs
   mid-fragment must re-send both fragments fresh, not resume).
   Update the docstring to state the contract: "delivers `data` to a
   reader that (re)opens the FIFO; EPIPE means the session was not
   consumed and the write is retried until delivered or the deadline".
2. tests/oap/test_fifo_write_retry.py — NEW deterministic regression test
   (unittest style, matching the other tests/oap/ harness tests; no
   Django/PG required): create a temp FIFO; a reader thread that (a)
   opens the read end (unblocking the writer's open), (b) sleeps ~100ms
   WITHOUT reading (simulating the wrapper's receive-timeout close), (c)
   closes, (d) reopens and reads to EOF; run `fifo_write` with a short
   deadline (e.g. 5s); assert the reader eventually received the exact
   payload and that the writer survived (no exception). A second test:
   reader that opens, closes, and NEVER reopens -> `fifo_write` with a
   short deadline (e.g. 1.5s) must raise after the deadline (no
   infinite retry). Keep total added runtime under ~10s.
3. tests/oap/test_roundtrip_canary.py — touch ONLY if a call site needs
   the deadline keyword for suite speed; otherwise byte-identical.

Non-negotiable: no oap/bin change; no wrapper contract change; no
weakening of any existing assertion (the canary's "exactly one
invocation", "duplicate wake-ups must not launch a second context",
pointer/byte, and state-trace assertions stay exactly as written).

## Non-goals

- No product change; no docs change; no workflow (.github/) change.
- No redesign of the wrapper's 0.5s polling, the lease protocol, or
  fifo_receive semantics (they are sound and are what makes late
  re-delivery safe).
- No canary re-design, no new canary rounds, no ICA, no milestone claim.
- No deployment, no lab/Neumann contact.
- No merge, auto-merge, approval or settings change.

## Numbered acceptance criteria

1. The report records the pre-change state: the exact EPIPE frame and
   test line from CI run 34811801450, the wrapper's 0.5s poll/
   timeout-continue loop, the state-based duplicate suppression, the
   fifo_write open-then-write structure, and the call-site audit of every
   fifo_write usage in tests/oap/ (with the re-delivery-safety argument
   for each context: single wake-up vs duplicate wake-up).
2. The `fifo_write` retry is implemented per Scope item 1 (both
   branches; full-payload resend; parameterized deadline; raise on
   deadline); the new deterministic tests (Scope item 2) pass and prove
   (a) retry-to-delivery under a simulated receive-timeout reader and
   (b) bounded failure when no reader ever returns.
3. Local evidence at the implementation head: the full canary test green
   in 10 consecutive focused runs (record the loop and the outcome
   counts; the flake is CI-load-dependent, so absence of a natural local
   repro is expected and must be recorded truthfully — it does not fail
   this criterion, which is about the fix passing, not about
   reproducing); full pytest suite green; ruff check, ruff format
   --check, mypy, makemigrations --check --dry-run, manage.py check,
   operational_check, spectacular --validate --fail-on-warn, pip-audit
   all green; all pre-existing files outside allowed_paths
   byte-identical (prove by diff).
4. CI at the exact implementation head: quality/test/security/container
   and oap-harness all success; the CI test job shows the canary test and
   the new retry tests running (counted in the pass total).
5. The report truthfully records the strategy-requested re-run outcome
   at f06aa94 (observed, not assumed).
6. The diff touches only allowed_paths.

## Deferred human adjudication

- Decision: NONE
