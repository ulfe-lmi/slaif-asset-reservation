# PLAN — existing SLAIF Asset Reservation agreement and conversion

**Authorship:** newly synthesized from the settled conversation and the inspected repository, not a
byte-preserved finalized PLAN.md (none was present). **Observed software revision:**
`1fcc2c91d793556a91711365abef562604b62f84`. **Design date:** 2026-09-07.
This is a handoff agreement for preserving and governing an existing product, not a greenfield spec.

## P-01. Product meaning and users

SLAIF Asset Reservation is a professional Linux-hosted reservation authority for shared laboratory
resources, initially machines and GPUs. Active human members use browser sessions; software agents
use owner-issued scoped bearer tokens; staff operate policies, blackouts and cross-user lifecycle
through a separate management UI. All act on the same scheduling records and rules. An accepted
reservation must remain policy-compliant, auditable and exclusive for its asset and effective time.

The user explicitly rejected repurposing SmartScheduling's salon staff/service/client concepts.
The original GPU-use discussion motivated the product, but neither SAM3/DAM4SAM nor any inference
model is a product dependency. Local Codex may eventually reserve an idle Neumann GPU and call a
separate deterministic execution gateway. The reservation app does not host an LLM, execute jobs,
SSH into the lab, replace Slurm, or enforce physical exclusivity. Neumann and all lab machines are
protected external resources during this conversion. Hardware labels in sanitized inventory remain
unverified until a human inventory process verifies them.

## P-02. Existing implemented baseline to preserve

The remote, private repository is `ulfe-lmi/slaif-asset-reservation`; default branch main. The current
request changes development workflow, not repository identity or visibility. Preserve the entire
Git ancestry and merged evidence. Main is the merge of PR27, not its old feature head.

| Historical work order | Delivered baseline | Historical PR / issue |
|---|---|---|
| Bootstrap constitution | Discovery, baseline decisions, sanitized inventory and governance | PR1 |
| 0001 | Django/PostgreSQL executable scaffold, custom user, CI/container/security settings | PR3 / #2 |
| 0002 | Hierarchical inventory, safe bootstrap import, staff-session asset API | PR5 / #4 |
| 0003 | Policies/reservation/audit services; UTC/effective-end/exclusion/concurrency | PR7 / #6 |
| 0004 | Human sessions, timezone/profile, private availability and owner reservation UI | PR9 / #8 |
| 0005 | Scoped token lifecycle, pepper/verifier, one-time UI and authenticator | PR11 / #10 |
| 0006 | Bearer reservation/availability/me APIs, problem details and idempotency | PR13 / #12 |
| 0007 | Staff management, maintenance blackouts, audit filtering/export | PR15 / #14 |
| 0008 | Production-shaped examples, safe logs, operational/backup/restore/purge commands | PR17 / #16 |
| 0009 | Synthetic-only migration parser/mapping/plan/apply/reports | PR19 / #18 |
| 0010 | Verification-only alpha review and docs continuity repair; not independent certification | #20 / PR21 |
| 0011 | Disposable deployment rehearsal and readiness checklist | PR23 / #22 |
| 0012 | Operator pilot preparation runbook and communication templates | PR25 / #24 |
| 0013 | Aggregate read-only pilot_readiness_check, human/JSON/strict modes | PR27 / #26 |

The conversation reports 419 tests on the PR27 implementation, preceding six browser tests and
narrow suites across token, concurrency, operational and migration behavior. The exact main push
run 28589883454 was retrieved as successful, event=push, head=the baseline above. These are historical
results; this package design did not rerun Django, PostgreSQL, Docker or browser tests. They are
not an ICA and do not prove untested failure paths. A post-conversion exact-head regression run is
required after separately authorized adoption.

## P-03. Architectural commitments

Preserve the modular Django monolith, Python3.13, Django5.2/DRF3.16, PostgreSQL17, uv/uv.lock,
server-rendered templates, Gunicorn/WhiteNoise, local OpenAPI UI assets and Docker Compose.
Business services own policy, locking, lifecycle and audited writes; adapters own input and output.
PostgreSQL GiST range exclusion remains the final same-asset conflict arbiter. The full canonical
architecture and SAR requirement index are in ARCHITECTURE.md and specifications/REQUIREMENTS.json.
No model-backed decision-making enters the product runtime merely because its development is agentic.

Keep opaque UUID identities, half-open UTC effective-end semantics, explicit timezone display,
no silent DST guesses, same-transaction audit, owner-only member/API routes, separate staff scope,
one-way token verifiers and distinct pepper, scoped idempotency, private availability and safe
operational diagnostics. Current asset discovery over REST is staff-session-only; knowing a valid
bearer token does not make asset list/detail accessible. Do not advertise full agent-side resource
search or atomic allocation as implemented.

## P-04. Deferred product requirements and exclusions

The original ambition included professional external hosting and broader resource policy. Later
accepted work orders explicitly retained broad internal-alpha human access and deferred project/
membership/resource restrictions. Preserve the ambition as deferred, not secretly implemented or
silently deleted. Current alpha scope excludes OIDC/password reset/email/notifications, dedicated
resource-manager delegation, token lifecycle or management REST APIs, service-account/admin token
issuance, monitoring stack, background scheduler, full operating-hours rules, physical probe,
atomic capability allocation, execution gateway and real SmartScheduling migration/cutover.

A first external or institutional pilot still needs an actual approved host/network/TLS/identity/
operator/resource-policy/backup decision. The historical runbooks are not deployment authorization.
A real restore drill was not established by the reports; refusal/dry-run tests and an operator
recipe are different evidence. Protected external work is D2. This package authorizes none of it.

## P-05. Newly requested workflow adaptation

The human explicitly requests Concentrated OAP according to the attached generator, for the existing
project, using this conversation AND current repository state; Codex only; remove CLAUDE.md from
operational discovery. Adopt separated long-lived strategic and fresh-per-round coding roles,
compact executor context, HWP/HJP/DHA, D0/D1/D2, tested local transport/helpers, exact order/report
publication, conditionally delegated development merge and Independent Closure Audit.

This supersedes old human-only-per-PR development workflow only through the controlled adoption and
activation sequence. Bootstrap materialization is local and inactive. Existing product law stays in
force. The conversion adoption PR itself remains human-merged; later strategic merges require a
specific human-attributable delegation and a checked no-deployment-on-merge boundary. Never treat a
role environment variable, file hash, model confidence or a typed human name as authorization.

The four instruction roles are different: extracted root bootstrap constitution; repository tiny
router; dense coding constitution; full strategic home constitution installed from versioned source.
A new full root ARCHITECTURE.md is authored now and a compact mapped projection supplied for coding.
The old architecture is preserved unchanged as a historical accepted baseline with explicit drift
annotations outside it. No operational CLAUDE.md is generated. Both operational clients are Codex;
model/provider configuration and actual installed CLI syntax require qualification.

## P-06. Milestones and evidence

**M-EXISTING:** implemented internal-alpha baseline, historically reviewed/tested with limitations.
It is a preservation target, not a new completion claim. Product runtime qualification must name an
exact merged revision; source inspection and historical reports have distinct confidence labels.

**M-CONVERSION:** helper/governance materialization and adoption. Gate: path/history protection,
canonical/projection coverage, Codex-only role routing, report-only commit mechanics, FIFO framing,
DHA/human authority, recovery tests and migration diff all evidenced; independent conversion audit
and human adoption before any operational canary. This is a pre-activation safety/adoption gate;
full M-CONVERSION closure follows the authorized canary, a fresh exact-merged-revision ICA and human
milestone judgment. No app behavior change is required for this gate.

**M-LOCAL-PILOT-EVIDENCE:** possible next governed development target, not automatically selected by
this bootstrap. Prove actual human/agent/management entry paths plus safe deployment/recovery on
owned disposable infrastructure, repair evidence-backed baseline defects, then architecture-driven
ICA. Inert drafts are provided so future strategy need not rediscover context. They require explicit
activation scope and live reconciliation; no product draft runs during bootstrap.

**M-EXTERNAL-PILOT / M-RELEASE:** blocked pending human host/identity/exposure/data/risk/operations
choices, applicable latest attributable DHA ACCEPTED dispositions, independent evidence and separate
release/deployment authorization. A completed queue, all-green CI or a readiness command is not this gate.

## P-07. Sources, uncertainties and continuity

See SOURCE-MAP.md for provenance and differences from old sources. Do not repeat historical assistant
errors that called an already merged PR open or requested duplicate post-merge work. Always read live
state once per relevant transition; an empty PR-only workflow wrapper result does not imply absent
push CI. The generic GitHub run GET exposes the actual known main run.

No exact target-machine checkout path, current strategic model ID, role authentication, tmux session,
sandbox approval, independent auditor or live deployment target is assumed. Use the named overrides
and proposed local defaults. Preserve the historical coding preference chatgpt-5.5-high without
assuming it is an installed/valid contemporary alias. No provider/model fallback is automatic.

Existing process state was absent in the inspected tracked tree. Bootstrap must still inspect local
untracked/private state before writing. A pre-existing register or active order discovered locally
is preserved and reconciled, never wiped. Empty CRITICAL seed here means no register was available,
not that all future human risk decisions have been made.
