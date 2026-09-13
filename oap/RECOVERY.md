# RECOVERY — protocol, not improvisation

Generated from OAP-PROTOCOL OP-14 for this installation (generation 1). Recovery
always inspects durable state (remote first, then repository, then private journal)
before acting. Private metadata supports recovery but never overrides repository/OAP
truth.

## State table

| Observation | State | Next permitted action |
|---|---|---|
| No `oap/active` pointer | INACTIVE | Wait externally; no model invocation, no invented work |
| Empty/malformed pointer, or ID matches no unique order | CORRUPT | Preserve bytes; stop affected operation; report |
| Order durable, pointer old/missing, identical unfinished journal | PUBLISHING | Complete the identical transition only (`publish_order.py --recover`) |
| Control consumed, process died, no report | RUNNING_INTERRUPTED | Resume same ID/branch/PR at the unfinished scope |
| First round `a` already has a PR | RESUME | Bind the verified existing PR; never create a second |
| Local report commit, remote unverified | REPORT_LOCAL | Verify/push the unchanged commit; no new implementation |
| Remote report, response lost | REPORT_PUBLISHED | Strategic review; no implementation rerun |
| Duplicate wake-up | (reconcile) | Inspect durable state; suppress if running/published/accepted |
| CI pending | REVIEW_PENDING | Wait/recheck outside the model; no make-work suffix |
| Accepted/merged PR but pointer remains | ACCEPTED/QUIESCENT | Not an executable active task; pointer reconciled by strategy |
| Replacement client/context/host | (restore) | Restore logical role/state; no new objective or suffix |
| Human quits | STOPPED | No resurrection until explicit restart |

## Publication recovery details

`publish_order.py --recover` may complete only the identical unresolved publication
whose journal digest matches the durable order bytes and whose pointer is absent or
still naming a different (older) objective. Mismatching bytes, a newer accepted state
or an already-completed historical order are conflicts: preserve and report. The
completed historical order can never be reactivated.

## Report recovery details

A local-only report is finished by pushing/verifying the unchanged commit (same full
object ID). A report-only commit that triggers CI failure is not amended by coding;
strategy publishes the next suffix on the same PR. A lost response after verified
remote publication routes to strategic review, never to implementation replay.

## Process and session rules

- Wrapper leases (owner/PID/start-time) prevent duplicate consumers; a stale lease is
  reconciled with evidence, never blindly deleted.
- Explicit quit (SIGINT/TERM/stop marker) exits owned wrappers and sessions only.
- Cleanup touches only owned resource IDs/paths (test-owned repos, FIFOs, tmux sockets
  on owned `-L` sockets, owned lock files). Never a foreign tmux session, container,
  database, volume or lock.
- Quiescent accepted-governance refresh: back up known installed copies (private
  backup dirs), preserve all private drafts/config/auth/logs/history, refuse unknown
  divergent copies as conflicts.
- Preserve reports and incorrect-interpretation history: append or supersede notes;
  never erase.
