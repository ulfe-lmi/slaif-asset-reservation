<!-- OAP-META
{
 "kind": "report",
 "id": "028-a",
 "order_path": "oap/orders/028-a-doc-truth-post-027.md",
 "order_sha256": "09d0182c506e4dd44a0613d4269634990d05b9d29a5ab94fc85bb8b53ea8a10d",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 55,
 "pr_number": 56,
 "branch": "codex/55-oap-028-a-doc-truth-post-027",
 "implementation_head": "dd7801ff0b2dacce1a30d75d27be0ccca13cfc20",
 "base_sha": "cb2045c51099dbc2878173e18ae5550d10793170",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "dd7801ff0b2dacce1a30d75d27be0ccca13cfc20",
  "runs": [
   {"run_id": 35191552886, "workflow": "CI", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 35191552897, "workflow": "oap", "event": "pull_request", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 028-a report — Correct post-027 documentation drift (three lines, two files)

Order digest: `09d0182c506e4dd44a0613d4269634990d05b9d29a5ab94fc85bb8b53ea8a10d`
(committed `oap/orders/028-a-doc-truth-post-027.md`; the strategy-published
`.FINAL` source `oap/orders/028-a-doc-truth-post-027.FINAL.md` was moved to the
allowed in-repo name with `mv` before committing, byte-identical, as in prior
rounds; `sha256sum` of both names:
`09d0182c506e4dd44a0613d4269634990d05b9d29a5ab94fc85bb8b53ea8a10d`).
Active pointer `oap/active` = `028-a` + LF (verified by hexdump:
`3032 382d 610a`, 6 bytes; `sha256sum`:
`6cc007b11af7e198b8794af1ac27e890a0be13b2a85457d9dfe7ebb2c29837a3`).

Implementation head SHA: dd7801ff0b2dacce1a30d75d27be0ccca13cfc20

Report publication commit: SELF

**Result: COMPLETE** — all eight numbered acceptance criteria met. The round
changes exactly three current-state doc lines (one in `README.md`, two in
`docs/roadmap.md`) and publishes the round bytes (order + active pointer); no
product, test, workflow, ICA-artifact, historical-doc, or other doc byte
changed. No ICA activity was performed: no audit execution, no classifications,
no re-audit, no new audit request. This is a development merge candidate only;
a real deployment has not yet been evidenced, none is approved, and deployment
remains human-authorized.

## 1. Starting state and E-list reconciliation (verify, do not assume)

Ordered reads completed: root router → `oap/coding-instructions/AGENTS.md` →
`ARCHITECTURE-for-agents.md` → `OAP-COMMUNICATION-coding-agent.md` → exact
active order (pointer `oap/active` = `028-a` + LF →
`oap/orders/028-a-doc-truth-post-027.FINAL.md`) → `SECURITY-CORE.md` /
`TESTING-CORE.md` → the order's additional read set: `README.md` (Status
section), `docs/roadmap.md` (WO 0014 section + Next-roadmap-item section),
`docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md` (result statement only),
and `ls oap/orders/` (existence check).

Base verification (order STOP condition): `git rev-parse main` =
`cb2045c51099dbc2878173e18ae5550d10793170`;
`git ls-remote origin refs/heads/main` =
`cb2045c51099dbc2878173e18ae5550d10793170`. Equal to the order's `base_sha`;
no STOP.

Fresh-round verification: no local or remote branch
`codex/55-oap-028-a-doc-truth-post-027` existed (`git branch -a --list '*028*'`:
empty; `git ls-remote origin '*028*'`: empty); no PR for issue #55
(`gh pr list --head codex/55-oap-028-a-doc-truth-post-027 --state all`:
`[]`; issue #55 itself exists and is OPEN, titled "028-a: correct post-027
documentation drift (README + roadmap current-state lines) (bounded)"). pr_mode
CREATE_OR_RESUME therefore resolved to CREATE. GitHub-assigned PR number:
**56** (recorded truthfully).

E-list values re-verified live at base before editing; none differed:
- `README.md` line 12 contained "015-a through 024-a".
- `docs/roadmap.md` line 190 contained "015-a through 024-a".
- `docs/roadmap.md` lines 209–214 contained the stale "Current human selection
  (2026-09-17): objective 024-a (the canonical installation/deployment
  documentation cleanup) is complete; ..." paragraph.
- `oap/orders/` contained order files for 015-a through 027-a (plus this
  round's 028-a bytes, see criterion 2).
- ICA report result statement (line 371ff of
  `docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md`): at exact merged
  product revision 21f6204, "37/38 rows as IMPLEMENTED and 1 row (SAR-037) as
  PARTIAL ... No ABSENT or UNPROVEN rows. No in-target blockers ..."; matches
  the counts the new paragraph must carry (37 IMPLEMENTED / 1 PARTIAL / 0
  ABSENT / 0 UNPROVEN).

## 2. Acceptance evidence (numbered per order)

1. **Diff scope — PASSED.** `git diff --name-status
   cb2045c51099dbc2878173e18ae5550d10793170..dd7801ff0b2dacce1a30d75d27be0ccca13cfc20`:
   ```
   M	README.md
   M	docs/roadmap.md
   A	oap/active
   A	oap/orders/028-a-doc-truth-post-027.md
   ```
   Only the two allowed doc files plus the round bytes. `git diff -U0` over the
   two doc files shows exactly one changed line in `README.md` (line 12) and
   exactly two changed hunks in `docs/roadmap.md` (the line-190 single line and
   the Next-roadmap-item paragraph at lines 209–214 → 209–223):
   ```
   @@ -12 +12 @@ (README.md)
   -  the one-time adoption was merged by the human, and OAP objectives 015-a through 024-a
   +  the one-time adoption was merged by the human, and OAP objectives 015-a through 027-a
   @@ -190 +190 @@ (docs/roadmap.md)
   -operational, and objectives 015-a through 024-a have been implemented on `main` (see `oap/orders/`).
   +operational, and objectives 015-a through 027-a have been implemented on `main` (see `oap/orders/`).
   @@ -209,6 +209,15 @@ (docs/roadmap.md, "Next roadmap item" paragraph only)
   -Current human selection (2026-09-17): objective 024-a (the canonical
   -installation/deployment documentation cleanup) is complete; the current
   -selection is deployment qualification for the first controlled internal-alpha
   -Docker deployment (objective 025-a and the independent closure audit that
   -follows), then the first real internal-alpha deployment, human-authorized and
   -performed per `INSTALL.md`. The slice after that remains human-selected.
   +Current human selection (2026-09-17): deployment qualification for the first
   +controlled internal-alpha Docker deployment. Completed since that selection:
   +024-a (canonical installation/deployment documentation), 025-a/b/c
   +(deployment-qualification docs, image reproducibility, and the post-merge
   +full-rehearsal CI workflow), 026-a (materialized M-LOCAL-PILOT-EVIDENCE ICA
   +request at merged main 21f6204), and 027-a (ICA findings F-001/F-002
   +doc-drift fix). The Independent Closure Audit was executed 2026-09-17 in a
   +fresh isolated context at product revision 21f6204 (report:
   +`docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md`; 37 IMPLEMENTED / 1
   +PARTIAL / 0 ABSENT / 0 UNPROVEN; no in-target blockers; the single PARTIAL
   +row's drift was corrected by 027-a, with the protocol re-audit scheduled at
   +the next milestone-closure attempt). The next slice is the first real
   +internal-alpha deployment, human-authorized and performed per `INSTALL.md`
   +(deployment-gate brief presented 2026-09-17; a real deployment has not yet
   +been evidenced). The slice after that remains human-selected.
   ```

2. **Both "015-a through 027-a" claims verified true — PASSED.** Scripted check
   (command + literal listing; run at implementation-head worktree).
   `ls oap/orders/` at check time (before the `mv` of the FINAL source, which
   left the canonical name in place):
   ```
   015-a-simplify-canary.md
   015-b-simplify-canary.md
   016-a-security-pip-audit.md
   017-a-restore-drill.md
   018-a-rehearsal-ownership.md
   019-a-readiness-boundaries.md
   020-a-booking-maintenance-races.md
   021-a-integrated-pilot-path.md
   022-a-legacy-import-concurrency.md
   023-a-fifo-write-flake-fix.md
   024-a-canonical-install-deployment-docs.md
   025-a-deployment-qualification.md
   025-b-rehearsal-ci-gate-fix.md
   025-c-separate-rehearsal-workflow.md
   026-a-ica-request-local-pilot.md
   027-a-ica-finding-doc-drift-fix.md
   028-a-doc-truth-post-027.FINAL.md
   028-a-doc-truth-post-027.md
   ```
   Script: for each of the 15 IDs (015-a, 016-a, 017-a, 018-a, 019-a, 020-a,
   021-a, 022-a, 023-a, 024-a, 025-a, 025-b, 025-c, 026-a, 027-a) assert exactly
   one canonical order file `NNN-*-slug.md` exists:
   ```
   missing: [] | FINAL-suffixed present: ['028-a-doc-truth-post-027.FINAL.md']
   15 canonical IDs present: True
   ```
   All 15 canonical IDs present (the 16th ID 028-a is this round's own order
   bytes, committed under its canonical name). After the documented `mv` of the
   FINAL source to the in-repo name, `ls oap/orders/` lists 17 files
   (015-a … 028-a, no `.FINAL` remainder) and
   `sha256sum oap/orders/028-a-doc-truth-post-027.md` =
   `09d0182c506e4dd44a0613d4269634990d05b9d29a5ab94fc85bb8b53ea8a10d`
   (identical under both names).

3. **New Next-roadmap-item paragraph — PASSED.** The paragraph now occupies
   `docs/roadmap.md` lines 209–223. Word-exactness: a Python check joining the
   15 wrapped lines and comparing to the order's exact replacement text (single
   spaces normalized) printed `WORD-EXACT: True` (re-wrapping only; wording
   matches). Positive fragment checks on the joined paragraph (each
   `grep -qF` → PRESENT):
   - "Current human selection (2026-09-17): deployment qualification for the first controlled internal-alpha Docker deployment."
   - "024-a (canonical installation/deployment documentation), 025-a/b/c (deployment-qualification docs, image reproducibility, and the post-merge full-rehearsal CI workflow), 026-a (materialized M-LOCAL-PILOT-EVIDENCE ICA request at merged main 21f6204), and 027-a (ICA findings F-001/F-002 doc-drift fix)."
   - "The Independent Closure Audit was executed 2026-09-17 in a fresh isolated context at product revision 21f6204 (report: `docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md`; 37 IMPLEMENTED / 1 PARTIAL / 0 ABSENT / 0 UNPROVEN; no in-target blockers;"
   - "the single PARTIAL row's drift was corrected by 027-a, with the protocol re-audit scheduled at the next milestone-closure attempt"
   - "The next slice is the first real internal-alpha deployment, human-authorized and performed per `INSTALL.md` (deployment-gate brief presented 2026-09-17; a real deployment has not yet been evidenced)."
   - "The slice after that remains human-selected."
   Negative checks on the exact paragraph lines 209–223: `grep -oiF
   'production-ready'` → 0 matches; `grep -oiF 'deployment approved'` → 0
   matches; `grep -oiE 'deployment (was|has been|is) performed'` → 0 matches.
   (Transparency note: an initial over-broad awk range extraction that ran past
   the paragraph into a later roadmap section tripped on a pre-existing,
   untouched "Production-ready" note in that later section; the proof above is
   the corrected check restricted to the paragraph's exact line range.)

4. **Historical snapshots byte-identical — PASSED.**
   `git show cb2045c51099dbc2878173e18ae5550d10793170:STATUS.md | cmp - STATUS.md`
   → identical; `git show cb2045c51099dbc2878173e18ae5550d10793170:docs/project-handoff.md
   | cmp - docs/project-handoff.md` → identical. Neither file appears in the
   base..impl `--name-status` list.

5. **CI at the exact implementation head — PASSED.** head_sha verified from the
   GitHub API (`gh api repos/ulfe-lmi/slaif-asset-reservation/actions/runs/<id>`
   and `.../runs/<id>/jobs`), not from UI copy:
   - Run 35191552886, workflow CI, event pull_request,
     `head_sha: dd7801ff0b2dacce1a30d75d27be0ccca13cfc20`, conclusion success;
     jobs (API per-job `head_sha` all equal to the implementation head):
     quality success (21s), test success (3m9s), security success (17s),
     container success (1m45s).
   - Run 35191552897, workflow oap, event pull_request,
     `head_sha: dd7801ff0b2dacce1a30d75d27be0ccca13cfc20`, conclusion success;
     job: oap-harness success (38s) — triggered because the round bytes touch
     `oap/**`.
   All five jobs green at the exact implementation head on the first run; the
   known pre-existing oap-harness flake did not occur, so no same-head
   re-demonstration was needed.

6. **PR description — PASSED.** PR #56
   (https://github.com/ulfe-lmi/slaif-asset-reservation/pull/56) description
   contains: the three corrected lines with provenance (strategy
   documentation-truth sweep at `cb2045c`; 2026-09-17 human
   deployment-qualification instruction section E "correct current-state
   drift, especially post-024 wording" and section 9 precise status language),
   the verification commands and their results, and truthful status language
   (development merge only; not release/deployment approval/milestone
   acceptance; a real deployment has not yet been evidenced and none is
   approved; deployment remains human-authorized per `INSTALL.md`; no
   merge/auto-merge by coding). "Closes #55" links the objective issue.

7. **This report — see section 4/5.** Report-only commit with the
   implementation head as first parent; contains the diff proof (criterion 1),
   the orders-listing proof (criterion 2), the paragraph grep proofs
   (criterion 3), the historical-docs byte-identity proof (criterion 4), and
   the honest implementation-head vs report-head CI separation (section 5).

8. **DHA outcome — PASSED.** `## Deferred human adjudication` / `- Decision:
   NONE`; no CRITICAL entry created or appended; no human disposition.

## 3. Changed files and scope

Implementation diff base..impl (one commit on the branch; no force-push was
used at any point):
- Commit `dd7801ff0b2dacce1a30d75d27be0ccca13cfc20` (implementation head):
  `README.md` (M, 1 line), `docs/roadmap.md` (M, 2 hunks: 1 line + 1
  paragraph), `oap/active` (A, `028-a` + LF),
  `oap/orders/028-a-doc-truth-post-027.md` (A, 161 lines; byte-identical to the
  published FINAL source).
- Report commit (this publication): only
  `oap/reports/028-a-doc-truth-post-027.md`.

## 4. Commands and results

| Command (revision context) | Result |
| --- | --- |
| `git rev-parse main` / `git ls-remote origin refs/heads/main` (pre-edit) | both `cb2045c51099dbc2878173e18ae5550d10793170` — PASSED (base precondition, equals order `base_sha`) |
| `git branch -a --list '*028*'`; `git ls-remote origin '*028*'` (pre-edit) | empty — PASSED (no branch, fresh round) |
| `gh issue view 55`; `gh pr list --head codex/55-oap-028-a-doc-truth-post-027 --state all` | issue OPEN; no existing PR — PASSED; pr_mode CREATE |
| assertion-guarded python3 edit (README.md line 12; roadmap.md line 190; roadmap.md paragraph lines 209–214) | `ALL EDITS APPLIED; wording verified word-exact (re-wrap only).` — PASSED |
| `cp` FINAL → in-repo order name; `cmp` of the two names | identical — PASSED |
| `git diff --name-status <base>..HEAD` | exactly the four allowed paths — PASSED (criterion 1) |
| `git diff -U0 <base>..HEAD -- README.md docs/roadmap.md` | 1 changed line in README.md; 2 changed hunks in roadmap.md — PASSED (criterion 1) |
| `ls oap/orders/` + 15-ID scripted existence check | `missing: []`, `15 canonical IDs present: True` — PASSED (criterion 2) |
| joined-paragraph word-exact comparison to order text | `WORD-EXACT: True` — PASSED (criterion 3) |
| positive fragment greps on joined paragraph (6 fragments) | all PRESENT — PASSED (criterion 3) |
| `grep -oiF 'production-ready'` / `grep -oiF 'deployment approved'` / `grep -oiE 'deployment (was\|has been\|is) performed'` on paragraph lines 209–223 | 0 / 0 / 0 matches — PASSED (criterion 3) |
| `git show <base>:STATUS.md \| cmp - STATUS.md`; same for `docs/project-handoff.md` | both identical — PASSED (criterion 4) |
| `sha256sum` order file (both names) / `oap/active` | `09d0182c…a10d` / `6cc007b1…37a3` — recorded |
| `gh pr create` (after push) | PR **#56** created, base `main`, head `codex/55-oap-028-a-doc-truth-post-027`, state OPEN, mergeable MERGEABLE, no auto-merge request — PASSED |
| `gh pr checks 56` + `gh api .../runs/<id>` + `.../runs/<id>/jobs` | five jobs green at head `dd7801ff…` — PASSED (criterion 5) |

Product suites: NOT RUN locally (zero product, test, workflow, dependency or
config bytes changed; the ordered acceptance criteria and CI cover this
round). `uv sync` / `ruff` / `mypy` / `pytest` / `pip-audit`: NOT RUN locally
for the same scope reason; all four standard CI jobs plus oap-harness at the
implementation head are PASSED (criterion 5).

## 5. CI observed before authoring

Observed at implementation head
`dd7801ff0b2dacce1a30d75d27be0ccca13cfc20` (head_sha verified from the GitHub
API, run- and job-level):
- CI run 35191552886 (pull_request): quality success, test success, security
  success, container success.
- oap run 35191552897 (pull_request): oap-harness success.

Report-head CI: NOT YET OBSERVED AT AUTHORING. The report publication commit
will re-trigger the oap workflow (it touches `oap/**`); any report-head run
results are post-publication observations and belong to the private execution
receipt, not to this immutable report. No future check success is claimed
anywhere in this report.

## 6. Security, data, dependencies and local tools

- No secrets, credentials, verifiers, peppers, tokens, cookies, CSRF values,
  auth homes or private exports touched, read into the report, or committed.
- No production/lab/Neumann/SmartScheduling contact; no deployment of any
  kind; no DNS/TLS/firewall changes; no real exports; no model calls.
- No ICA activity: no audit execution, no classifications, no re-audit, no new
  audit request; `docs/audit/requests/local-pilot.md`,
  `docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md`, `ARCHITECTURE.md`,
  `ARCHITECTURE-for-agents.md` and `PLAN.md` are byte-untouched (none appears
  in the base..impl `--name-status` list).
- No new dependencies; `uv.lock` untouched. Only routine tooling used: system
  git, python3 (stdlib), gh CLI (Git publication only — push + PR creation,
  the two mutating GitHub operations permitted by the order).
- No reset/clean/stash/force-push. The two pre-existing untracked round files
  (`oap/active`, `oap/orders/028-a-doc-truth-post-027.FINAL.md`) were the only
  dirty worktree entries at start and were consumed by the round (FINAL moved
  to its committed in-repo name, byte-identical).
- No operational CLAUDE.md/Claude launcher.

## 7. DHA outcome and unresolved gates

DHA outcome: **NONE**. No `CRITICAL.md` change; no CRIT entry created,
appended, or referenced as resolved; no human disposition. No unresolved gates
remain for this round; no coding adjudication or gate clearance was performed.

## 8. Limitations and recommendation

- This report proves the three ordered wording corrections, the round bytes,
  and their CI at the implementation head; it is not a release, deployment, or
  milestone acceptance, and it does not claim strategic acceptance of the
  report or PR.
- The corrected lines make current-state docs true about current main: OAP
  objectives 015-a through 027-a are implemented on `main`, the deployment
  qualification selection and the 21f6204 ICA outcome are recorded with exact
  counts, and the document states that a real deployment has not yet been
  evidenced. No status wording implies production-readiness, deployment
  approval, or a performed deployment.
- Recommendation (evidence-backed, not a next order): strategy may review and
  merge PR #56 at exact head `dd7801ff0b2dacce1a30d75d27be0ccca13cfc20`
  (delegated merge after exact-head review); deployment remains
  human-authorized and is the human-selected next slice.
