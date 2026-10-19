# PLAN — existing SLAIF Asset Reservation agreement and conversion

**Authorship:** newly synthesized from the settled conversation and the inspected repository, not a
byte-preserved finalized PLAN.md (none was present). **Observed software revision:**
`1fcc2c91d793556a91711365abef562604b62f84`. **Design date:** 2026-09-07.
This is a handoff agreement for preserving and governing an existing product, not a greenfield spec.
**Temporal scope:** P-01–P-07 record the original 2026-09 conversion/baseline agreement; their
chronology and evidence are preserved and are historical for that date. The current selected
targets (2026-10-04, 2026-10-17) are recorded in P-04, P-06 and P-08.

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

Preserve the modular Django monolith, Python3.13, Django5.2/DRF3.17, PostgreSQL17, uv/uv.lock,
server-rendered templates, Gunicorn/WhiteNoise, local OpenAPI UI assets and Docker Compose.
Business services own policy, locking, lifecycle and audited writes; adapters own input and output.
PostgreSQL GiST range exclusion remains the final same-asset conflict arbiter. The full canonical
architecture and SAR requirement index are in ARCHITECTURE.md (SAR index, SAR-001 through SAR-038).
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
silently deleted. As of 2026-10-04 the attributable human selected Internet-reachable
authenticated service development as the current target (P-06, M-INTERNET-UX-PILOT);
projects/memberships/resource restrictions remain deferred and real Internet exposure
remains a human D2 decision. Current alpha scope excludes OIDC/password reset/email/notifications, dedicated
resource-manager delegation, token lifecycle or management REST APIs, service-account/admin token
issuance, monitoring stack, background scheduler, full operating-hours rules, physical probe,
atomic capability allocation, execution gateway and real SmartScheduling migration/cutover.

A first external or institutional pilot still needs an actual approved host/network/TLS/identity/
operator/resource-policy/backup decision. The historical runbooks are not deployment authorization.
A real restore drill was not established by the 2026-09 baseline reports; refusal/dry-run
tests and an operator recipe are different evidence, and current recovery evidence belongs
to the exact reports/tests/audits at the exact revision. Protected external work is D2. This package authorizes none of it.

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

**M-LOCAL-PILOT-EVIDENCE:** 2026-09 bootstrap target, not automatically selected by that
bootstrap. Current status (2026-10-04): the old controlled-internal alpha work is implemented
and audited; report `docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-a9c3133.md` is historical and
superseded by the selected new target. It is not available as queued replay, and no human
milestone acceptance is inferred from its audit counts. Its inert drafts remain for strategy
reference only; later selection would need explicit strategy activation.

**M-INTERNET-UX-PILOT (selected 2026-10-04; software qualified; human acceptance pending):** Internet-reachable
authenticated service through a normal HTTPS endpoint and a friendly SLAIF browser experience, per
the selected contract in ARCHITECTURE.md A-15. The exact eight human meanings selected on
2026-10-04 map to: requirement 1 (Internet HTTPS/proxy boundary, plus its security paragraph) ->
SAR-039 and SAR-040; requirement 2 (default fresh-install policy) -> SAR-041; requirement 3
(public product entry) -> SAR-042; requirement 4 (browser product identity) -> SAR-043;
requirement 5 (explained accessible forms) -> SAR-044; requirement 6 (safe operator appearance
overrides) -> SAR-045; requirement 7 (SLAIF design and visual qualification) -> SAR-046;
requirement 8 (threaded Gunicorn responsiveness) -> SAR-047. Scope: bounded development,
disposable qualification, strategic development merge, and a final fresh isolated ICA over the
full current requirement index (SAR-001–SAR-047). The fresh independent
[audit at cd5a436](docs/audit/reports/M-INTERNET-UX-PILOT-cd5a436.md) classified all
47 rows IMPLEMENTED within the selected software/synthetic scope, with no mandatory
software blockers. Its independent-context, execution and operator limits remain explicit;
this is evidence for human milestone judgment, not inferred human acceptance.
[Publication freshness](docs/audit/qualification/M-INTERNET-UX-PILOT-FRESHNESS.md)
binds reuse to unchanged enforcing source and deployment assumptions. Real Internet exposure,
DNS/TLS/firewall, identity, secrets and private data remain human D2; development evidence may
present one exact revision to that decision, never deploy it. Development under this milestone
authorizes none of the M-EXTERNAL-PILOT/M-RELEASE gates below.

Original bounded development sequence, retained as a scope map rather than an active
backlog. Current qualification is recorded above. Later work still requires a new
strategy-issued order with live authority and exact scope, base and PR; historical
orders and initial UNPROVEN states are not replayed:

| # | Original slice (scope map) | Bounded scope derived from A-15 |
|---|---|---|
| 1 | runtime | Delivered by merged PR62 (031-a) on main: threaded Gunicorn baseline with regression; not future backlog. Remaining SAR-047 consistency facets (pool across image/local/production/rehearsal, six-client positive plus old-sync negative, cleanup, proxy rationale) are swept in the final qualification line, not re-implemented. |
| 2 | architecture contract | Recorded documentation-only contract slice: the selected target recorded in canonical ARCHITECTURE.md, the executor projection and the coverage record. It does NOT authorize deployment/configuration changes. |
| 3 | proxy + production security | Disposable Internet-shaped HTTPS reverse proxy: trusted-peer forwarding normalization, read/idle/body bounds, client IP/TLS header handling; plus production configuration for the qualified topology: Compose, allowed hosts/CSRF origins, private docs/schema, fail-closed production settings (A-15 topology facet; SAR-039). |
| 4 | sharedabuse | Shared cross-process rate bounds for member and administration login plus API traffic; configurable rates, trusted-client identity, expiry/cleanup, safe failure, no permanent lockout (A-15 abuse facet; SAR-040). |
| 5 | defaultpolicy | Supported fresh-initialization path creating the `default` active global fallback policy; idempotent/atomic, upgrade-safe, unique active-global, real booking (A-15 policy facet; SAR-041). |
| 6 | landing/admin | Anonymous landing with Login and Administration actions, administration login entry, structural SLAIF administration identity, no framework branding (A-15 landing/identity facets; SAR-042, SAR-043). |
| 7 | help | Systematic explained accessible forms across member/management/administration fields, human token scopes, units/policy/DST help, validation preserved (A-15 forms facet; SAR-044). |
| 8 | themes | SLAIF default appearance from current references with CSS tokens, safe operator appearance overrides, Playwright-tested default/custom fixtures, semantic visual regressions (A-15 appearance facets; SAR-045, SAR-046). |
| 9 | finalqualification+freshICA | Full qualification sweep (browser fixtures at ~1440/1024/768/390, concurrency, negatives, container/health, fresh+upgrade policy init), standard five exact-head checks, links/pip audit, then the fresh isolated ICA over SAR-001–SAR-047 at the exact merged revision (A-15 qualification facet; all rows). |

**M-EXTERNAL-PILOT / M-RELEASE:** blocked pending human host/identity/exposure/data/risk/operations
choices, applicable latest attributable DHA ACCEPTED dispositions, independent evidence and separate
release/deployment authorization. A completed queue, all-green CI or a readiness command is not this gate.
M-INTERNET-UX-PILOT development does not authorize any part of this gate.

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
## P-08. Selected group authorization extension (2026-10-17)

**Human provenance.** The attributable human selected M-GROUP-AUTHORIZATION on 2026-10-17
(request sections 1–11: group-based capabilities, exact-asset booking, separate cross-user
read bearer and external identifier; workflow clarification: concentrated OAP, coding agent).
The selected target is recorded in ARCHITECTURE.md A-16 with stable rows SAR-048–SAR-053,
each initially UNPROVEN until a fresh independent closure at the exact merged revision.
The original 2026-10-17 selection is historical provenance: at selection time no
capability, route, scope, field, command or migration in A-16 existed yet, and the
principle that selection is not completion remains binding.

**Selected target, no infrastructure authorization.** Extend existing Django groups and
individual permissions across member, management and Administration surfaces; explicit
exact-asset booking eligibility; separately authorized cross-user read-only browser and
bearer access; one optional external user identifier. This milestone authorizes bounded
development and independent qualification only. It authorizes no deployment, real
exposure, DNS/TLS/firewall, identity or secret administration, execution or physical
allocation; the external enforcer owns account mapping and enforcement outside this
application.

**Development purposes — original scope map, retained as history.** The selected-target
contract recorded by order 047-a (ARCHITECTURE.md A-16, SAR-048–SAR-053, compact
projection, docs/authorization.md) was the binding prerequisite for every purpose below.
Each purpose required its own strategy-issued order with live authority, exact scope,
base and PR; the numbering is a private orientation, not an active backlog. The table is
retained as the original selection/scope map — a labelled history, not nonexistent
future implementation or a new replay queue; per-purpose delivered status is recorded
under Current state below:

| # | Purpose (derived from A-16) | Stable rows |
|---|---|---|
| 048 | One additive grant system: documented application permissions, baseline booking-permission assignment for existing non-service-account users, optional external identifier, deliberate legacy-staff upgrade setup | SAR-048, SAR-052, SAR-053 |
| 049 | Exact-asset booking eligibility: unrestricted/group-restricted assets, shared browser/bearer enforcement, no inheritance or historical reservation rewriting | SAR-049 |
| 050 | Explicit cross-user management visibility: All reservations browser with validated filters/pagination and granular mutation controls | SAR-050 |
| 051 | Explicit read-all bearer authority: reservations:read_all scope AND current owner permission, bounded issuance, live grant revocation, minimal cross-user representation | SAR-051 |
| 052 | Full qualification and fresh independent ICA over SAR-001–SAR-053 at the exact merged revision, standard five exact-head checks; human milestone judgment separate | all rows |

**Current state (delivered at merged evidence; fresh full-53 ICA published,
human milestone judgment pending).** Purposes 048–051 are
delivered at the actual merged evidence named below, cited to bind the exact merged
state; a hash, report or CI result alone is not proof that an implementation exists, and
none of this is milestone closure, release, deployment or human acceptance.
**048 — one additive grant system, external identifier and deliberate upgrade setup:**
delivered by PR100 (objective 48, rounds 048-a…048-c), merged 2026-10-17 at
`12947e9b368445eeb4a48416421626224b49f4dc`, with immutable reports
`oap/reports/048-a-authorization-foundation.md`,
`oap/reports/048-b-identifier-review-closure.md` and
`oap/reports/048-c-deterministic-verification-clock.md`.
**049 — exact-asset booking eligibility:** delivered by PR102 (rounds 049-a/049-b),
merged 2026-10-17 at `b873f4cf1071bded044ba456625b0ced355407a8`, with immutable reports
`oap/reports/049-a-booking-eligibility.md` and
`oap/reports/049-b-booking-eligibility-corrections.md`.
**050 — explicit cross-user management visibility and granular capabilities:**
delivered by PR104 (rounds 050-a…050-c), merged 2026-10-18 at
`3461fa0106c55994a959f88450d4866b018ad890`, with immutable reports
`oap/reports/050-a-granular-management-authority.md`,
`oap/reports/050-b-operator-authorization-guide.md` and
`oap/reports/050-c-report-identity-binding.md`.
**051 — explicit read-all bearer authority:** delivered by PR106 (rounds 051-a/051-b),
merged 2026-10-19 at `1adf776e553bcd56cd0a7fa229c8eb0bcb56c1fe`, with immutable reports
`oap/reports/051-a-read-all-bearer-authority.md` and
`oap/reports/051-b-read-all-evidence-closure.md`.
**052 — full qualification and fresh independent ICA:** the fresh full53 independent
closure audit at the exact merged revision
`1adf776e553bcd56cd0a7fa229c8eb0bcb56c1fe` is published unchanged as
[M-GROUP-AUTHORIZATION-1adf776](docs/audit/reports/M-GROUP-AUTHORIZATION-1adf776.md)
(SHA-256
`7b03025c4a4f2757b5a0d2e252878ed5f236594bdc2953e2bb57dd40a28c43f1`). That closure is
FAILED, not green: 48 rows IMPLEMENTED and 5 PARTIAL (SAR-016, SAR-037, SAR-039,
SAR-048 and SAR-053), with required findings ICA-GA-001 (current-human admission missing
on the four older staff read surfaces) and ICA-GA-002 (this canonical-status
reconciliation); optional ICA-GA-O1 provenance refinements remain separately recorded and
are not ordered by this text. ICA-GA-001/002 are remediated under issue #107 (order
052-a), merged 2026-10-19 at `bddda89a5ddb428c64a36c7c2bd1f35cab2acbba`.
The fresh independent full-architecture re-audit at that exact repaired
merged revision is published unchanged as
[M-GROUP-AUTHORIZATION-bddda89](docs/audit/reports/M-GROUP-AUTHORIZATION-bddda89.md)
(SHA-256
`574024e2511af121f4665a89fa53cdfd0eefb12c816e82697ed2b9f724cd4177`) with its
[publication freshness record](docs/audit/qualification/M-GROUP-AUTHORIZATION-FRESHNESS.md):
53 IMPLEMENTED and 0 PARTIAL/ABSENT/UNPROVEN within the stated software/synthetic
scope, with no mandatory finding. That software/synthetic closure evidence
supports presentation to HUMAN milestone judgment only: it is not HUMAN
milestone acceptance, and no release, real deployment or exposure,
DNS/TLS/firewall, identity or secret administration, private or lab data
access or physical allocation is inferred from it; the human owns that
separate milestone and D2 judgment.

**Deferral reconciliation.** SAR-036’s deferral of existing-group/resource restriction
and delegated management capabilities is superseded only by A-16. All other deferrals
remain: projects, organizational trees, delegated group ownership, general policy
languages, token/management admin or mutation bearer APIs, OIDC/password
reset/notifications, monitoring stack, scheduler, automatic physical allocation, real
migration/cutover and the execution gateway.

**Milestone history preserved.** M-EXISTING, M-CONVERSION, M-LOCAL-PILOT-EVIDENCE,
M-INTERNET-UX-PILOT and M-EXTERNAL-PILOT/M-RELEASE remain as recorded in P-06; their
chronology, evidence and gates are unchanged. M-INTERNET-UX-PILOT remains the
software-qualified baseline for the Internet/UX facets, and its prior evidence is
historical context for this changed authorization target. Human milestone acceptance,
release and all real infrastructure decisions remain separate and are not inferred from
development evidence.
