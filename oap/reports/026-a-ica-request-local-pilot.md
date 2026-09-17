<!-- OAP-META
{
 "kind": "report",
 "id": "026-a",
 "order_path": "oap/orders/026-a-ica-request-local-pilot.md",
 "order_sha256": "deb829deedbc647be9847e27e50b5ef03f261d9c13fdc3f8f46af4d040a84e9c",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 51,
 "pr_number": 52,
 "branch": "codex/51-oap-026-a-ica-request-local-pilot",
 "implementation_head": "fad04893eaaf16ee11ac9b6bac4660fe3e49c37e",
 "base_sha": "21f6204d5f03c304991d4cd5c45a74aecdcb686a",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "fad04893eaaf16ee11ac9b6bac4660fe3e49c37e",
  "runs": [
   {"run_id": 35183802047, "workflow": "CI", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 35183802004, "workflow": "oap", "event": "pull_request", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 026-a report — Materialize the M-LOCAL-PILOT-EVIDENCE ICA request at merged main 21f6204

Order digest: `deb829deedbc647be9847e27e50b5ef03f261d9c13fdc3f8f46af4d040a84e9c`
(committed `oap/orders/026-a-ica-request-local-pilot.md`; the materialized
`.FINAL` source was moved to the canonical name with `mv` before committing,
byte-identical, as in every prior round; `sha256sum` of both names:
`deb829deedbc647be9847e27e50b5ef03f261d9c13fdc3f8f46af4d040a84e9c`).

Implementation head SHA: fad04893eaaf16ee11ac9b6bac4660fe3e49c37e

Report publication commit: SELF

**Result: COMPLETE** — all eight numbered acceptance criteria met. The round
produces exactly one new file (the materialized ICA request), deletes the
superseded pre-target draft, and publishes the round bytes; no product, test,
workflow, dependency or other documentation byte changed. No ICA activity was
performed: no audit execution, no classifications beyond the ordered UNPROVEN
skeleton, no findings, no auditor identity, no milestone claims.

## 1. Starting state and E-list reconciliation (verify, do not assume)

Ordered reads completed: root router → `oap/coding-instructions/AGENTS.md` →
`ARCHITECTURE-for-agents.md` → `OAP-COMMUNICATION-coding-agent.md` → exact
active order → `SECURITY-CORE.md`/`TESTING-CORE.md` → the order's additional
read set (`docs/audit/ICA-PROTOCOL.md` in full,
`docs/audit/ICA-REQUEST-TEMPLATE.md` in full,
`docs/audit/requests/local-pilot.DRAFT.md` in full, `ARCHITECTURE.md` A-03 +
the SAR index header and all 38 rows' Source/Inspect/Evidence lines,
`PLAN.md` P-03/P-04, `docs/security-model.md` section 6, `INSTALL.md`
section 12, `oap/bin/check_ica.py` in full).

`oap/active` held exactly `026-a` + LF (verified by hexdump:
`3032 362d 610a`); the materialized order source
`oap/orders/026-a-ica-request-local-pilot.FINAL.md` was untracked in the
worktree (published by strategy before invocation). Every E-list value was
re-verified live on 2026-09-17; none differed, so the order's STOP condition
did not trigger:

| E-list value | ordered | live verification | match |
|---|---|---|---|
| main (local) | 21f6204d5f03c304991d4cd5c45a74aecdcb686a | `git rev-parse main` | ✓ |
| main (remote) | 21f6204d5f03c304991d4cd5c45a74aecdcb686a | `git ls-remote origin refs/heads/main` | ✓ |
| OAP state at base | INACTIVE, pointer ABSENT | `git ls-tree 21f6204 -- oap/active oap/orders/026-a-...FINAL.md` → 0 entries | ✓ |
| CI at merge 979882e3ed318b0a90f35bd3a99fca0161edb782 | all runs success, head_sha verified | check-runs API: security/quality/oap-harness/test/container all completed+success, head_sha = 979882e… per run | ✓ |
| CI at quiesce 21f6204 | all runs success, head_sha verified | check-runs API: deployment-rehearsal/container/quality/test/oap-harness/security all completed+success, head_sha = 21f6204… per run | ✓ |
| Gate-time rehearsal dispatch | run 35182574499 (deployment-rehearsal, head 21f6204) — NOT this order's scope | actions API: run 35182574499, workflow deployment-rehearsal, head 21f6204…, created 2026-09-17T04:36:47Z, conclusion success | ✓ (recorded for completeness only) |
| ARCHITECTURE.md SHA-256 at main | 182d9cf924931e846bc7965a079482b6753de762af807196ca0b87f8dffdf863 | `sha256sum` on clean main worktree | ✓ |
| PLAN.md SHA-256 at main | d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06 | `sha256sum` on clean main worktree | ✓ |
| SAR index | SAR-001 through SAR-038, each row with Source/Inspect/Evidence | programmatic parse of live ARCHITECTURE.md A-14: 38 rows, SAR-001…SAR-038 in order, every row carries all three lines | ✓ |
| Template/draft/protocol presence | ICA-REQUEST-TEMPLATE.md; DRAFT 18 lines with historical wording "Future drafts016–020" and "419-test report"; ICA-PROTOCOL.md; check_ica.py structural checks | all present; `wc -l` = 18; both historical wording strings found by grep; protocol and validator read in full | ✓ |
| Fresh round | no local/remote branch `codex/51-oap-026-a-ica-request-local-pilot`, no PR for issue #51 | `git branch --list 'codex/51-*'` empty; `git ls-remote origin 'refs/heads/codex/51-oap-026-a*'` empty; `gh pr list --state open` = []; issue #51 OPEN ("026-a: materialize M-LOCAL-PILOT-EVIDENCE ICA request at merged main 21f6204 (bounded)") | ✓ → pr_mode resolved to CREATE |

Worktree on main was clean apart from the two untracked round bytes listed
above. No other local modifications existed; nothing was reset/stashed/
cleaned.

## 2. Acceptance evidence (one row per ordered criterion)

**Criterion 1 — request file with every ordered field: PASSED.**
`docs/audit/requests/local-pilot.md` (new, 178 lines,
`sha256sum 1d047d57af32fea9610f4be102cd69ad23ba09d7d465f97763ebb167a484134c`
at the implementation head) contains, in order:
- Status line: "REQUEST (not an audit result)", materialized 2026-09-17 at
  merged main, structural validation via `oap/bin/check_ica.py --kind
  request`;
- Milestone: M-LOCAL-PILOT-EVIDENCE (first controlled internal-alpha Docker
  deployment target; per ICA-PROTOCOL.md includes all applicable product
  boundaries);
- Human scope/provenance: the 2026-09-17 in-session human instruction quoted
  (objective sentence + verbatim exclusions sentence), attributed to the
  in-session human principal, with the note that human milestone acceptance
  and release/deployment authority remain separate from ICA;
- Repository: ulfe-lmi/slaif-asset-reservation;
- line `Merged product revision: 21f6204d5f03c304991d4cd5c45a74aecdcb686a`
  (line-start anchored, full 40-hex);
- Canonical PLAN/ARCHITECTURE revisions and hashes: both at the merged
  revision, with the two 64-hex digests above (re-verified live this round,
  section 1);
- the complete 38-row SAR matrix (programmatic cross-check below);
- the separate deferral section with authority per item (7 items,
  section 3 note);
- Auditor/context identity: PENDING (unfilled; fresh isolated context to be
  spawned by strategy after merge; concrete identity recorded in the audit
  report);
- the independence statement (fresh isolated context; no prior involvement;
  bounded inputs; read-only mandate; same model family recorded honestly;
  structural validation cannot prove independence; human retains final
  milestone acceptance);
- the audit-method paragraph per ICA-PROTOCOL.md (input order; evidence
  indexes not proof; classify every applicable row; named negative paths;
  findings with provenance and strongest reason not to fix now; rerun on the
  new exact revision after remediation; unresolved DHA/D2 gates explicit);
- the deliverable line (docs/audit/reports/
  M-LOCAL-PILOT-EVIDENCE-<revision-prefix>.md, written by the audit context,
  not this round);
- the structural-only disclaimer and NO pre-filled "Result: PASS" or
  equivalent (negative grep: no line-start `Result:\s*PASS` anywhere in the
  file).

Programmatic cross-check at the implementation head (scripted, live
`ARCHITECTURE.md` A-14 parsed, request table parsed): **all 38 rows match the
live index verbatim** (title + Inspect + Evidence transcribed byte-for-byte,
every row UNPROVEN, every row carrying a named negative path of 20+
characters); 38/38 table rows; no row required a "missing field" recording
(every live index row carries both an Inspect and an Evidence line).

**Criterion 2 — DRAFT deleted, deletion recorded: PASSED.**
`docs/audit/requests/local-pilot.DRAFT.md` deleted in the implementation
commit (`git diff --name-status` shows `D`). Reason, recorded here as
ordered: it is a stale pre-target draft (18 lines; "DRAFT UNTIL HUMAN TARGET
SELECTION"; historical wording "Future drafts016–020" and "419-test
report"), superseded by this round's materialized request, and is not an
immutable historical snapshot (the order's scope section designates it as
superseded). The pre-deletion bytes were inspected in full and quoted in the
reconciliation above.

**Criterion 3 — structural validation at the implementation head: PASSED.**
Command:
`python3 oap/bin/check_ica.py --repo . --file docs/audit/requests/local-pilot.md --kind request`
(re-run at the implementation head with a clean worktree). Literal output:

```
result=PASS-STRUCTURAL-ONLY
  [ok] human_scope
  [ok] architecture_hash
  [ok] architecture_hash_current
  [ok] exact_revision
  [ok] requirement_matrix_present
  [ok] classifications_present
  [ok] auditor_provenance
  [ok] negative_paths
  [ok] no_prefilled_success
  [ok] structural_only_disclaimer
```
exit code 0. (The same command produced identical output before the commit;
the file is byte-identical between the two runs, digest above.)

**Criterion 4 — diff touches only the ordered paths: PASSED.**
`git diff --name-status 21f6204d5f03c304991d4cd5c45a74aecdcb686a..
fad04893eaaf16ee11ac9b6bac4660fe3e49c37e` (full IDs):

```
D	docs/audit/requests/local-pilot.DRAFT.md
A	docs/audit/requests/local-pilot.md
A	oap/active
A	oap/orders/026-a-ica-request-local-pilot.md
```

Nothing else — no ARCHITECTURE.md, PLAN.md, INSTALL.md, security-model.md,
product, test, workflow or other doc change. `git diff --stat`: 4 files
changed, 441 insertions(+), 18 deletions(-) (the 18 deletions are exactly the
deleted DRAFT). Digest re-verification at the implementation head (must be
unchanged vs the E list): ARCHITECTURE.md `182d9cf924931e846bc7965a079482b6753
de762af807196ca0b87f8dffdf863` ✓, PLAN.md `d03eb29713cfbdb7e227413618396e6bb2
a7a08749225979c3055dacfd461d06` ✓. The GitHub PR file listing for PR #52
independently shows exactly these four paths.

**Criterion 5 — CI at the exact implementation head: PASSED** (all five
green; the oap-harness flake escape clause was not needed).
head_sha verified per check run from the GitHub API (check-runs for commit
`fad04893eaaf16ee11ac9b6bac4660fe3e49c37e`):
- run **35183802047** (CI, pull_request, PR #52, created 2026-09-17T04:56:22Z,
  head_sha fad0489…): quality success (04:56:24→04:57:17Z), test success
  (04:56:24→04:59:20Z), security success (04:56:25→04:56:40Z), container
  success (04:56:25→04:57:00Z) — all four standard jobs GREEN;
- run **35183802004** (oap, pull_request, head_sha fad0489…): oap-harness
  success (04:56:24→04:57:03Z).
No missing/skipped/cancelled job; no failure; no rerun required.

**Criterion 6 — PR description: PASSED.**
PR **#52** (GitHub-assigned; recorded truthfully) opened against `main` from
`codex/51-oap-026-a-ica-request-local-pilot`, state OPEN, MERGEABLE at
authoring, head fad0489…. The description contains all ordered elements:
what was materialized and why (human target fixed 2026-09-17; 025 merged at
21f6204; ICA mandatory per S-23/SAR-038; audit NOT performed in this PR);
the exact values bound (merged revision + both 64-hex digests); the 38-row
matrix summary (verbatim materialization from the live SAR index, every row
UNPROVEN + enforcing source + evidence index + named negative path); the
deferral list with authorities (7 items); the next step (strategy spawns the
isolated audit context after merge and files the report; remediation rounds
per protocol if in-target defects are found, then a fresh rerun); and
truthful status language (CI-green candidate; real deployment not yet
evidenced; no deployment performed; deployment remains human-authorized; a
development merge is not release/deployment/milestone acceptance per
SAR-038).

**Criterion 7 — report-only commit with the implementation head as first
parent: in construction here.**
This file is the only change in the final commit, whose first parent is the
implementation head `fad04893eaaf16ee11ac9b6bac4660fe3e49c37e` (verified on
publication; see section 8). It contains the diff proof (criterion 4), the
check_ica.py literal output (criterion 3), the digest re-verification
(sections 1 and 4), the deletion record (criterion 2) and the honest
implementation-head vs report-head CI separation (section 6).

**Criterion 8 — DHA outcome: NONE (section 5).**

## 3. Deferrals materialized (scope note)

The order's E section enumerates the approved deferrals with authority; all
enumerated groups were materialized in the request's separate deferral
section, each recorded out-of-target with its authority and the note that a
deferral is not a pass: (1) institutional OIDC / password reset / email
workflow — SAR-036, roadmap deferred, INSTALL.md §12; (2) projects /
memberships / resource restrictions — SAR-036, broad authenticated-human
authorization is the current model (security-model §6), acceptable only under
a constrained trusted pilot, exposure boundary an explicit human-gate input;
(3) execution gateway / automatic physical allocation — SAR-036 (separate
future trust boundary per SAR-002); (4) notification system — SAR-036,
INSTALL.md §12; (5) monitoring stack — SAR-036 (Phase 4), INSTALL.md §12;
(6) SmartScheduling production cutover — SAR-030 scope, INSTALL.md §12;
(7) database role separation + backup hardening — security-model §6 ("Remain
operational work"), exposure-scope dependent, human-gate input.
Ordering note (D0, no scope impact): the order's scope section says "the six
groups listed in the E section" while the E section — and the scope section's
own parenthetical — enumerate seven; the enumerated list is authoritative and
all seven were materialized.

## 4. Changed files and scope

Implementation commit `fad04893eaaf16ee11ac9b6bac4660fe3e49c37e` ("026-a:
materialize M-LOCAL-PILOT-EVIDENCE ICA request at merged main 21f6204") vs
base `21f6204d5f03c304991d4cd5c45a74aecdcb686a`:
- `docs/audit/requests/local-pilot.md` (A — the materialized request, digest
  `1d047d57af32fea9610f4be102cd69ad23ba09d7d465f97763ebb167a484134c`);
- `docs/audit/requests/local-pilot.DRAFT.md` (D — superseded pre-target
  draft, 18 lines);
- `oap/orders/026-a-ica-request-local-pilot.md` (A — materialized order
  source, byte-identical rename of the `.FINAL` file; committed blob digest
  verified via `git show HEAD:oap/orders/026-a-ica-request-local-pilot.md |
  sha256sum` = `deb829deedbc647be9847e27e50b5ef03f261d9c13fdc3f8f46af4d040a84e9c`);
- `oap/active` (A — exactly `026-a` + LF, hexdump-verified
  `3032 362d 610a`).
No other file (including CRITICAL.md) changed in any round commit.

## 5. DHA outcome

- Decision: NONE. No `CRITICAL.md` entry was appended or altered; no human
  disposition, gate clearance or milestone judgment was performed. The order
  declares exactly `Decision: NONE`; nothing here contradicts that.

## 6. CI observed before authoring

Observed at the exact implementation head `fad04893eaaf16ee11ac9b6bac4660fe3
e49c37e` (section 2, criterion 5): run 35183802047 (CI) — quality/test/
security/container all success; run 35183802004 (oap) — oap-harness success;
head_sha verified per check run from the API. **Report-head CI: NOT YET
OBSERVED AT AUTHORING** — this report commit becomes the new PR head, and its
checks had not run (and are not claimed) at authoring. Later publication
verification goes to the private execution receipt, not to a report rewrite.

## 7. Commands and results (summary)

- `python3 oap/bin/check_ica.py --repo . --file docs/audit/requests/local-
  pilot.md --kind request` → `result=PASS-STRUCTURAL-ONLY`, 10/10 checks ok,
  exit 0 (criterion 3; literal output above).
- `sha256sum ARCHITECTURE.md PLAN.md` at base and at the implementation head
  → `182d9cf9…` / `d03eb297…` unchanged (criteria 1/4).
- `sha256sum` of the `.FINAL` source and the renamed committed order file →
  identical `deb829de…` (round bytes).
- Scripted live-index cross-check (38 rows parsed from `ARCHITECTURE.md`
  A-14; 38 table rows parsed from the request; title/Inspect/Evidence
  compared verbatim) → 38/38 match, zero problems; negative-path length
  check 38/38 passed; line-start `Result:\s*PASS` search → no match;
  `Auditor/context identity:\s*PENDING` → present;
  `^Merged product revision: (\S+)$` → `21f6204d5f03c304991d4cd5c45a74aecdcb
  686a` (criterion 1).
- `git diff --name-status/--stat` base..implementation head → exactly the
  four ordered paths (criterion 4).
- GitHub API (check-runs/actions runs/PR view) for reconciliation and CI
  (sections 1, 2, 6).
No test suite execution was ordered or required (documentation-only round;
no product bytes changed). Nothing FAILED/SKIPPED/BLOCKED; no NOT RUN
product tests relevant to this order.

## 8. Publication procedure (before the exact response signal)

Before the exact ASCII OK response: push this report-only commit and verify
the actual remote identity with the verifier — PR #52 head advanced to this
publication commit; the publication commit's first parent is
fad04893eaaf16ee11ac9b6bac4660fe3e49c37e; its diff versus the first parent
changes ONLY `oap/reports/026-a-ica-request-local-pilot.md`; the remote
report blob matches the local file bytes (contents API digest); PR #52
remains OPEN with the four-path implementation diff plus this report path.
This report never asserts its own future publication facts; later
publication observations go to the private execution receipt, not to a
report rewrite.

## Security, data, dependencies and local tools

No secrets, verifiers, peppers, credentials, cookies, CSRF values or private
data entered Git, this report, the PR description or logs; no auth-home
copying; no OS sidecars. No deployment of any kind; no DNS/TLS/firewall/host
changes; no production/lab/Neumann contact; no real exports, real secrets or
paid inference. No dependency changes (uv.lock untouched); no product code,
migration, workflow or test byte touched. Local tools: git, python3 (stdlib
+ repo `oap/bin/check_ica.py`), gh CLI (read APIs + the ordered publication
operations only: one branch push, one PR creation). The response FIFO helper
(`oap/bin/oap_fifo.py send`) is used only for the exact ASCII OK completion
signal after verified remote publication.

## Limitations and recommendation to strategy

- This round materializes the request only; it proves nothing about target
  readiness. The structural validator's PASS is structural-only (it cannot
  prove independence, correctness or closure). All 38 SAR rows remain
  UNPROVEN until the independent audit context substantiates them.
- The audit itself is the next step and is NOT performed here: after merge,
  strategy spawns the fresh isolated audit context bound to this exact merged
  revision and files the report at docs/audit/reports/
  M-LOCAL-PILOT-EVIDENCE-<revision-prefix>.md. If the audit finds in-target
  defects, remediation rounds follow per protocol, then a fresh
  architecture-to-current-main rerun on the new exact revision.
- Real deployment remains human-authorized and unevidenced; this PR's merge
  is a development merge only (SAR-038). Recommendation to strategy: after
  exact-head review and delegated merge of PR #52, quiesce the active
  pointer, then dispatch the ICA context per ICA-PROTOCOL.md. No merge,
  release or self-certification is claimed or requested by coding.

## Deferred human adjudication

- Decision: NONE
