<!-- OAP-META
{
 "kind": "report",
 "id": "027-a",
 "order_path": "oap/orders/027-a-ica-finding-doc-drift-fix.md",
 "order_sha256": "a27136e7abcc3ad94d7e6d921a1987bc5f7b1c4fae7d85eed77659acf67c4e81",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 53,
 "pr_number": 54,
 "branch": "codex/53-oap-027-a-ica-finding-doc-drift-fix",
 "implementation_head": "2f1ca0a81fb4b8868253c48738cff9c954f5555e",
 "base_sha": "a7b89d21dbb2512d94168d4f3c8a6ceb2f283e45",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "2f1ca0a81fb4b8868253c48738cff9c954f5555e",
  "runs": [
   {"run_id": 35188303965, "workflow": "CI", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 35188303993, "workflow": "oap", "event": "pull_request", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 027-a report — Fix ICA findings F-001/F-002 (two-line governance-doc drift)

Order digest: `a27136e7abcc3ad94d7e6d921a1987bc5f7b1c4fae7d85eed77659acf67c4e81`
(committed `oap/orders/027-a-ica-finding-doc-drift-fix.md`; the strategy-published
`.FINAL` source `oap/orders/027-a-ica-finding-doc-drift-fix.FINAL.md` was moved to
the allowed in-repo name with `mv` before committing, byte-identical, as in prior
rounds; `sha256sum` of both names:
`a27136e7abcc3ad94d7e6d921a1987bc5f7b1c4fae7d85eed77659acf67c4e81`).
Active pointer `oap/active` = `027-a` + LF (verified by hexdump: `3032 372d 610a`;
`sha256sum`: `26156583cb5fadb0eb08286797d3558fecc240c1e38217b4b919b1b9fe50860a`).

Implementation head SHA: 2f1ca0a81fb4b8868253c48738cff9c954f5555e

Report publication commit: SELF

**Result: COMPLETE** — all eight numbered acceptance criteria met. The round
changes exactly two governance-doc lines (one per file) and publishes the round
bytes (order + active pointer); no product, test, workflow, request, ICA-report
or other doc byte changed. No ICA activity was performed: no audit execution,
no classifications, no re-audit, no new audit request. This is a development
merge candidate only; the deployment gate revision 21f6204 is unchanged and
deployment remains human-authorized.

## 1. Starting state and E-list reconciliation (verify, do not assume)

Ordered reads completed: root router → `oap/coding-instructions/AGENTS.md` →
`ARCHITECTURE-for-agents.md` → `OAP-COMMUNICATION-coding-agent.md` → exact active
order (`oap/orders/027-a-ica-finding-doc-drift-fix.FINAL.md`, pointer `027-a`) →
`SECURITY-CORE.md`/`TESTING-CORE.md` → the order's additional read set: the two
lines named in F-001/F-002, the canonical SAR-022 row (`ARCHITECTURE.md` line
526), `docs/architecture.md` (compatibility pointer), the `uv.lock`
djangorestframework entry, and the ICA report findings section F-001/F-002
(`docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md`).

Base verification (order STOP condition): `git rev-parse main` =
`a7b89d21dbb2512d94168d4f3c8a6ceb2f283e45`;
`git ls-remote origin refs/heads/main` =
`a7b89d21dbb2512d94168d4f3c8a6ceb2f283e45`. Equal; no STOP.

Fresh-round verification: no local or remote branch
`codex/53-oap-027-a-ica-finding-doc-drift-fix` existed (`git branch -a`;
`git ls-remote origin` grep for 53/027: none); no open PR for issue #53
(existing remote PR refs belong to issues 6/18/22/29/39/47 only). pr_mode
CREATE_OR_RESUME therefore resolved to CREATE. GitHub-assigned PR number: **54**
(recorded truthfully).

E-list values re-verified live before editing; none differed:
- `ARCHITECTURE-for-agents.md` line 51 (SAR-022 projection row) contained
  "DRF3.16"; line 7 ("Existing baseline" historical row) also contains "DRF3.16"
  and was left untouched per order scope.
- `ARCHITECTURE.md` line 526 (canonical SAR-022 row) contains "DRF3.17";
  `uv.lock` pins `djangorestframework` version 3.17.2 (specifier
  `>=3.16,<3.18`).
- `ARCHITECTURE.md` header line 5 cited `sources/repository/docs-architecture.md`;
  `git ls-files 'sources/repository' | wc -l` → `0`;
  `git rev-parse HEAD:docs/bootstrap/1/previous/docs-architecture.md` →
  `246870a7771452ce3878c228b9ad7ffd8e71eda0`; path exists in-tree.
- Note: the ICA report's F-001 provenance text cites "line 12" for the
  projection SAR-022 row; in the live file at base a7b89d2 that row is line 51,
  matching the order's strategy spot-verification (2026-09-17). The edit was
  applied to the row that is actually the SAR-022 projection row.

## 2. Acceptance evidence (numbered per order)

1. **Diff scope — PASSED.** `git diff --name-status
   a7b89d21dbb2512d94168d4f3c8a6ceb2f283e45..2f1ca0a81fb4b8868253c48738cff9c954f5555e`:
   ```
   M	ARCHITECTURE-for-agents.md
   M	ARCHITECTURE.md
   A	oap/active
   A	oap/orders/027-a-ica-finding-doc-drift-fix.md
   ```
   Only the two allowed doc files plus the round bytes. `git diff -U0` over the
   two doc files shows exactly one changed line in each (one removed + one added
   line per file):
   ```
   @@ -51 +51 @@ (ARCHITECTURE-for-agents.md)
   -**SAR-022 / Reproducible monolith:** Preserve Python3.13, Django5.2, DRF3.16, PostgreSQL17, uv.lock, Gunicorn, WhiteNoise, local Swagger sidecar and server-rendered views. Add no production dependency or alternate stack without ordered justification/accepted decision.
   +**SAR-022 / Reproducible monolith:** Preserve Python3.13, Django5.2, DRF3.17, PostgreSQL17, uv.lock, Gunicorn, WhiteNoise, local Swagger sidecar and server-rendered views. Add no production dependency or alternate stack without ordered justification/accepted decision.
   @@ -5 +5 @@ (ARCHITECTURE.md)
   -The accepted `docs/architecture.md` is preserved unchanged in `sources/repository/docs-architecture.md`
   +The accepted `docs/architecture.md` is preserved unchanged in `docs/bootstrap/1/previous/docs-architecture.md`
   ```
   No wrap was needed for the line-5 sentence to stay grammatical, so the change
   remains exactly one line.

2. **F-001 correction — PASSED.** `sed -n '51p' ARCHITECTURE-for-agents.md |
   grep -c 'DRF3.17'` → `1`; `... | grep -c 'DRF3.16'` → `0`. Line 7
   byte-identical to base: `git show main:ARCHITECTURE-for-agents.md | sed -n '7p'`
   vs `sed -n '7p' ARCHITECTURE-for-agents.md`, then `cmp` → identical (no
   output, rc 0). Scripted stack-label comparison (command + literal output):
   ```
   $ python3 - <<'EOF'
   import re
   proj = open('ARCHITECTURE-for-agents.md').read().splitlines()
   canon = open('ARCHITECTURE.md').read().splitlines()
   def row(lines, needle):
       for i, l in enumerate(lines, 1):
           if needle in l:
               return i, l
       raise SystemExit('row not found: ' + needle)
   pi, pl = row(proj, '**SAR-022 / Reproducible monolith:**')
   ci, cl = row(canon, 'Preserve Python3.13, Django5.2, DRF3.17, PostgreSQL17')
   labels = ['Python3.13', 'Django5.2', 'DRF3.17', 'PostgreSQL17']
   p = [l in pl for l in labels]; c = [l in cl for l in labels]
   print('projection row line', pi, 'labels present:', p)
   print('canonical row line', ci, 'labels present:', c)
   print('MATCH' if p == c == [True]*4 else 'MISMATCH')
   EOF
   projection row line 51 labels present: [True, True, True, True]
   canonical row line 526 labels present: [True, True, True, True]
   MATCH
   ```
   Run at implementation head 2f1ca0a81fb4b8868253c48738cff9c954f5555e worktree.

3. **F-002 correction — PASSED.** Header now cites
   `docs/bootstrap/1/previous/docs-architecture.md`; path exists in-tree
   (`test -e` → true). `git rev-parse HEAD:docs/bootstrap/1/previous/docs-architecture.md`
   (at implementation head) prints exactly:
   `246870a7771452ce3878c228b9ad7ffd8e71eda0`. The blob citation on header line 6
   is unchanged — the `git diff -U0` in criterion 1 shows line 5 as the only
   changed line in `ARCHITECTURE.md`; line 6 still reads "(Git blob
   `246870a7771452ce3878c228b9ad7ffd8e71eda0`). This edition consolidates that
   design with".

4. **Digests — PASSED.**
   - `ARCHITECTURE.md` before (base a7b89d2): `182d9cf924931e846bc7965a762af807196ca0b87f8dffdf863`
     (matches the ICA request/report's bound digest).
   - `ARCHITECTURE.md` after (implementation head): `8483a070026f382bb9b698e9346f3cb33f7dea44f8190b231431585986ebb17d`
     (header edit changes the canonical digest, as expected).
   - The 21f6204 ICA request
     (`docs/audit/requests/local-pilot.md`) and ICA report
     (`docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md`) remain bound to the
     old digest `182d9cf9…` as revision-bound, immutable artifacts; both are
     unchanged in this round (`git diff --name-status` base..impl lists neither).
   - `PLAN.md` unchanged: `d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06`
     (before and after; equals the order's expected value).
   - `ARCHITECTURE-for-agents.md` after (implementation head):
     `67cc4f8fbeb5223bf6816cc63e154ef58d14cde3ec6b11c594702f85f3a1c531`
     (recorded for completeness; projection file is not digest-bound in-tree).

5. **CI at the exact implementation head — PASSED.** head_sha verified from the
   GitHub API (`gh run view <id> --json headSha`):
   - Run 35188303965, workflow CI, event pull_request,
     `headSha: 2f1ca0a81fb4b8868253c48738cff9c954f5555e`, conclusion success;
     jobs: quality success, test success, security success, container success.
   - Run 35188303993, workflow oap, event pull_request,
     `headSha: 2f1ca0a81fb4b8868253c48738cff9c954f5555e`, conclusion success;
     job: oap-harness success (triggered because the round bytes touch `oap/**`).
   All five jobs green at the exact implementation head on the first run; the
   known pre-existing oap-harness flake did not occur.

6. **PR description — PASSED.** PR #54 (https://github.com/ulfe-lmi/slaif-asset-reservation/pull/54)
   description contains: both findings with provenance (ICA report F-001/F-002 +
   strategy spot-verification 2026-09-17), the exact one-line diffs, the
   recorded no-re-audit sequencing decision (S-23 non-goal), and truthful status
   language (development merge only; deployment gate revision 21f6204 unchanged;
   deployment remains human-authorized).

7. **This report — see verification below.** Report-only commit with the
   implementation head as first parent; contains the diff proof (criterion 1),
   the scripted stack-label comparison output (criterion 2), the rev-parse proof
   (criterion 3), the digest before/after record (criterion 4), and the honest
   implementation-head vs report-head CI separation (section 4).

8. **DHA outcome — PASSED.** `## Deferred human adjudication` / `- Decision:
   NONE`; no CRITICAL entry created or appended; no human disposition.

## 3. Changed files and scope

Implementation diff base..impl (two commits on the branch; no force-push was
used at any point):
- Commit 15c28f3…: round bytes — `oap/active` (A),
  `oap/orders/027-a-ica-finding-doc-drift-fix.md` (A).
- Commit 2f1ca0a… (implementation head): `ARCHITECTURE-for-agents.md` (M, 1
  line), `ARCHITECTURE.md` (M, 1 line).
- Report commit (this publication): only
  `oap/reports/027-a-ica-finding-doc-drift-fix.md`.

The branch needed two implementation commits because the first commit was made
after staging the round bytes, before the two doc edits were added to the index;
rewriting it would have required a force-push, which C-09/SC-04 forbid. The
acceptance-relevant evidence is the base..impl diff, which touches only the four
allowed paths.

## 4. Commands and results

| Command (revision context) | Result |
| --- | --- |
| `git rev-parse main` / `git ls-remote origin refs/heads/main` (pre-edit) | both `a7b89d21dbb2512d94168d4f3c8a6ceb2f283e45` — PASSED (base precondition) |
| `git branch -a`; `git ls-remote origin \| grep -Ei '53\|027'` (pre-edit) | no branch/PR for this objective — PASSED (fresh round) |
| `sed -i '51s/DRF3\.16/DRF3.17/' ARCHITECTURE-for-agents.md` | 1 line changed — PASSED |
| `sed -i '5s\|sources/repository/docs-architecture.md\|docs/bootstrap/1/previous/docs-architecture.md\|' ARCHITECTURE.md` | 1 line changed — PASSED |
| `sha256sum` order file before/after `mv` to in-repo name | identical `a27136e7…` — PASSED (byte-identical rename) |
| `git diff -U0 <base>..HEAD` (doc files) | exactly one changed line per file — PASSED |
| `sed -n '51p' … \| grep -c 'DRF3.17'` / `grep -c 'DRF3.16'` | `1` / `0` — PASSED |
| `cmp` line 7 base vs head | identical — PASSED |
| scripted stack-label comparison (section 2.2) | `MATCH` — PASSED |
| `git rev-parse HEAD:docs/bootstrap/1/previous/docs-architecture.md` | `246870a7771452ce3878c228b9ad7ffd8e71eda0` — PASSED |
| `sha256sum ARCHITECTURE.md ARCHITECTURE-for-agents.md PLAN.md` (pre-edit and post-edit) | section 2.4 values — PASSED |
| `git diff --check` (index and worktree) | clean — PASSED |
| `python3 -m unittest discover -s tests/oap -p 'test_*.py'` (local, worktree at impl head) | `Ran 154 tests … FAILED (failures=1)` — see below |
| same module with `env -u OAP_ROLE` | `Ran 12 tests … OK` — PASSED under CI-equivalent environment |

**Local oap-harness failure (honest record, environment artifact).** The single
local failure is
`test_ba39_strategic_same_prerequisites
(tests/oap/test_ba38_39_tmux_config.py:220)`, assertion
"print-only is always allowed" (rc 1). Root cause: this agent environment
exports `OAP_ROLE=CODING` (wrapper-provided role marker), and
`oap/bin/oap_launch.py` line 255–257 refuses a strategic launch under a
conflicting role (`"conflicting OAP_ROLE=CODING; refusing"`). The test's
fixture invokes `oap_launch.py strategic … --print-only` inheriting the
ambient environment. This is role-separation working as designed, not a
repository defect, and is unrelated to the two doc-line changes (docs are not
exercised by the harness). With `OAP_ROLE` unset (the CI condition) the full
module passes 12/12, and the CI oap-harness job at the exact implementation
head is green (criterion 5).

Product suites: NOT RUN locally (zero product, test, workflow, dependency or
config bytes changed; the ordered acceptance criteria and CI cover this round).
`uv sync`/`ruff`/`mypy`/`pytest`/`pip-audit`: NOT RUN locally for the same
scope reason; all four standard CI jobs at the implementation head are PASSED.

## 5. CI observed before authoring

Observed at implementation head
`2f1ca0a81fb4b8868253c48738cff9c954f5555e` (head_sha verified from the API):
- CI run 35188303965 (pull_request): quality success, test success, security
  success, container success.
- oap run 35188303993 (pull_request): oap-harness success.

Report-head CI: NOT YET OBSERVED AT AUTHORING. The report publication commit
will re-trigger oap-harness (it touches `oap/**`); any report-head run results
are post-publication observations and belong to the private execution receipt,
not to this immutable report. No future check success is claimed anywhere in
this report.

## 6. Security, data, dependencies and local tools

- No secrets, credentials, verifiers, peppers, tokens, cookies, CSRF values,
  auth homes or private exports touched, read into the report, or committed.
- No production/lab/Neumann/SmartScheduling contact; no deployment of any kind;
  no DNS/TLS/firewall changes; no real exports; no model calls.
- No ICA activity: no audit execution, no classifications, no re-audit, no new
  audit request; the ICA report and request (revision-bound to 21f6204) are
  byte-untouched.
- No new dependencies; `uv.lock` untouched. Only routine tooling used: system
  git, python3 (stdlib), gh CLI (Git publication only — push + PR creation, the
  two mutating GitHub operations permitted by the order).
- No reset/clean/stash/force-push; the two pre-existing untracked round files
  were the only dirty worktree entries at start and were consumed by the round.
- No operational CLAUDE.md/Claude launcher.

## 7. DHA outcome and unresolved gates

DHA outcome: **NONE**. No `CRITICAL.md` change; no CRIT entry created,
appended, or referenced as resolved; no human disposition. No unresolved gates
remain for this round; no coding adjudication or gate clearance was performed.

## 8. Limitations and recommendation

- This report proves the two ordered wording corrections and their CI at the
  implementation head; it is not a release, deployment, or milestone
  acceptance, and it does not claim strategic acceptance of the report or PR.
- The canonical `ARCHITECTURE.md` digest changed by design
  (`182d9cf9…` → `8483a070…`); the 21f6204 ICA request/report remain bound to
  the old digest as revision-bound artifacts. Per the recorded S-23
  sequencing decision, the architecture-to-current-main ICA matrix rerun is
  scheduled at the next milestone-closure attempt (post-deployment pilot
  evidence) against the then-current revision; no re-audit is owed by this
  round.
- Recommendation (evidence-backed, not a next order): strategy may review and
  merge PR #54 at exact head `2f1ca0a81fb4b8868253c48738cff9c954f5555e`
  (delegated merge after exact-head review); deployment remains
  human-authorized.
