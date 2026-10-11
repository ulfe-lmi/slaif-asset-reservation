# OAP communication — strategic role (full protocol)

Generated for this installation from the package OAP-PROTOCOL (all OP clauses retained);
paths use ~/ notation for the current user home. The versioned source lives at
`~/codex-work/slaif-asset-reservation/oap/strategic-instructions/OAP-COMMUNICATION-strategic.md`; this home holds the
installed byte-identical copy.

## OP-01. Planes, ownership, state and authorization

`~/codex-work/slaif-asset-reservation` is the existing private product Git workspace. `~/codex-supervision/slaif-asset-reservation` is the private, separate
POSIX strategic home. Roles are explicit. All real publication and execution remain
disabled until candidate adoption and attributable activation.

Canonical paths for this installation:
- `~/codex-work/slaif-asset-reservation/oap/orders/<ID>-<slug>.md`: immutable FINAL orders, strategy-authored.
- `~/codex-work/slaif-asset-reservation/oap/reports/<ID>-<slug>.md`: immutable coding reports, final report-only commit.
- `~/codex-work/slaif-asset-reservation/oap/active`: exactly ID + LF, or absent; empty/malformed is an error.
- `~/codex-work/slaif-asset-reservation/CRITICAL.md`: canonical append-only DHA register; never a private editable copy.
- `~/codex-supervision/slaif-asset-reservation/control.fifo`, `~/codex-supervision/slaif-asset-reservation/response.fifo`: notifications only, owned mode 0600.
- private `~/codex-supervision/slaif-asset-reservation/workorders/state.json`: reconstructable journal, never overrides remote.
- private `~/codex-supervision/slaif-asset-reservation/workorders/receipts/`: publication/review/install observations.
- private `~/codex-supervision/slaif-asset-reservation/runtime.env` and `~/codex-supervision/slaif-asset-reservation/activation.json`: configuration and externally
  attributable activation reference, never proof by file/name/flag alone.

Strategy writes order/pointer; coding commits their exact authorized bytes. Coding owns
bounded implementation/report changes and cannot rewrite orders, select the next
objective or merge. Strategy never changes product files concurrently with an active
coder. Human scope/authority provenance is resolved before operational writes; runtime
role markers do not authenticate people or sandbox processes. Same-account credentials
do not give a bot human adjudication authority.

## OP-02. IDs, branches, corrections and legacy history

ID grammar `^[0-9]{3}-[a-z]{1,2}$`; objective range 000-999, suffix sequence a...z,
aa...az, ba...zz using numeric suffix progression (a=1, z=26, aa=27, zz=702), not
lexicographic order. Exhaustion stops publication for a deliberate protocol revision.
Objective/round do not change on restart/compaction.

Historical WO0001-0013 and their PRs remain historical, never converted to fictional
orders/reports. WO0014 is reserved for the supervised conversion adoption, outside the
active protocol. Proposed first operational ID is 015-a, subject to checking that no
newer adopted epoch exists. One objective has one issue and one
`codex/<issue>-oap-<id>-<slug>` branch/PR. Round a creates a PR only if none exists;
an interrupted a reuses the verified PR. Corrections b onward amend that PR/branch. A
new objective is allowed only after verified merge/acceptance, or explicit recorded
abandonment with dependency reassessment. An abandoned objective is not accepted work.

Existing active order/report/register or a newer epoch discovered locally requires
quiescent migration/reconciliation; no blank reseeding. A pointer identifying a
completed round after merge is ACCEPTED/QUIESCENT, not executable. Never replay it
merely because a notification arrived. A newly bootstrapped installation has no active
pointer or operational orders.

## OP-03. Order format and publisher validation

UTF-8 LF Markdown; a single `<!-- OAP-META\n{JSON}\n-->` block precedes the body.
Required metadata: `schema_version`=1; `kind`="order"; `id`; `objective` integer;
`round`; `slug`; `state`="FINAL"; `repo` exact owner/name (`ulfe-lmi/slaif-asset-reservation`);
`base_branch`="main"; `base_sha` full actual object ID; `issue_number` positive
integer; `branch`; `pr_mode`="CREATE_OR_RESUME" for a or "AMEND" later; `pr_number`
null only for a before the initial PR exists; `previous_round` null for a, predecessor
later; `provenance` list of `{marker:H|A|E|I|C, source, section_or_evidence}`;
`requirements` nonempty SAR IDs; `governance_revision` actual accepted commit;
`source_hashes` map; `allowed_paths` and `forbidden_resources`; `decision_class`
D0|D1|D2_PREPARATION; `expected_report_path`; `tests`; `target_gate`. No
secrets/personal data.

Body sections: Goal/Scope/Non-goals/Numbered acceptance/Verification/Negative
paths/Documentation/Recovery/Reporting. Finalized fields cannot retain genuine
TODO/TBD/unknown values; quoted example literals in test cases are not unresolved
finalization fields. Publisher validates structure, source identities, role/activation,
transitions, exact repo/object format, unique file, base/current remote reconciliation,
PR identity, concrete provenance and DHA declaration. Invalid or absent declaration
always rejects.

Exactly one body declaration:
```
## Deferred human adjudication
- Decision: NONE
```
or `- Decision: APPEND CRIT-0001` with the full strategic exact payload. Initial drafts
carry state DRAFT UNTIL STRATEGIC RECONCILIATION and live only under
`~/codex-work/slaif-asset-reservation/oap/strategic-instructions/initial-orders/` and this home's `drafts/`; the
publisher never accepts them. Future SHAs/PRs/results are not fabricated. Strategy
fills final metadata after fresh remote/state inspection.

## OP-04. Two recoverable publication writes

`~/codex-work/slaif-asset-reservation/oap/bin/publish_order.py --repo ~/codex-work/slaif-asset-reservation --strategic-home ~/codex-supervision/slaif-asset-reservation --order FILE
[--dry-run] [--recover]`. All inputs are checked before any write. Dry-run performs
zero writes, not even lock/journal/cache/temp creation. Real publication uses the
private publication lock and validates current accepted state. First create the order
exclusively at its immutable destination, fsync file and directory. Then write a
same-directory pointer temp containing exact ID+LF and atomically replace/fsync
`oap/active`. Record recoverable journal state, then signal control OK with bounded
timeout. Signal failure means PUBLISHED_NOT_SIGNALED - not a failed/absent publication
and not permission to start a new ID.

An interrupted publication after order creation can complete only the identical
unresolved publication; mismatching bytes/pointer/newer state is a conflict. An
existing identical historical completed order cannot be reactivated. Replacing an
order in place is forbidden. The publisher uses expected current active, accepted
governance and remote state - never a new candidate file's self-declared permission.

## OP-05. Transport

`~/codex-work/slaif-asset-reservation/oap/bin/oap_fifo.py send --fifo PATH --timeout SECONDS`;
`receive --fifo PATH --timeout SECONDS`. Payload is exactly bytes 0x4F 0x4B (ASCII
OK), length 2, no newline/ID/status/JSON. The sender handles partial writes/EINTR and
closes the descriptor. The receiver holds a single-consumer lease, accumulates until
EOF, and rejects zero/one/>two bytes, invalid bytes, missing FIFO, symlinks and
inappropriate owner/mode; it handles partial reads, writer disconnect, timeout and
cancellation with finite tests. Opening/waiting belongs outside a model. No dummy
persistent writer may make framing/EOF untestable.

A FIFO is not a queue/database or authority. A wake-up means inspect durable state.
Multiple notifications must not cause repeated execution. A lost response after remote
report needs strategic review, not implementation replay. Bootstrap sent no real
notifications; all pipe tests use temp paths.

## OP-06. Coding runner and idle discipline

`~/codex-work/slaif-asset-reservation/oap/bin/launch-coding-agent.sh --repo ~/codex-work/slaif-asset-reservation --strategic-home ~/codex-supervision/slaif-asset-reservation
[--print-only] [--once]` discovers the configured Codex argv from the qualified private
profile and never shell-evals arbitrary strings. It sets cwd `~/codex-work/slaif-asset-reservation`, a separate
CODEX_HOME (`~/codex-supervision/slaif-asset-reservation/agent-homes/coding`), OAP_ROLE=CODING and the visible startup prompt
(`~/codex-work/slaif-asset-reservation/oap/prompts/coding-round.md`). The long-lived wrapper blocks on
`~/codex-supervision/slaif-asset-reservation/control.fifo`, consumes it exactly once, checks durable state, then launches one
fresh coding context for that round. If state lacks pending work it remains idle without
a model call. The model must NOT wait for control a second time. A crash resumes the same
ID/branch/PR after recovery.

Explicit quit (SIGINT/TERM or operator stop marker) exits the owned wrapper and leaves
the shell; no automatic resurrection, cron/systemd install or unrelated process
killing. Owner/PID/start-time lease identity prevents duplicate wrappers/readers, not
PID alone. Stale leases are reconciled with evidence, not blindly deleted. No
operational launch without activated authority.

## OP-07. Strategic runner

`~/codex-work/slaif-asset-reservation/oap/bin/launch-strategic-agent.sh --repo ~/codex-work/slaif-asset-reservation --strategic-home ~/codex-supervision/slaif-asset-reservation
[--print-only]` starts from `~/codex-supervision/slaif-asset-reservation` with the full installed constitution, private
strategy CODEX_HOME (`~/codex-supervision/slaif-asset-reservation/agent-homes/strategic`) and the visible STRATEGIC prompt
(`~/codex-work/slaif-asset-reservation/oap/prompts/strategic-start.md`). Use supported Codex interactive/session
behavior qualified at install time (recorded in `~/codex-supervision/slaif-asset-reservation/RUNTIME.md`). Strategy may wait
through a blocking response-FIFO helper; no periodic paid model calls. Logical
continuity persists even when a new incarnation reloads a handoff from
`~/codex-supervision/slaif-asset-reservation/workorders/STRATEGIC-HANDOFF.md`. Never invent flags for background resume,
model identifiers, context size, cost or an API endpoint. Missing qualified
configuration blocks operation, not setup.

## OP-08. Setup vs operational tmux

`~/codex-work/slaif-asset-reservation/oap/bin/launch-setup-tmux.sh [--print-only]`: create a NEW owned tmux session
(isolated socket) with two side-by-side panes: left strategy (cwd `~/codex-supervision/slaif-asset-reservation`), right
coding (cwd `~/codex-work/slaif-asset-reservation`). Shells only; permit deliberate human login/config; no
operational agents, active order or signal. It must work when model/auth/remote is
missing. Never repurpose another tmux session or inherit unrelated terminal state.

`~/codex-work/slaif-asset-reservation/oap/bin/launch-oap-tmux.sh [--print-only]`: same topology, but it first
requires the doctor operational gates, explicit activation scope/authority, accepted
governance/copy identities, source/projection integrity, qualified runtime/client/
remote, no conflicting active state/process and checked merge side effects. Only then
does it start role wrappers. Missing auth/model cannot silently select another
provider. Setup and operation are different modes; successful setup does not grant
operation permission.

## OP-09. PR-before-report sequence

1. Coding reconciles active order, branch/PR/remote and allowed existing changes.
2. Implements scoped work, tests, docs and the exact authorized DHA append.
3. Commits/pushes non-report work INCLUDING exact order/pointer bytes. Opens/amends the
   correct PR now.
4. Inspects in-scope CI failures, repairs and pushes implementation until ready to
   report truthfully.
5. Captures the literal full implementation head from the actual Git object format
   (SHA1 or SHA256).
6. Writes immutable `~/codex-work/slaif-asset-reservation/oap/reports/<ID>-<slug>.md`; commits ONLY that file,
   implementation head first parent.
7. Pushes the report commit; verifies remote PR/head/branch/report bytes/parent/
   report-only diff privately.
8. No further mutation/push for this round. Sends response OK, then exits.

Required literal report lines:
```
Implementation head SHA: <actual full ID>
Report publication commit: SELF
```
Report metadata: kind=report, id, order_path/hash, repo, issue_number, pr_number,
branch, implementation_head, result COMPLETE|PARTIAL|BLOCKED|FAILED,
observed_implementation_ci (runs/checks/status/observed_head),
report_head_ci="NOT YET OBSERVED AT AUTHORING" where applicable. Body: acceptance by
number, changed files, commands/exact results, privacy/dependency/DHA facts,
uncertainty/blockers, remaining limitations and next recommendation (not activation).
SELF resolves to the containing commit; no future CI/push success can be claimed
inside its own not-yet-published report.

## OP-10. Report verification and correction

`~/codex-work/slaif-asset-reservation/oap/bin/verify_report.py --repo ~/codex-work/slaif-asset-reservation --id ID --pr N --head H --remote
REMOTE [--json]` verifies actual object format, exact file/order digest, literal
implementation parent, report-only changed path, no new CRITICAL mutation in the
report commit, correct PR/branch/round, remote availability and exact remote head.
Missing remote evidence returns BLOCKED/PENDING, not a local pass. The shared fake
adapter has an identical read interface for tests and must never be selected silently
in operational mode.

If the report-only commit itself triggers a CI failure, coding cannot amend/rewrite
it or append extra implementation to that round. Strategy reviews and publishes the
next suffix on the same PR. Reports are indexes into evidence; a COMPLETE statement
is not acceptance. If initial PR publication is blocked, retain local implementation
evidence but do not fabricate a PR/report remote or emit OK.

## OP-11. Strategic acceptance and merge gate

Strategy independently checks all rounds, actual base-to-head scope, criteria,
code/tests/docs, source/project invariants, the strongest reason not to merge,
combined risk, pending D1 entries and D2 boundaries. Fetch current required checks
for the exact report head: quality/test/security/container plus any adopted OAP
checks and repository-required checks. Unknown/missing/skipped/cancelled/pending is
not success. Old green implementation CI does not cover a changed report head by
assumption.

Verify deployment side effects before enabling delegated merge and on relevant
workflow changes. If hooks/apps/config cannot be inspected, require attributable
operator evidence and keep merge activation blocked until resolved. Never alter
repository protection to proceed. Expected-head protected merge; a changed head
forces review again. Verify actual merged state afterward. Squash is used only if
approved for future development, preserving PR/ref/implementation-report ancestry
receipts. Past merges need not have used squash; preserve their actual two-parent
history.

Coding cannot merge or enable auto-merge. The manual migration-adoption PR remains
human-only. A strategic development merge means accepted for continued development -
not final milestone, production readiness, public exposure, real-data migration or
release.

## OP-12. CRITICAL payload bytes and append helper

The order's `## Exact CRITICAL payload` contains one fenced `text` block: UTF-8 LF
bytes between the opening LF and the closing fence, INCLUDING the final LF.
`Payload SHA-256:` records that exact byte sequence. Required entry headings/fields
are in `~/codex-work/slaif-asset-reservation/oap/templates/CRITICAL-ENTRY-TEMPLATE.md`. No placeholders or unknown
PR number in a real entry. The ordered prior register SHA-256 and byte length bind
history.

`~/codex-work/slaif-asset-reservation/oap/bin/append_critical.py --repo ~/codex-work/slaif-asset-reservation --order ORDER --kind
admission|evidence [--dry-run]` validates the active order, strategy-authorized exact
bytes, all-five attestation, unique ID, complete fields, actual PR, trusted prior
register prefix and owner lock. Admission accepts only the next monotonic CRIT ID; a
retry after crash succeeds as NO_OP only when the exact full payload already exists at
the authorized position. A duplicate differing entry, changed prefix or conflicting
concurrent append fails. Atomic replace preserves all prior bytes exactly. Never
regenerate the register from a parser.

Evidence/mitigation appends use the separate heading
`## EVIDENCE APPEND - CRIT-NNNN - <UUID>` and exact ordered bytes; they carry no human
disposition/status replacement and never clear the original judgment. The helper
refuses HUMAN ADJUDICATION content. Templates/fenced examples are ignored by the live
register parser. Private CRITICAL drafts are not entries. CRITICAL changes precede
the implementation head, never the final report-only commit.

## OP-13. Human recording and gate evaluation

A separate human recording procedure appends the exact
`~/codex-work/slaif-asset-reservation/oap/templates/HUMAN-ADJUDICATION-TEMPLATE.md` record. Values only
ACCEPTED/REJECTED/CHANGE REQUIRED/DEFERRED. The entry/scope/conditions/evidence are
bound to independently verified origin: for example an externally signed human
artifact or a GitHub comment/review from an explicitly approved human identity not
operated by agent credentials. Bootstrap produces trust-config examples
(`~/codex-work/slaif-asset-reservation/oap/governance/HUMAN-AUTHORITY.example.json`), not a populated allowlist or
proof. Default provenance=MISSING => gate blocked.

`~/codex-work/slaif-asset-reservation/oap/bin/check_state.py --check-human-gates TARGET` reads the latest
attributable disposition for each applicable entry. Unverified human-looking text or
a later non-ACCEPTED disposition blocks. Conditions requiring material work should
remain CHANGE REQUIRED/DEFERRED until satisfied, not auto-treated as acceptance.
Human scope acceptance does not substitute for separate release/deployment
authorization. Structural validation proves format only, not admission truth,
attribution or judgment correctness.

## OP-14. Recovery state machine

See `~/codex-work/slaif-asset-reservation/oap/RECOVERY.md` for the complete generated protocol. Observation ->
state / next permitted action: no pointer INACTIVE (wait externally, no model
invocation); empty/malformed pointer or nonunique order CORRUPT (preserve and stop);
durable order with old/missing pointer and identical unfinished journal PUBLISHING
(complete the identical transition only); control consumed with process death and no
report RUNNING_INTERRUPTED (same ID/branch/PR, finish unfinished scope); first a
already has a PR RESUME (bind the verified PR, never a second); local report commit
with remote unverified REPORT_LOCAL (verify/push unchanged, no new implementation);
remote report with lost response REPORT_PUBLISHED (strategy review, no rerun);
duplicate wake-up reconcile and suppress if running/published/accepted; CI pending
REVIEW_PENDING (wait outside the model, no make-work suffix); accepted merged PR with
pointer remaining ACCEPTED/QUIESCENT (not an executable active task); replacement
client/context/host restore logical role/state (no new objective/suffix); human quit
STOPPED (no resurrection until explicit restart).

Recovery checks remote before trusting local metadata. Reports and
incorrect-interpretation history are preserved; append/supersede notes, never erase.
Cleanup touches only owned resource IDs/paths - never a foreign tmux session,
container, DB or lock. Quiescent accepted governance refresh backs up known installed
copies, preserves private state and refuses conflicts.

## OP-15. Helper interfaces and responsibilities

All helpers support `--help` and bounded, redacted failures; write helpers support a
real no-write dry-run or `--print-only`. Shared stdlib code
(`~/codex-work/slaif-asset-reservation/oap/bin/oaplib.py`) implements IDs, paths, schemas, hashes, locks and the
remote adapter once. No redundant daemons/databases/dependency platform.

| Helper | Contract for this installation |
|---|---|
| `oap/bin/bootstrap-two-agent-oap.sh` | inspect/plan/apply/refresh the owned file manifest; default dry-run; no activation/publication |
| `oap/bin/doctor.sh` | separate structural/setup/operational/adoption readiness; missing credentials do not prevent shells |
| `oap/bin/check_governance.py` | source/projection/installed-copy identities, accepted-vs-candidate diff scope, clause and context coverage |
| `oap/bin/check_state.py` | ID/pointer/order/report/PR/remote/recovery/gates; no mutation by default |
| `oap/bin/publish_order.py` | OP03-OP04 final validation; immutable order, then pointer, then signal |
| `oap/bin/append_critical.py` | OP12 exact locked append; no adjudication |
| `oap/bin/verify_report.py` | OP09-OP10 parent/report-only/SELF/remote identity |
| `oap/bin/oap_fifo.py` | OP05 exact framing, partial I/O, single consumer, timeouts |
| `oap/bin/check_ica.py` | required matrix/target/revision/independence evidence fields; no semantic certification |
| `oap/bin/launch-coding-agent.sh` | OP06 fresh round, no idle model polling |
| `oap/bin/launch-strategic-agent.sh` | OP07 logical continuity, full-role home |
| `oap/bin/launch-setup-tmux.sh` | OP08 two side-by-side setup shells before credentials |
| `oap/bin/launch-oap-tmux.sh` | OP08 gated operation; explicit quit; duplicate-process refusal |

Fixture injection only through an explicit test-mode adapter at isolated fixture
roots; the production doctor rejects TEST authority/remote/client adapters. No helper
may silently call a real model or product endpoint during bootstrap.

## OP-16. Private configuration is data, not executable authority

Parse `~/codex-supervision/slaif-asset-reservation/runtime.env` with the strict allowlisted data parser in oaplib - never
shell source/eval. Reject duplicate keys, interpolation/command substitution and
invalid booleans/paths/argv JSON. Render exact argv arrays without shell
concatenation. Missing model/auth/authority remains explicit. Private configuration
never contains copied credentials, and flipping an activation boolean cannot
establish human origin. The externally attributable authority reference stays
separate from local reconstructable state.

Home-relative path data is expanded by the shared helper before filesystem/client use.
Only ~ and ~/ are supported; foreign-user expansion, parent traversal and absolute
subpaths are refused. Absolute paths remain supported. CLI cwd-relative file arguments
remain relative to cwd. No shell sourcing/interpolation is introduced.
