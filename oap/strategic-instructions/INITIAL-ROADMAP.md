# Initial roadmap — Concentrated OAP (inactive drafts)

Generation 1, 2026-09-13. All entries below are **inactive**: they exist as expanded
drafts under `initial-orders/` (this home: `drafts/`). Nothing here is an active order.
WO0014 (supervised conversion adoption) is reserved and outside the operational ID
sequence; its issue/branch/PR are created only by separately authorized human action.

## Sequence and dependencies

```text
WO0014 (human-merged conversion adoption, reserved)
  -> attributable activation for M-CONVERSION
  -> 015-a  round-trip canary (M-CONVERSION)
  -> ICA at exact merged revision -> human M-CONVERSION acceptance
  -> target selection (M-LOCAL-PILOT-EVIDENCE, human)
       016-a pilot-readiness failure boundaries   (independent after 015)
       017-a rehearsal ownership/cleanup          (independent after 015)
       019-a booking/maintenance/import concurrency (independent after 015)
       018-a isolated backup/restore proof        (after 017 or equivalent)
       020-a pilot path through actual adapters   (after 016-019 accepted/reassessed)
  -> fresh full-matrix ICA -> human judgment
M-EXTERNAL-PILOT / M-RELEASE: D2, human host/identity/exposure/data/ops decisions.
```

## Drafts (expanded, inactive)

| ID | Title | Milestone | Prerequisites | Draft path |
|---|---|---|---|---|
| 015-a | Concentrated OAP round-trip canary on the existing repository | M-CONVERSION | Human-merged WO0014; qualified roles/runtime/remote and attributable activation | `initial-orders/015-a-concentrated-oap-round-trip-canary.md` |
| 016-a | Qualify and contain pilot-readiness failure boundaries | M-LOCAL-PILOT-EVIDENCE | 015 accepted; human-selected target; not authorized during bootstrap | `initial-orders/016-a-pilot-readiness-failure-boundaries.md` |
| 017-a | Qualify rehearsal ownership and failure-safe cleanup | M-LOCAL-PILOT-EVIDENCE | 015 accepted; target selected | `initial-orders/017-a-rehearsal-ownership-cleanup.md` |
| 018-a | Prove isolated PostgreSQL backup and restore end to end | M-LOCAL-PILOT-EVIDENCE | 017 accepted (or equivalent ownership qualification); target selected | `initial-orders/018-a-isolated-backup-restore.md` |
| 019-a | Qualify booking versus maintenance and import concurrency | M-LOCAL-PILOT-EVIDENCE | 015 accepted; target selected | `initial-orders/019-a-booking-maintenance-concurrency.md` |
| 020-a | Record human-agent-management pilot path through actual adapters | M-LOCAL-PILOT-EVIDENCE | 016-019 accepted or explicitly reassessed with evidence; target selected | `initial-orders/020-a-pilot-path-actual-adapters.md` |

## Rules

- One objective = one issue = one `codex/<issue>-oap-<id>-<slug>` branch/PR; round `a`
  creates the PR only if none exists; corrections amend the same PR.
- Draft metadata (base SHA, governance revision, issue/PR numbers, timings, results)
  stays unresolved until strategy inspects current state; fabrication is a protocol
  violation.
- Draft retirement is explicit, with dependency/requirement reassessment; every SAR
  requirement remains implemented, explicitly deferred, or visibly unproven.
- No arbitrary task quota; do not invent work to keep a loop busy.
