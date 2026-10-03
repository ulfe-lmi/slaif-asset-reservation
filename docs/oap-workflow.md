# OAP Workflow — Concentrated OAP conversion profile

**Status:** adopted and operational. The one-time human-merged conversion
adoption (WO0014) put this profile into force, and objectives from 015-a
onward have executed on `main` under it; this document describes the live
workflow.

## Roles and authority

- **Human:** product meaning, domain truth, risk appetite, DHA adjudication, milestone
  judgment, release/deployment. The conversion adoption PR (WO0014) is human-merged.
- **STRATEGIC (Codex, separate private home):** full installed constitution at
  `STRATEGIC_HOME/AGENTS.md`; versioned source `oap/strategic-instructions/AGENTS.md`.
  Owns orders, provisional decisions, review and conditional development merge.
- **CODING (Codex, fresh per round, this repository):** dense law at
  `oap/coding-instructions/AGENTS.md`. Executes exactly the activated order.
  Never merges, never self-approves, never adjudicates DHA.
- **BOOTSTRAP / ICA:** separately scoped; inspecting this repository does not switch role.

See `AGENTS.md` (root router), `oap/README.md`, `docs/OAP-RUNBOOK.md` and
`docs/AGENT-ROLE-SETUP.md`. Codex is the only operational client; no CLAUDE.md or Claude
launcher is part of this profile.

## Work, publication and reporting

1. Strategy finalizes one immutable order `oap/orders/<ID>-<slug>.md` and atomically
   publishes the exact-ID pointer `oap/active` (ID + LF). Absent pointer = inactive.
2. The coding wrapper consumes the control FIFO wake-up exactly once, inspects durable
   state, and starts one fresh coding invocation with the compact read set.
3. Coding implements within allowed paths, commits/pushes non-report work including the
   exact order/pointer bytes, opens/amends the objective PR, records the literal
   implementation head, then commits only the immutable report
   `oap/reports/<ID>-<slug>.md` (report-only first parent, `SELF` marker) and verifies
   remote publication before sending the exact two-byte response OK.
4. Strategy reviews the exact report head, required CI, DHA registration and combined
   risk; only strategy may perform an authorized development merge under separately
   attributable scoped delegation. Release and production remain human.
   An objective PR uses `Closes #<issue>` only when it fully satisfies that
   issue. After the merge, strategy verifies the closure; a satisfied issue
   that remains open is reconciled with a factual merged-PR closeout.

## Adoption

The one-time supervised conversion-adoption session and the activation procedure are
defined in `docs/OAP-RUNBOOK.md` (section "Conversion adoption") and in
`docs/decisions/0014-concentrated-oap-workflow-conversion.md`. Bootstrap materialization
is local and inactive: no active pointer, no operational signals, no commits or PRs.

Historical process text of the previous loop is preserved at
`docs/bootstrap/1/previous/oap-workflow.pre-concentrated.md`. Work-order documents
under `docs/work-orders/` remain historical accepted baselines.
