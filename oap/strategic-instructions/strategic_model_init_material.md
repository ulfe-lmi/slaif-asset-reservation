# Strategic model initialization material — SLAIF Asset Reservation

Substantive continuity material for the long-lived STRATEGIC role (generation 1,
2026-09-13). This is not a pasted transcript: it distills the project agreement, source
state, work program and readiness from the canonical sources named in
SOURCE-REFERENCES.md. Re-read canonical sources at every incarnation; trust this file
for orientation, not for current truth.

## 1. Product agreement (stable)

SLAIF Asset Reservation is a professional Linux-hosted reservation authority for shared
laboratory resources (initially machines and GPUs). Humans use browser sessions; agents
use owner-issued scoped bearer tokens; staff operate policies, blackouts and cross-user
lifecycle through a management UI. One entitlement engine, hierarchical inventory,
policies, audit, tokens. A reservation is an entitlement recorded by the service, not
proof that any process obeyed it. The user explicitly rejected the salon-domain
repurposing; Neumann and all lab machines are protected external resources; reservation
is not execution; no LLM in the product runtime. Codex is a development client only.

## 2. Source and repository state at initialization

- Repository: private `ulfe-lmi/slaif-asset-reservation`, default branch main.
- Observed baseline main: `1fcc2c91d793556a91711365abef562604b62f84` (merged PR27); remote main verified identical to
  local at bootstrap on 2026-09-13; no open PRs/issues observed then.
- Work Orders 0001-0013 are completed historical work with merged PRs; their evidence
  (including the historical 419-test report and main push CI run 28589883454) is
  historical, not a current measurement and not an ICA.
- Accepted architecture preserved byte-identically at
  `~/codex-work/slaif-asset-reservation/docs/bootstrap/1/previous/docs-architecture.md`; the current canonical
  architecture is root `~/codex-work/slaif-asset-reservation/ARCHITECTURE.md` (candidate until human adoption).
- Root `~/codex-work/slaif-asset-reservation/PLAN.md` is a newly synthesized agreement (labeled as such); the
  zero-entry `~/codex-work/slaif-asset-reservation/CRITICAL.md` is a seed installed only because no register existed
  locally; a discovered pre-existing register is always preserved.
- CLAUDE.md was absent at the inspected baseline; this profile is Codex-only and
  generates no operational CLAUDE.md.

## 3. The conversion you now steward

The accountable human requested the Concentrated OAP profile for this existing project.
Bootstrap generation 1 materialized candidate governance, helpers and fixture tests
locally; it committed nothing and activated nothing. Your duties now:

1. Treat every `initial-orders/` draft as **DRAFT UNTIL STRATEGIC RECONCILIATION**:
   inspect current remote/runtime facts, fill final metadata with actual identities,
   then publish only when separately authorized.
2. Keep the one-time conversion adoption (WO0014) on the human-merge path; never use
   delegated authority to approve the conversion's own installation.
3. Preserve the product: application bytes, migrations, lockfile, sanitized inventory,
   ADRs 0001-0013, Git history and accepted exclusions are preservation targets.
4. Resolve D0 directly; investigate and choose D1 with all-five CRITICAL discipline;
   stop at D2 and continue only safe independent work.
5. Review at the exact head; merge development work only under separately attributable
   scoped delegation with verified merge side-effect absence; coding never merges.
6. Require ICA at the exact merged revision before any milestone acceptance; human
   judgment and separate release authorization always remain human.

## 4. Work program orientation (see INITIAL-ROADMAP.md)

- 015-a: M-CONVERSION round-trip canary (first operational objective after adoption).
- 016-a: pilot-readiness failure boundary qualification.
- 017-a: rehearsal ownership and failure-safe cleanup qualification.
- 018-a: isolated PostgreSQL backup/restore end-to-end proof.
- 019-a: booking/maintenance/import concurrency qualification.
- 020-a: human-agent-management pilot path through actual adapters.
Dependencies: 016/017/019 may reconcile independently once 015 is accepted; 018 depends
on owned-resource safety; 020 assembles accepted evidence and a fresh ICA. No draft is
authorized by materialization alone.

## 5. Readiness at initialization (honest labels)

- Existing functionality: source-observed internal-alpha baseline; NOT re-qualified.
- Helper materialization: completed locally with fixture tests (see receipt); product
  runtime NOT RUN.
- Operational client/runtime: UNCONFIGURED (models/argv/auth pending qualification).
- Remote publication: BLOCKED until explicitly configured and authorized.
- Conditional strategic merge: DISABLED until attributable scoped activation.
- Independent conversion closure: UNPROVEN.
- Real deployment/release: NOT AUTHORIZED.

## 6. Continuity discipline

Write a private handoff (workorders/STRATEGIC-HANDOFF.md) at compaction/restart with
accepted hashes, observed main/PR, active ID, publication state and the first next
permitted action. Never store secrets or fork canonical documents here. A lost
notification after a remote report means review, not rerun. Explicit quit stays stopped.
