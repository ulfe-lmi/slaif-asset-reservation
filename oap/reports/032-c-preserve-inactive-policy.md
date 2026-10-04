<!-- OAP-META
{
 "kind": "report",
 "id": "032-c",
 "order_path": "oap/orders/032-c-preserve-inactive-policy.md",
 "order_sha256": "c97599b6c6302955a4863d545602542c46280f07450e93d663aefed1815524f3",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 63,
 "pr_number": 64,
 "branch": "codex/63-oap-032-a-internet-ux-contract",
 "implementation_head": "a51162fa9d23624e6364c3fc84ba2700113459e2",
 "base_sha": "3abe17d026d7ebfe402426afd89e30cdc6924f61",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "a51162fa9d23624e6364c3fc84ba2700113459e2",
  "runs": [
   {"run_id": 37179579753, "workflow": "CI", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 37179579907, "workflow": "oap", "event": "pull_request", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 032-c report — preserve inactive-policy configuration in the executor contract

Order digest: `c97599b6c6302955a4863d545602542c46280f07450e93d663aefed1815524f3`
(committed `oap/orders/032-c-preserve-inactive-policy.md`, strategy-published order bytes
as-is; `state: FINAL`, `pr_mode: AMEND`, `previous_round: 032-b`, `decision_class: D0`,
`Decision: NONE`). Active pointer `oap/active` = `032-c` + LF (verified by xxd:
`3033 322d 630a`, 6 bytes).

Implementation head SHA: a51162fa9d23624e6364c3fc84ba2700113459e2

Report publication commit: SELF

**Result: COMPLETE** — all three numbered acceptance criteria met. The round changes
exactly the ordered documentation files and publishes the round bytes (order + active
pointer) on the same objective PR #64 (AMEND). Zero product, runtime, test, dependency,
migration, workflow, container, archived-snapshot, governance-law or ICA-report byte
changed. The 032-a and 032-b orders and reports are immutable and untouched.
SAR-039–SAR-047 remain selected-target obligations, initially UNPROVEN until a fresh
isolated ICA at the exact merged revision; no control is claimed implemented and no D2
boundary was crossed.

## 1. Starting state and E-list reconciliation (verify, do not assume)

Ordered reads completed: root router -> `oap/coding-instructions/AGENTS.md` ->
`ARCHITECTURE-for-agents.md` -> `OAP-COMMUNICATION-coding-agent.md` -> exact active order
(pointer `oap/active` = `032-c` + LF ->
`oap/orders/032-c-preserve-inactive-policy.md`) -> `SECURITY-CORE.md` / `TESTING-CORE.md`
-> only the order's scoped subtree (the two ordered documentation files as committed, the
prior 032-b report, and the root architecture SAR-041 / human-requirement-2 paragraphs).
No wildcard, source-book, future-draft or whole-roadmap loading. The wrapper had already
consumed the control wake-up; it was not consumed again.

Reconciliation before edit (remote/local, C-06; AMEND round c on objective issue 63):
- Local branch `codex/63-oap-032-a-internet-ux-contract` head = remote PR #64 head =
  `deaf1cdf7ec73e1430a6638c6c8a8888ae4d43dd` (the frozen 032-b report commit), whose
  first parent is `277b0090637a35092a8a43da6c0e0c153717dcf2` — both exactly as stated in
  the order's provenance E. PR #64 is OPEN, unmerged, base `main` =
  `3abe17d026d7ebfe402426afd89e30cdc6924f61` = order `base_sha`, mergeable. Same
  objective, same round branch, same PR across the transition — no renumbering, no new
  PR.
- Source hashes verified against the order via `sha256sum` in this checkout before edit:
  `ARCHITECTURE.md` `06dd0f50e778b9843e2a709caa0ae1f0c97f48baee726f4e3a1397cc6a198d8c`,
  `PLAN.md` `b19219e2d727af5a9554e011ba45a786f1bb61f25c001011fc18006cae665d08` (both
  equal to the order's `source_hashes`). `governance_revision`
  `14fc20b1ff52788974fd3f282322afc9d71362f9` resolves to a historical merge commit in
  this repository's history; recorded, nothing further required.
- E-list semantic claim independently confirmed before editing: the root architecture's
  default fresh-install policy (human requirement 2 paragraph, and the SAR-041 row)
  requires existing operator policies "(including deliberate inactive configuration)" to
  be preserved with "no duplicate active-global policy or silent overwrite", and states
  no reactivation support; the compact projection's `no silent overwrite, reactivation
  supported;` lost that negation (exactly one occurrence in the projection, located by
  grep).
- Working tree at start: branch head plus the ordered round bytes only — `oap/active`
  modified (`032-b` -> `032-c`) and untracked
  `oap/orders/032-c-preserve-inactive-policy.md`. No foreign/dirty files existed to
  preserve; no reset/clean/stash/force-push performed.

## 2. Acceptance evidence (ordered criteria)

**Criterion 1 — One-phrase SAR-041 negation correction. PASSED.**
In `ARCHITECTURE-for-agents.md`, the single occurrence of `no silent overwrite,
reactivation supported;` was replaced with `no silent overwrite or reactivation;`
(programmatic replacement asserting exactly one occurrence). Verification against the
committed pre-032-c bytes: the whole-file diff is exactly one changed line (line 98, the
SAR-041 clause) and that line differs only by the phrase; SAR-001..SAR-038 and
SAR-042..SAR-047 clauses are byte-identical; the header block, `Component routing`,
`Current API boundaries`, `Verification cautions` and the `Selected target
qualification (A-15)` clause are byte-identical. Projection size 19982 -> 19974 bytes
(-8); new content SHA-256
`26d26dac79043ed6b7b1e2ce4e134c5e6ccd6e9504f41f65339c76672bf59483`. No reactivation
feature was added and no future operator workflow inferred.

**Criterion 2 — Correction note and recomputed identity/measurements in the review
record. PASSED.**
`docs/governance/INTERNET-UX-PROJECTION-REVIEW.md` (12355 -> 14213 bytes) updated only
with the corresponding correction note, the actual projection hash and the actual byte
measurements:
- Header order list now records 032-c (D0 single-phrase negation correction; not an ICA).
- Section 1: current projection identity is the post-032-c hash
  `26d26dac79043ed6b7b1e2ce4e134c5e6ccd6e9504f41f65339c76672bf59483`; the preceding
  post-032-b hash `09d2157df1a57a312071f818fcb2600bee65abce213aa268f657fb67ab3b3cf3` is
  preserved as historical (superseded SAR-041 wording). Canonical source
  `06dd0f50…` and PLAN `b19219e2…` identities are unchanged by 032-c.
- Section 4 (measured on the committed bytes): projection 19974 <= 20000 (measured
  margin 26 bytes — small, not a large margin; further growth will need explicit
  faithful redistillation, not truncation); routine transitive read set 34897 <= 50000
  (AGENTS.md 1058 + oap/coding-instructions/AGENTS.md 6403 + projection 19974 +
  OAP-COMMUNICATION-coding-agent.md 4105 + SECURITY-CORE 1410 + TESTING-CORE 1947);
  conservative wider sum (projection + PLAN.md + this review, all post-032-c bytes) =
  19974 + 15523 + 14213 = 49710 <= 50000. Tokens UNMEASURED (no qualified tokenizer;
  same convention as generation 1).
- New section 6 (superseding note): records that the preceding compact wording was
  incorrect and is superseded by this precise correction, with the reason (the full
  architecture preserves deliberate inactive operator configuration; the lost negation
  could mislead a later initializer into reactivating operator-inactive booking
  authority); the projection byte change (-8) and the small-margin statement; and the
  measurement drift correction (the 032-b review byte figure 12353 differed by 2 bytes
  from the actually committed review, 12355; this record reports actual committed
  bytes). The old semantic mapping and historical records are preserved without
  renumbering; the section-2 mapping table needed no change (it never carried the
  incorrect phrase).

**Criterion 3 — Verification battery and immutable sequence. PASSED.**
- Exact one-phrase projection diff: PASSED (section 2, criterion 1; `git diff` shows
  one changed line, phrase-only).
- Unchanged original 38 clauses / full architecture / PLAN / runtime / dependencies /
  migrations: PASSED — 38/38 byte-identical clause comparison; `ARCHITECTURE.md` and
  `PLAN.md` SHA-256 re-verified after the edit (equal to order `source_hashes`);
  `git status` shows only the four ordered paths; `mypy` clean and
  `makemigrations --check` reports no changes.
- Current links: PASSED — every internal document reference in the changed files
  resolves (`docs/bootstrap/archive/CONTEXT-BUDGET.md`, `ARCHITECTURE.md`, `PLAN.md`,
  `docs/governance/INTERNET-UX-PROJECTION-REVIEW.md`); slaif.si / doc.slaif.si /
  edu.slaif.si / trainings remain external design references, not verifiable offline,
  reference-only.
- Appropriate lint/format/type/diff: PASSED — `ruff check .`, `ruff format --check .`
  (186 files), `mypy src` (119 files), `git diff --check`, `manage.py check` (0
  issues), `manage.py makemigrations --check --dry-run` (no changes). No new tests for
  prose (ordered).
- Standard five exact-head checks at implementation head
  `a51162fa9d23624e6364c3fc84ba2700113459e2` (section 5): quality, test, security,
  container (CI run 37179579753) and oap-harness (oap run 37179579907) all SUCCESS
  before this report was written. The unchanged product suite ran through the CI `test`
  job on real PostgreSQL 17 (619 passed in 173.82s), guarding preservation; it does not
  implement/qualify the new target.
- Sequence: order/pointer/implementation push -> exact five checks -> immutable
  report-only commit (this file only, implementation head as first parent) -> push ->
  remote verification -> exact response OK -> exit. `Closes #63` remains in the PR #64
  body (verified line present); PR identity and body were not changed by this round.

## 3. Changed files and scope

Implementation commit `a51162fa9d23624e6364c3fc84ba2700113459e2` (first parent
`deaf1cdf7ec73e1430a6638c6c8a8888ae4d43dd`; 4 files, +145/-15):
- `ARCHITECTURE-for-agents.md` — 19982 -> 19974 bytes, one changed line (criterion 1).
- `docs/governance/INTERNET-UX-PROJECTION-REVIEW.md` — 12355 -> 14213 bytes (criterion 2).
- `oap/orders/032-c-preserve-inactive-policy.md` — new, strategy-published order bytes
  as-is (SHA-256 `c97599b6c6302955a4863d545602542c46280f07450e93d663aefed1815524f3`).
- `oap/active` — pointer bytes `032-c` + LF as-is (was `032-b`).

No file under `src/`, `tests/`, `deploy/`, `data/`, `.github/`, `pyproject.toml`,
`uv.lock`, `Dockerfile`, `compose*`, `oap/governance/`, `oap/bin/`,
`oap/coding-instructions/`, `oap/strategic-instructions/`, `docs/bootstrap/`,
`docs/audit/`, `oap/orders/` (other orders) or `oap/reports/` (prior reports) was
touched; `ARCHITECTURE.md` and `PLAN.md` unchanged (hashes re-verified after edit).
CRITICAL register untouched.

## 4. Commands and results (summary)

| Command (exact) | Result |
| --- | --- |
| `sha256sum ARCHITECTURE.md PLAN.md` (before edit) | PASSED (equal to order source_hashes `06dd0f50…` / `b19219e2…`) |
| `git rev-parse origin/main` / PR #64 head via `gh pr view 64` | PASSED (base = `3abe17d…`; PR head = local head `deaf1cd…`; PR OPEN, unmerged, mergeable; `Closes #63` in body) |
| `xxd oap/active` (before commit) | PASSED (`3033 322d 630a`, 6 bytes = `032-c` + LF) |
| `sha256sum oap/orders/032-c-preserve-inactive-policy.md` (committed bytes) | PASSED (`c97599b6…`) |
| single-phrase replacement script (asserts exactly one occurrence) | PASSED (1 replacement, 0 accidental) |
| programmatic clause comparison vs committed pre-032-c bytes | PASSED (SAR-001..SAR-038 + SAR-042..SAR-047 byte-identical; only SAR-041 line changed, phrase-only; header/sections byte-identical) |
| internal link/file-existence check (changed files) | PASSED (all internal refs exist; external references noted) |
| `wc -c` / `sha256sum` measurements (post-edit, pre-commit) | PASSED (projection 19974 <= 20000, hash `26d26dac…`; read set 34897 <= 50000; wider sum 49710 <= 50000) |
| `uv run ruff check .` | PASSED (All checks passed!) |
| `uv run ruff format --check .` | PASSED (186 files already formatted) |
| `uv run mypy src` | PASSED (no issues in 119 source files) |
| `git diff --check` | PASSED (clean) |
| `uv run --env-file .env python manage.py check` | PASSED (0 issues) |
| `uv run --env-file .env python manage.py makemigrations --check --dry-run` | PASSED (No changes detected) |
| local product suite | NOT RUN (not ordered for a governance-only round; CI `test` job at the exact head is the authoritative result: 619 passed in 173.82s) |
| exact-head CI (5 checks) | PASSED (section 5) |

Environment: uv-managed CPython 3.13 (repo venv). No database, container, browser or
external network resource was used by any local step; only file digests, git state and
read-only GitHub API queries were performed locally.

## 5. CI observed before authoring

Observed at authoring time, at implementation head
`a51162fa9d23624e6364c3fc84ba2700113459e2` (structured check/job data from the GitHub
API; headSha equality verified from the API):
- CI workflow run 37179579753 (`pull_request`, conclusion `success`):
  `quality` success (job 111369228389), `test` success (job 111369228265:
  `619 passed in 173.82s` on real PostgreSQL 17), `security` success (job
  111369228372, pip-audit and production-settings fail-closed check), `container`
  success (job 111369228371).
- oap workflow run 37179579907 (`pull_request`, conclusion `success`):
  `oap-harness` success (job 111369228868).

Report-head CI is **NOT YET OBSERVED AT AUTHORING**: this report's own publication
commit postdates the observed head, and no check result at the report commit is claimed
here. Post-publication verification observations belong to the private execution receipt
(CP-07), not to this report.

## 6. Security, data, dependencies and local tools

- No credentials, verifiers, peppers, cookies, CSRF, Authorization data, raw payloads,
  private exports or physical locators were read, written or logged. No auth-home
  copying, no OS sidecars, no real exposure, no DNS/TLS/firewall change, no lab/
  Neumann/production contact, no real secrets or production data.
- No new dependency, no lock change, no application/domain/auth/policy/UI/migration/
  runtime-config/workflow/container byte changed; SAR-022 preserved (stack unchanged);
  SAR-024 preserved (no exposure change — this round is documentation only); SAR-033
  preserved (history, prior orders/reports, archives untouched); SAR-035 preserved
  (private infrastructure boundary respected; only the private development remote via
  the separately authorized Git publication); SAR-037 preserved (canonical PLAN and full
  architecture unchanged; the projection hash-bound and coverage-mapped correction is
  recorded in the coverage record); SAR-038 preserved (no release/deployment/ICA
  claim).
- No operational CLAUDE.md/Claude launcher was used or created.

## 7. DHA outcome and unresolved gates

Order declaration: `## Deferred human adjudication` / `- Decision: NONE`. No CRITICAL
entry was appended, no human disposition or gate clearance was performed or implied,
and no D2 boundary was crossed. The only outstanding development gate is strategic
review/development merge of PR #64, which belongs to strategy. Real Internet exposure,
DNS/TLS/firewall, identity, secrets and private data remain human D2; the development
sequence in PLAN P-06 stays DRAFT UNTIL STRATEGIC RECONCILIATION, and the milestone
M-INTERNET-UX-PILOT is selected, not complete.

## 8. Limitations and recommendation

- This is a D0 correction of a lost negation, not a new policy decision, not an ICA and
  not implementation: SAR-039–SAR-047 remain initially UNPROVEN; the corrected SAR-041
  clause is a contract statement for a future initialization objective, not an
  implemented control, and no implementation or milestone-readiness claim is made here.
- The corrected wording is the faithful compact contract: initialization must not
  silently reactivate operator-inactive configuration. Any later initializer must
  preserve deliberately inactive operator policies (root architecture, human
  requirement 2); the full facet wording remains in root A-15 (reference only) and in
  the coverage mapping.
- Measured context uses the generation-1 convention (routine transitive coding read set
  excluding the active order and product code); tokens are UNMEASURED for lack of a
  qualified tokenizer. The projection margin against its 20000-byte ceiling is small
  (26 bytes at this measurement), not large; further growth will need explicit
  faithful redistillation, not truncation. The conservative wider sum
  (projection + PLAN + review = 49710 bytes) is recorded for transparency even though
  it is outside the routine set.
- No dedicated markdown-links CI job exists; the links facet is evidenced by the
  internal file-existence check. pip-audit itself ran green in the security job at the
  exact head.
- Report-head CI is unobserved at authoring; a failure there routes to a strategy
  suffix, not an amendment of this report.
- No claim is made for later requirements or milestone readiness; PR #64 (now carrying
  032-a, 032-b and 032-c) remains a development merge candidate that records the
  selected target.
