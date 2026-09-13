# Materialize and validate the existing-project conversion

This is the bootstrap agent's executable work specification, not instructions for the planning
assistant to operate the user's machine. You must create actual files/directories/helpers/tests
and a truthful receipt, then stop inactive. Do not substitute another plan, ZIP or title-only scaffolds.

## I-01. Non-negotiable transition boundary

Existing private repo: ulfe-lmi/slaif-asset-reservation. Inspected main:
1fcc2c91d793556a91711365abef562604b62f84. Preserve all application code, tests, migrations, lockfile,
sanitized inventory and history. This task authors governance infrastructure, not product features.
Do not run old WO0001–0013. No real commits/pushes/issues/PRs/merges or active orders in bootstrap.
The one-time adoption procedure is separate and human-controlled; see MIGRATION-ADOPTION.md.

Run stages: input verification -> read-only destination inventory -> no-write plan -> scoped local
materialization -> fixture tests/semantic review -> receipt -> STOP. If a protected prerequisite is
missing, complete independent safe work and report precisely what remains blocked. Do not fake success.

## I-02. Input checks and source fidelity

Run `python3 tools/check_package.py --root .` if Python3 is available, and independently verify
INPUTS.sha256. PACKAGE-MANIFEST lists all payload files except itself and INPUTS.sha256; INPUTS.sha256
lists every file except itself, including the manifest. No circular hashes. Verify generator/OAP
source and preserved legacy architecture/blob identities recorded by SOURCE-MAP.

PLAN/ARCHITECTURE are newly authored canonical candidates. Copy their initial package bytes exactly
into the target after checking absence/conflicts. They are not permissions to override a different
approved file found locally. CRITICAL seed applies only when no register exists. Original product
architecture is preserved exactly before replacing docs/architecture.md with a compatibility pointer.
Do not silently normalize the old bytes. Preserve source snapshots under non-discovered names.

## I-03. Resolve destinations before writing

BOOTSTRAP_ROOT = actual extracted directory, canonicalized.
REPO_ROOT = explicit OAP_REPO_ROOT if provided; proposed default
`$HOME/codex-work/slaif-asset-reservation` otherwise.
STRATEGIC_HOME = explicit OAP_STRATEGIC_HOME if provided; proposed default
`$HOME/codex-supervision/slaif-asset-reservation` otherwise.

Reject identical or nested canonical roots. Validate existing parent directories, symlink chains,
ownership, file types and write boundaries. Do not use /mnt/data paths from this planning environment
on the target machine. Support spaces/Unicode, Git worktree .git files and ordinary .git directories.
Do not overwrite global/ancestor instructions. Reject a destination regular file, symlink escape,
foreign-owned sensitive path or running installation.

Prefer an explicitly supplied existing checkout. If proposed REPO_ROOT is absent, a read-only clone
of the known existing remote may materialize it using the operator's already authorized Git access;
do not `git init` a replacement app or create/change remotes. If private access is unavailable,
produce safe candidate governance in a clearly labelled staging directory and mark actual repo
installation BLOCKED, not complete. Do not copy authentication files to make access work.

Read git status including untracked files, current branch/HEAD, remotes, object format, worktree root,
open PR/issues and latest relevant main state if authenticated access is available. The source
package baseline is a comparison anchor, not an instruction to reset an advanced branch. A newer
main requires scoped reconciliation and updated source identities; unknown product changes block
overwriting dependent canonical files, not unrelated inspection. Never reset/clean/stash/force-push.

Inventory every existing AGENTS.md, CLAUDE.md, root PLAN/ARCHITECTURE/CRITICAL, oap/orders/reports/active,
strategic copies/FIFOs/runtime.env and known governance manifests before deciding ownership. Active
roles or pointer trigger quiescent migration plan, not new-install defaults. Preserve dirty/untracked
files. A touched file with unrelated modifications is conflict; do not replace it. `.env`, dumps,
credentials and private exports are never inputs to this package.

## I-04. No-write planning and manifest-owned writes

Implement `oap/bin/bootstrap-two-agent-oap.sh --dry-run --repo ... --strategic-home ...` (or its
underlying stdlib module) with default dry-run. Dry-run makes no writes, no temp files in destination,
no FIFO creation, no Git mutation and no model invocation. Print safe created/identical/replace/
conflict classification. Each replacement is explicitly listed and backed up to a private
bootstrap-backups generation directory before atomic scoped write.

Apply only generated manifest-owned paths. Write temp files in target directories, fsync and atomic
rename with expected previous identity checks. Do not follow unsafe symlinks. Identical rerun is a
true no-op (including metadata where practical). Explicit `--refresh` may back up and replace known
previous generated versions at a quiescent checkpoint, preserving runtime config/auth/logs/drafts/
CRITICAL/history. Any unknown content conflict stays untouched and reported.

## I-05. Canonical product and legacy-document migration

Materialize these new root files from package sources: PLAN.md, ARCHITECTURE.md, CRITICAL.md when
absent, ARCHITECTURE-for-agents.md from blueprint, OAP-COMMUNICATION-coding-agent.md from blueprint,
STATUS.md and TESTING.md (generate according to blueprints/specs). Do not replace README wholesale.

Known replacements/edits in the conversion candidate:
1. Archive existing root AGENTS.md byte-identically under
   docs/bootstrap/<generation>/previous/AGENTS.pre-concentrated.md; install tiny router.
2. Archive docs/architecture.md unchanged under
   docs/bootstrap/<generation>/previous/docs-architecture.md; replace its current path with a
   concise compatibility pointer to root ARCHITECTURE.md and historical archive. No second editable
   full architecture. List explicit drift reconciliation from SOURCE-MAP.
3. Preserve all existing root SECURITY.md disclosure/security content. Append a process/security
   section from blueprint; don't replace its contact/reporting policy. New TESTING.md is substantive
   and points to existing exact suite definitions; compact coding cores remain small.
4. Archive old docs/oap-workflow.md before replacing current process instructions with this profile's
   role/authority/publication/candidate-adoption references. Preserve historical work-order docs.
5. Make only targeted updates to CONTRIBUTING.md, .github issue/PR templates, docs/README.md,
   README.md, docs/roadmap.md and docs/project-handoff.md to distinguish legacy human-merges,
   conversion adoption, inactive bootstrap and conditional future strategic development merges.
   Remove mandatory CLAUDE reads/client fallbacks from active instructions; do not rewrite old PRs.
6. Add a conversion ADR at the next unused ADR number (expected0014; discover first) documenting
   this human-requested workflow change, root architecture consolidation, role/router/context model,
   manual adoption exception, conditional delegated merge and independent closure. Do not alter
   product ADRs0001–0013 or claim their deferred features have shipped.
7. Update .gitignore/.dockerignore only for generated private-runtime paths and to prevent accidental
   inclusion of agent homes/FIFOs/logs/receipts; do not remove existing secret/export/sidecar rules.
8. Add pure harness tests to existing CI quality job while preserving quality/test/security/container
   and all existing product steps. No deployment trigger, secret change or permission expansion.
9. Update MANIFEST.sha256 for existing listed changed files plus public immutable generated paths.
   Keep dynamic active/order/report/register/private state out of static seed-equality checks.
   Document this separation; do not broadly glob secrets into any manifest or archive.

Codex-only: no tracked CLAUDE.md was found at the baseline. Do not invent a deletion. If a later
tracked file exists, inspect it, preserve unique obligations in canonical new law, archive original
bytes as CLAUDE.pre-conversion.md and remove only that operational file through the candidate diff.
Untracked or externally owned CLAUDE.md is preserved and reported; never delete unknown files.
Source books may mention Claude; they remain unchanged historical sources, not active instructions.
Do not remove legitimate project source text merely because it names a different tool historically.

## I-06. Required coding workspace inventory

Create/populate all of the following; combine no responsibilities away. Additional shared helper
modules are encouraged; unrelated platform scaffolding/dependencies are not.

```text
AGENTS.md
PLAN.md
ARCHITECTURE.md
ARCHITECTURE-for-agents.md
CRITICAL.md
OAP-COMMUNICATION-coding-agent.md
STATUS.md
SECURITY.md                        # preserve and extend existing content
TESTING.md
README.md                          # targeted existing-doc pointer only
.gitignore                         # preserve existing rules, scoped additions
docs/OAP-RUNBOOK.md
docs/AGENT-ROLE-SETUP.md
docs/READINESS.md
docs/DECISION-POLICY.md
docs/RUNTIME-CONSTRAINTS.md
docs/BOOTSTRAP-SOURCES.md
docs/bootstrap/<generation>/BOOTSTRAP-GENERATOR.md
docs/bootstrap/<generation>/inputs/  # immutable input snapshots, no operational AGENTS basename
docs/bootstrap/<generation>/previous/
oap/README.md
oap/RECOVERY.md
oap/COMPLETENESS.md
oap/bootstrap-sources.lock.json
oap/runtime.env.example
oap/coding-instructions/AGENTS.md
oap/coding-instructions/SECURITY-CORE.md
oap/coding-instructions/TESTING-CORE.md
oap/strategic-instructions/AGENTS.md
oap/strategic-instructions/OAP-COMMUNICATION-strategic.md
oap/strategic-instructions/strategic_model_init_material.md
oap/strategic-instructions/INITIAL-ROADMAP.md
oap/strategic-instructions/initial-orders/<every expanded inactive draft>
oap/governance/MANIFEST.json
oap/governance/DISTILLATION-MAP.md
oap/governance/CONTEXT-BUDGET.md
oap/governance/HUMAN-AUTHORITY.example.json
oap/templates/WORK-ORDER-TEMPLATE.md
oap/templates/REPORT-TEMPLATE.md
oap/templates/STRATEGIC-REVIEW-CHECKLIST.md
oap/templates/CRITICAL-ENTRY-TEMPLATE.md
oap/templates/HUMAN-ADJUDICATION-TEMPLATE.md
oap/templates/HANDOFF-TEMPLATE.md
oap/audit/ICA-PROTOCOL.md
oap/audit/ICA-REQUEST-TEMPLATE.md
oap/audit/ICA-REPORT-TEMPLATE.md
oap/audit/ICA-REQUIREMENT-MATRIX-TEMPLATE.md
oap/audit/requests/<conversion and local-pilot draft requests>
oap/prompts/coding-round.md
oap/prompts/strategic-start.md
oap/prompts/ica-start.md
oap/bin/bootstrap-two-agent-oap.sh
oap/bin/doctor.sh
oap/bin/check_governance.py
oap/bin/check_state.py
oap/bin/publish_order.py
oap/bin/append_critical.py
oap/bin/verify_report.py
oap/bin/oap_fifo.py
oap/bin/check_ica.py
oap/bin/launch-coding-agent.sh
oap/bin/launch-strategic-agent.sh
oap/bin/launch-setup-tmux.sh
oap/bin/launch-oap-tmux.sh
oap/orders/                        # empty if absent originally; not future drafts
oap/reports/                       # no fake old or future execution reports
tests/oap/                         # implemented executable fixture tests
```

Do not copy source root AGENTS.md as inputs/AGENTS.md: rename the archived bootstrap constitution
BOOTSTRAP-GENERATOR.md. Preserve source documents but prevent instruction discovery through archived
AGENTS basenames. Preserve any genuine existing reports/orders instead of emptying the directories.
New bootstrap's `oap/active` is absent; do not create an empty pointer. Generated work drafts remain
under initial-orders/private drafts and cannot be published without reconciliation.

## I-07. Required strategic workspace inventory

Install full controlled source copies and create private structure:

```text
AGENTS.md
OAP-COMMUNICATION-strategic.md
strategic_model_init_material.md
INITIAL-ROADMAP.md
SOURCE-REFERENCES.md
RUNTIME.md
runtime.env                        # 0600, activation disabled, no secrets copied
control.fifo                       # owned 0600
response.fifo                      # owned 0600
drafts/                            # expanded project drafts
critical-drafts/                    # empty; no fabricated decisions
workorders/EXECUTION_TIMINGS.md      # empty measured-result table, no invented times
workorders/STRATEGIC-HANDOFF.md
audit/requests/
audit/results/                     # empty: no fake independent audit
logs/
bootstrap-backups/
agent-homes/coding/
agent-homes/strategic/
```

Directories with private state use0700. Product PLAN/ARCHITECTURE/CRITICAL are referenced by canonical
path/revision/digest in SOURCE-REFERENCES, not copied as independent mutable governance. Installed
strategy source identities are recorded; candidate state is INACTIVE_UNADOPTED until accepted PR.
Role homes are empty except safe generated role config; never copy auth files, sessions or histories.

## I-08. Authoring/copying and compact coverage

Copy blueprints for router, full strategy, coding law, compact architecture/communication and cores
as specified. Generate full strategic communication from OAP-PROTOCOL plus concrete installed paths;
retain all OP clauses. Generate init material from PLAN/ARCHITECTURE/source state/work program/
readiness, not a pasted whole transcript. Expand every work seed into a standalone inactive order
with all fields/criteria/tests/provenance; no future SHA/PR/result fabrication.

Use full architecture/strategic law to complete DISTILLATION-MAP. Map source obligations, conditions,
exceptions/order/failure/escalation to compact clauses or explicit non-applicability reasons. Include
legacy source obligations preserved by this change. Measure exact transitive bytes and token
provenance; if no qualified tokenizer, tokens=UNMEASURED. Limits are in ROLE-CONTEXT. Compact source
hash metadata must match actual candidate source bytes. A semantic second pass is required and
recorded but never presented as independent audit.

## I-09. Helpers and tests

Implement all contracts in OAP-PROTOCOL using shared stdlib code. Do not leave executable files as
TODO stubs, echo wrappers or fake-pass validators. Fixtures use disposable Git repos/remotes,
fake Codex/remote/CI executables, real temp FIFOs and isolated owned tmux sessions. No real model,
lab/product endpoints or production credentials. Implement and actually run every required test
case in BOOTSTRAP-ACCEPTANCE. Tools missing for an area => mark BLOCKED/NOT RUN precisely; complete
independent work, never report all tests passed. Test installed CLI help/config separately from
fake invocation semantics. No implicit auth login or paid call.

Pure harness command: `python3 -m unittest discover -s tests/oap -p 'test_*.py' -v` (or equivalently
scoped pytest without application state, with exact reproducible command recorded). Default existing
product tests are not run during bootstrap because some touch deployment paths/Compose. Product
regression runs belong to separately authorized adoption in an isolated checkout/DB; document
this NOT RUN boundary in the receipt rather than claiming product verification.

## I-10. Installation receipt and inactive stop

Write BOOTSTRAP-RECEIPT.md in BOOTSTRAP_ROOT: actual roots/generation/HEAD/source identities; created/
identical/backed-up/conflicting files; preserved app/history/register; all measured context and
semantic review notes; expanded draft/requirement coverage; every test command/outcome/evidence;
installed client qualification separately; missing remote/model/auth/runtime/merge/target/auditor
prerequisites; proof no active order/operational signal/model invocation/product work/publication;
exact remaining human adoption/config/activation steps.

Distinguish input package checks, materialized helper verification, activation readiness, product
runtime qualification and human milestone acceptance. A local scaffold may be valid yet activation
blocked. Leave runtime disabled, no orders activated, no agents running, no Git commit/push/PR and
no deployment. Stop. Never print a blanket completion claim hiding blockers.
