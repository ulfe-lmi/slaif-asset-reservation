# Coding communication — compact protocol

CP-01. Durable truth: actual Git/PR/CI > report claims; versioned order/pointer/report select work;
private receipts reconstruct; FIFO only wakes. Retain CODING role. No merge, auto-merge, self-approval,
DHA adjudication, roadmap selection or bootstrap activation. Check accepted governance/source hashes.

CP-02. Active=`ID+LF` exactly; absent=inactive, malformed/empty/nonunique=refuse. ID NNN-a…z,aa…zz;
restart never renumbers. Use exact order; never newest filename. a uses CREATE_OR_RESUME; later
suffix AMEND same objective issue/branch/PR. If a already opened PR, reuse. New objective only after
strategy verified merge/acceptance or explicit abandonment with dependencies reassessed.

CP-03. Wrapper consumed control OK before invocation; do not consume again. Read root router ->
coding law -> compact architecture -> this -> exact order -> compact security/testing -> only scoped
excerpts. Inspect current remote/base/branch/PR before edit; preserve unrelated local changes. Only
order-authorized files including exact order/pointer are permitted. Scope mismatch -> report, no
reset/stash/clean/force. Full protocol is a strategy source; ask bounded clarification on genuine gap.

CP-04. Final order includes actual base/governance identities, concrete H/A/E/I/C source, criteria,
negative tests, allowed paths, forbidden resources, PR mode and exactly one DHA declaration.
`## Deferred human adjudication` then `- Decision: NONE` is normal. APPEND CRIT-NNNN requires exact
full strategic payload between fenced text delimiters (UTF-8 LF including final LF), SHA-256 and
trusted register prefix; use append helper before implementation commit. Never create an entry or
human disposition yourself. Candidate concern goes to strategy. Ordinary bugs/tests/setup are D0.

CP-05. Implementation: perform order/tests/docs/authorized DHA; commit+push all non-report work;
create/amend actual PR BEFORE final report; repair safe in-scope CI failure; record full actual
implementation head. Then write immutable oap/reports/<ID>-<slug>.md, containing literal
`Implementation head SHA: <full ID>` and `Report publication commit: SELF`.
Final commit has implementation head as first parent and changes ONLY matching report file.
No other file (including CRITICAL) may change in that report-only commit.

CP-06. Report per OP09 metadata plus numbered acceptance evidence, paths/commands/results, uncertainty,
privacy/dependencies/DHA/limits. Results COMPLETE/PARTIAL/BLOCKED/FAILED. Implementation CI observed
at authoring is separate from report-head CI; no future push/check success claimed. SELF resolves
to containing commit, not a hash invented before commit exists.

CP-07. Push final report and verify actual remote PR/head/report bytes/parent/path with verifier.
Post-publication observations go to private execution receipt, never rewrite report. No further
mutation/push in this round. Send exactly ASCII OK bytes4f4b, no LF/ID/JSON, using response FIFO
helper; close descriptor; exit. Publication failure => no completion signal, preserve recovery state.
Published PARTIAL/BLOCKED/FAILED may notify honestly. Report-head failure => next strategy suffix,
not amendment of old immutable report. Coding never claims its report is strategically accepted.

CP-08. Lost control/process: same ID/branch/PR resume unfinished work. Local-only report: finish/verify
publication unchanged. Remote report/lost response: strategic review, no implementation replay.
Duplicate wake-up checks durable state; accepted PR with old pointer is quiescent. CI pending means
wait outside model, not new feature. Explicit quit stops owned wrapper; no automatic resurrection.

CP-09. Use check_state/verify_report/oap_fifo/append_critical with qualified paths; all private homes/
FIFOs/logs mode0600/0700 as appropriate. No credentials or private artifacts in report/transcript.
No product/lab/real export/model call in bootstrap tests. No unqualified provider/CLI fallback.
Report exact PASSED/FAILED/SKIPPED/NOT RUN/BLOCKED/PENDING/MISSING; only actual success passes.
