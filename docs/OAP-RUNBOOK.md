# OAP RUNBOOK — setup, operation, adoption (candidate profile)

Generation 1. This runbook describes the installed candidate profile. Until human
adoption and separately attributable activation, the only permitted mode is local
inspection, dry runs and the fixture test suite.

## 1. Roles and homes

| Role | Start directory | Instruction source | Home |
|---|---|---|---|
| CODING | `/home/ubuntu/codex-work/slaif-asset-reservation` | `AGENTS.md` router -> `oap/coding-instructions/AGENTS.md` | `/home/ubuntu/codex-supervision/slaif-asset-reservation/agent-homes/coding` |
| STRATEGIC | `/home/ubuntu/codex-supervision/slaif-asset-reservation` | installed `/home/ubuntu/codex-supervision/slaif-asset-reservation/AGENTS.md` (versioned source `/home/ubuntu/codex-work/slaif-asset-reservation/oap/strategic-instructions/AGENTS.md`) | `/home/ubuntu/codex-supervision/slaif-asset-reservation/agent-homes/strategic` |
| ICA | isolated | `/home/ubuntu/codex-work/slaif-asset-reservation/oap/prompts/ica-start.md` + `oap/audit/ICA-PROTOCOL.md` | fresh isolated context |

Both operational clients are Codex with separate private CODEX_HOME directories. No
operational CLAUDE.md or Claude launcher exists. Role markers are routing aids, not
authentication.

## 2. Setup (before any credentials)

```bash
/home/ubuntu/codex-work/slaif-asset-reservation/oap/bin/doctor.sh --repo /home/ubuntu/codex-work/slaif-asset-reservation --strategic-home /home/ubuntu/codex-supervision/slaif-asset-reservation --level structural
/home/ubuntu/codex-work/slaif-asset-reservation/oap/bin/launch-setup-tmux.sh --repo /home/ubuntu/codex-work/slaif-asset-reservation --strategic-home /home/ubuntu/codex-supervision/slaif-asset-reservation
```

The setup tmux session creates two side-by-side shells (strategy home left, repository
right) on an isolated owned socket. It works without models, authentication or remote
access and activates nothing. Log in/configure each role independently; never copy
authentication files between homes.

## 3. Qualification (still required before operation)

1. Record installed Codex version/help/config and safe instruction discovery
   (`docs/AGENT-ROLE-SETUP.md` lists the exact checks).
2. Fill `/home/ubuntu/codex-supervision/slaif-asset-reservation/runtime.env` (mode 0600) with supported argv arrays and model
   identifiers only after discovery; no silent fallback; no credentials in the file.
3. Qualify the private remote publication path and inspect merge side effects
   (workflow/app/webhook); unverified external effects keep merge delegation blocked.
4. Establish the human adjudication provenance mechanism (externally signed artifact or
   verified GitHub identity); bootstrap examples are not a populated allowlist.

## 4. Activation (human-attributable, separate step)

A human records an externally attributable activation identifying: repository, base
branch, accepted governance commit/digest, allowed runtime/roots/network/resources,
selected milestone/objective range, development-merge permission scope, acknowledged
merge side-effect review, adjudicator provenance mechanism and revocation/stop
procedure. `/home/ubuntu/codex-supervision/slaif-asset-reservation/runtime.env` gains `OAP_ACTIVATION_ENABLED=true` plus the authority
reference **only after** that record exists. The file is data, never proof.

## 5. Operation (only after activation)

```bash
/home/ubuntu/codex-work/slaif-asset-reservation/oap/bin/launch-oap-tmux.sh --repo /home/ubuntu/codex-work/slaif-asset-reservation --strategic-home /home/ubuntu/codex-supervision/slaif-asset-reservation
```

Gates (all required): doctor operational readiness, accepted governance/copy
identities, source/projection integrity, qualified runtime/client/remote, no
conflicting active state or duplicate processes, checked merge side effects. Strategy
publishes 015-a (or the next reconciled objective) via `publish_order.py`; the coding
wrapper consumes exactly one wake-up per round; reports follow the PR-before-report
sequence; strategy reviews the exact head; development merge only under scoped
delegation. Explicit quit stops owned wrappers; nothing auto-restarts.

## 6. Conversion adoption (one-time, human-governed)

WO0014 is reserved for this conversion. After the human reviews
`BOOTSTRAP-RECEIPT.md` (kept at the bootstrap root, outside this repository), a
**separately authorized supervised adoption session** may create the conversion
issue/branch/PR using the existing human-merge workflow. It publishes only the reviewed
conversion scope plus necessary harness/regression repairs; it does not activate OAP,
execute product drafts, use delegated merge or deploy. The adoption PR is
**human-merged**. This session is a scoped transition exception recorded in
ADR 0014; it does not loosen normal coding's active-order rule. After acceptance,
refresh the strategic installed copies at a quiescent checkpoint (backups preserved,
private state untouched).

## 7. Inactive and recovery

Absent `oap/active` = inactive. Empty/malformed pointer = CORRUPT (preserve, stop).
Recovery follows `oap/RECOVERY.md`. Bootstrap materialization never creates an active
pointer, operational signal, commit, PR or order.
