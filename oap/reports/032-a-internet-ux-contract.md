<!-- OAP-META
{
 "kind": "report",
 "id": "032-a",
 "order_path": "oap/orders/032-a-internet-ux-contract.md",
 "order_sha256": "5ae318238de755bedde5b87137a3e171d05b257e6c2e8615558dbed4f596cfb6",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 63,
 "pr_number": 64,
 "branch": "codex/63-oap-032-a-internet-ux-contract",
 "implementation_head": "6373aba6729ca94e5eabf79d65a2649c24f8de86",
 "base_sha": "3abe17d026d7ebfe402426afd89e30cdc6924f61",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "6373aba6729ca94e5eabf79d65a2649c24f8de86",
  "runs": [
   {"run_id": 37176857062, "workflow": "CI", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 37176857071, "workflow": "oap", "event": "pull_request", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 032-a report — record selected Internet/UX contract and executor projection

Order digest: `5ae318238de755bedde5b87137a3e171d05b257e6c2e8615558dbed4f596cfb6`
(committed `oap/orders/032-a-internet-ux-contract.md`, strategy-published
order bytes as found in the working tree; no rename/move). Active pointer
`oap/active` = `032-a` + LF (verified by xxd: `3033 322d 610a`, 6 bytes).

Implementation head SHA: 6373aba6729ca94e5eabf79d65a2649c24f8de86

Report publication commit: SELF

**Result: COMPLETE** — all numbered acceptance criteria met. The round changes
exactly the seven ordered documentation/governance files and publishes the
round bytes (order + active pointer). Zero product, runtime, test,
dependency, migration, workflow, container, archived-snapshot, governance-law
or ICA-report byte changed. The selected M-INTERNET-UX-PILOT contract
(A-15, SAR-039–SAR-047) is recorded as target meaning only; every new row is
initially UNPROVEN and no control is claimed implemented. Development merge
candidate only; no deployment, release, ICA, milestone-complete or
physical-resource consequence is claimed.

## 1. Starting state and E-list reconciliation (verify, do not assume)

Ordered reads completed: root router -> `oap/coding-instructions/AGENTS.md`
-> `ARCHITECTURE-for-agents.md` -> `OAP-COMMUNICATION-coding-agent.md` ->
exact active order (pointer `oap/active` = `032-a` + LF ->
`oap/orders/032-a-internet-ux-contract.md`, `state: FINAL`,
`pr_mode: CREATE_OR_RESUME`, `previous_round: null`, `decision_class: D0`,
`Decision: NONE`) -> `SECURITY-CORE.md` / `TESTING-CORE.md` -> only the
order's scoped subtree (the six ordered documentation files as committed at
base). No wildcard, source-book, future-draft or whole-roadmap loading. The
wrapper had already consumed the control wake-up; it was not consumed again.

Reconciliation before edit (remote/local, C-06; CREATE_OR_RESUME round a):
- Local main = remote `origin/main` =
  `3abe17d026d7ebfe402426afd89e30cdc6924f61` = order `base_sha`. No local branch/PR for issue 63 existed; `gh` shows no open
  PR and no remote branch matching the ordered name, so this round created
  branch `codex/63-oap-032-a-internet-ux-contract` and PR #64 (one PR for
  the objective, body ends with `Closes #63`).
- Source hashes verified against the order via `sha256sum` in this checkout
  at base: `ARCHITECTURE.md`
  `8483a070026f382bb9b698e9346f3cb33f7dea44f8190b231431585986ebb17d`,
  `PLAN.md` `d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06`
  (both equal to the order's `source_hashes`, i.e. pre-change identities).
- E-list items independently re-observed via the GitHub API: PR #62
  `state: MERGED` (merged 2026-10-04T04:00:25Z) on branch
  `codex/61-oap-031-a-gunicorn-idle-connections`; issue #61 `CLOSED`
  (2026-10-04T04:00:26Z); report head
  `065cf891c2cf353114928eba6c4e2bdf7612d361` has both runs at `success`
  (CI 37175425767, oap 37175425641, `pull_request`); local main's push CI at
  `3abe17d` was observed completed `success` (CI 37175710010, oap
  37175709851) during this reconciliation — recorded as an observation at
  this time, not as a claim at activation.
- Working tree at start: main plus the ordered round bytes only —
  `oap/active` modified (`031-c` -> `032-a`) and untracked
  `oap/orders/032-a-internet-ux-contract.md`. No foreign/dirty files existed
  to preserve; no reset/clean/stash/force-push performed.
- The 031-a/031-b/031-c report and order bytes were not touched; no merged
  PR was mutated; no prior report was rewritten.

## 2. Acceptance evidence (ordered criteria)

**Criterion 1 — Canonical architecture changes applied exactly. PASSED.**
- `ARCHITECTURE.md` final bytes
  SHA-256 `06dd0f50e778b9843e2a709caa0ae1f0c97f48baee726f4e3a1397cc6a198d8c`
  (64758 bytes, was 45876 at base, +18882):
  - Root header now distinguishes the original conversion observations
    (2026-09 baseline, point-in-time, not current audit results) from the
    current selected target (2026-10-04, M-INTERNET-UX-PILOT development,
    real exposure human D2), states that this edition appends A-15 and
    SAR-039–SAR-047 and weakens/replaces no A-01–A-14 section or
    SAR-001–SAR-038 requirement, and preserves the archived accepted-source
    provenance (Git blob `246870a7…` line unchanged in meaning).
  - A-03: current source constraint made explicit — DRF `>=3.16,<3.18`
    (source) with "the lock is authoritative and resolves DRF 3.17.x"
    (verified against `pyproject.toml` and `uv.lock`: djangorestframework
    3.17.2).
  - A-05 Policies: the old no-policy-seed assertion is now a labeled
    historical 2026-09 baseline observation with an explicit pointer to the
    SAR-041 target; the token-scope non-grant sentence continues.
  - A-10: both old proof-gap claims (count-queries-before-DB-readiness
    guard/broad catch; no documented isolated restore drill) are labeled
    point-in-time/historical with "current evidence belongs to the exact
    reports/tests/audits at the exact revision" and "no fresh result is
    claimed here".
  - A-13: current selected target sentence added (selection is not
    completion; D2 and M-EXTERNAL-PILOT/release gates continue).
  - A-14 intro: classification lines declared baseline point-in-time (or
    new-milestone initial), not current audit results.
  - New stable rows SAR-039–SAR-047 appended after SAR-038 in the exact
    existing Source/Inspect/Evidence/classification format, each
    `**UNPROVEN** (new milestone…)`; SAR-047 carries the predecessor
    "evidence indexed but not self-certified ICA" note.
  - New A-15 section appended at end of file: the strategy-authored
    selected-target contract (all nine substantive paragraphs) applied in
    meaning verbatim — product meaning, qualified topology, abuse
    protection, default fresh-install policy (`default`: asset NULL,
    horizon 7 days by reservation START, max 2880 minutes/48 h/2 days, no
    operating-hour window, lead 0, cutoff 0, purpose optional), public
    landing/identity, explained forms, SLAIF appearance/theming, threaded
    Gunicorn (plus the permitted observed-not-claimed note that merged
    predecessor 031-a/PR62 established the gthread baseline), and the
    qualification/human-gate paragraph. No control below A-15 is claimed
    implemented.
- `PLAN.md` final bytes SHA-256
  `c39f3f82b8493f751cb57388b46e4f61e1be1c82be1c9613ec09c3715634d0fc`
  (15201 bytes, was 10642 at base, +4559): temporal-scope header; P-04
  current-selection sentence (projects/memberships deferred; real exposure
  D2) and historical restore-drill label; P-06 M-LOCAL-PILOT-EVIDENCE
  supersession note; new M-INTERNET-UX-PILOT block with the exact eight
  human meanings mapped to SAR-039…SAR-047 (requirement 1 -> SAR-039 and
  SAR-040) and the bounded nine-slice draft sequence (runtime ->
  architecture -> proxy -> sharedabuse -> defaultpolicy -> landing/admin ->
  help -> themes -> finalqualification+freshICA), every future order marked
  DRAFT UNTIL STRATEGIC RECONCILIATION with no invented PR/SHA; deferred
  OIDC/projects/notifications/execution/scheduler/real-cutover scope and
  the M-EXTERNAL-PILOT/M-RELEASE D2 gates preserved, plus the clause that
  milestone development authorizes none of that gate.

**Criterion 2 — Projection compiled and coverage/measured context written.
PASSED.**
- `ARCHITECTURE-for-agents.md` final bytes SHA-256
  `1b271b2fa41c57126d7e47e6ec4f6155e07dd7e2bbc873fc0227a16476227175`
  (17328 bytes): header carries the current full-source SHA-256 identity
  (`06dd0f50…`) with the initial projection source SHA-256
  (`9e7c60e4…`) preserved as historical provenance; the stale
  "Current conversion is governance only" workflow-only claim is removed
  and replaced by the selected-target scope line; the stale "DRF3.16"
  baseline label is replaced by the current source constraint with the
  authoritative lock (3.17.2).
- All 47 stable requirements present. The original 38 clauses are
  byte-identical to the pre-order projection (verified programmatically,
  line-by-line: 38/38 unchanged); component routing is byte-identical; the
  Current API boundaries section gained only the A-15 "disabled by default
  and staff-only when enabled" clause for `/api/schema/` and `/api/docs/`;
  Verification cautions relabel the two baseline proof-gap observations as
  historical. The nine new clauses enforce the A-15 facets and are marked
  UNPROVEN (new milestone).
- New `docs/governance/INTERNET-UX-PROJECTION-REVIEW.md`
  (SHA-256 `2eb1aa7b296f402fd3ffb937ac06c9ba3c9bc35eb92364f94b04a2384655eb81`):
  A-15 obligation -> requirement ID -> compact clause mapping table (every
  A-15 normative paragraph mapped; every new ID mapped), explicit
  strategy-only decision list (8 items including human-only D2 items),
  measured context, and method/limitations. The generation-1 record
  (`docs/bootstrap/archive/CONTEXT-BUDGET.md`) is preserved unchanged and
  cited as the measurement convention (routine transitive coding read set
  excluding the active order and product code).
- Measured bytes (exact UTF-8, on the committed files):
  | File | Bytes | Ceiling |
  |---|---:|---:|
  | `AGENTS.md` | 1058 | 2048 |
  | `oap/coding-instructions/AGENTS.md` | 6403 | 12000 |
  | `ARCHITECTURE-for-agents.md` | 17328 | 20000 |
  | `OAP-COMMUNICATION-coding-agent.md` | 4105 | 10000 |
  | `oap/coding-instructions/SECURITY-CORE.md` | 1410 | — |
  | `oap/coding-instructions/TESTING-CORE.md` | 1947 | — |
  | **Total (excluding order/code)** | **32251** | **50000** |
  Projection alone 17328 <= 20000; read set 32251 <= 50000. Tokens:
  UNMEASURED (no qualified tokenizer; same convention as generation 1).
  The 032-a order file (22034 bytes) is order-scoped, outside the routine
  transitive set per the generation-1 convention.
- `docs/audit/ICA-PROTOCOL.md`: requirement scope now derived dynamically
  from the canonical index at the audited revision (2026-10-04 edition:
  SAR-001–SAR-047) instead of a hardcoded 38; rest of the fresh-audit
  protocol unchanged. `docs/audit/ICA-REQUIREMENT-MATRIX-TEMPLATE.md`:
  title and header relabel the 38-row matrix as a historical seed for its
  2026-09 baseline revision with a pointer to dynamic derivation; all 38
  existing rows and the final required-columns paragraph are preserved
  byte-identical.

**Criterion 3 — Diff allowlist and zero runtime byte change. PASSED.**
- `git status --porcelain` at implementation commit
  `6373aba6729ca94e5eabf79d65a2649c24f8de86` (first parent `3abe17d…`):
  exactly the 8 committed paths — 6 allowed documentation files (5
  modified + 1 new), `oap/orders/032-a-internet-ux-contract.md` (new,
  strategy bytes as-is), `oap/active` (pointer bytes as-is). No other
  tracked or untracked path changed; no file under `src/`, `tests/`,
  `deploy/`, `data/`, `.github/`, `pyproject.toml`, `uv.lock`, `Dockerfile`,
  `compose*`, `oap/governance/`, `oap/bin/`, `oap/coding-instructions/`,
  `oap/strategic-instructions/`, `docs/bootstrap/`, `docs/audit/reports/`,
  `docs/audit/requests/`, `oap/orders/` (other orders) or
  `oap/reports/` (prior reports) was touched. CRITICAL register untouched.
  Scripted allowlist check: 0 violations.
- No new framework, harness, test platform, dependency or lock change; no
  meaningless new tests for prose were added.

**Criterion 4 — Existing quality gates and standard five exact-head checks.
PASSED.**
- Local at the implementation bytes: `uv run ruff check .` -> All checks
  passed!; `uv run ruff format --check .` -> 186 files already formatted;
  `uv run mypy src` -> Success: no issues found in 119 source files;
  `git diff --check` -> clean; `uv run --env-file .env python
  manage.py check` -> 0 issues; `uv run --env-file .env python
  manage.py makemigrations --check --dry-run` -> No changes detected.
- Standard five checks at the exact implementation head
  `6373aba6729ca94e5eabf79d65a2649c24f8de86` (section 5): quality, test,
  security, container (CI run 37176857062) and oap-harness (oap run
  37176857071) all SUCCESS before this report was written. The unchanged
  product suite ran through the CI `test` job on real PostgreSQL 17
  (619 passed in 177.76 s), guarding preservation; it does not
  implement/qualify the new target. No dedicated markdown-links job exists
  in the current CI workflow (job list verified in
  `.github/workflows/ci.yml`); the A-15 "links" facet applies to future
  qualification rounds.

**Criterion 5 — DHA, claims and immutability. PASSED (to authoring).**
- `Decision: NONE` honored: no CRITICAL entry appended, no human
  disposition or gate clearance performed or implied, no D2 boundary
  crossed. No deployment, release, ICA, milestone-complete or
  physical-resource consequence claimed; SAR-039–SAR-047 remain initially
  UNPROVEN until a fresh isolated ICA at the exact merged revision.
- Normal immutable sequence: implementation commit (criterion paths only)
  -> push -> PR #64 created before this report -> exact-head checks
  observed -> literal full implementation head captured -> this report.
  Pending at authoring (not yet successful, not claimed as done): this
  report committed as the only changed file with the implementation head as
  first parent, push, remote verification, exact response OK, exit. No
  further mutation in this round after publication. Coding never merges.

## 3. Changed files and scope

Implementation commit `6373aba6729ca94e5eabf79d65a2649c24f8de86` (first
and only non-report commit of the round; 8 files, +603/−42; first parent
`3abe17d026d7ebfe402426afd89e30cdc6924f61`):
- `ARCHITECTURE.md` — +266/−23 (criterion 1 detail above).
- `PLAN.md` — +44/−4 (criterion 1 detail above).
- `ARCHITECTURE-for-agents.md` — +38/−11 (criterion 2; 38 original clauses
  byte-identical).
- `docs/governance/INTERNET-UX-PROJECTION-REVIEW.md` — new, +98.
- `docs/audit/ICA-PROTOCOL.md` — +4/−1.
- `docs/audit/ICA-REQUIREMENT-MATRIX-TEMPLATE.md` — +6/−2 (all 38 rows and
  the required-columns paragraph byte-identical).
- `oap/orders/032-a-internet-ux-contract.md` — new, strategy-published
  order bytes as-is (+146).
- `oap/active` — pointer bytes `032-a` + LF as-is (was `031-c`).

The report commit changes only
`oap/reports/032-a-internet-ux-contract.md` (new file), first parent
`6373aba6729ca94e5eabf79d65a2649c24f8de86`. No CRITICAL register or other
file is touched; no prior report was rewritten; no merged PR was mutated.

## 4. Commands and results (summary)

| Command (exact) | Result |
| --- | --- |
| `git rev-parse origin/main` / `git rev-parse HEAD` (before branch) | PASSED (both `3abe17d026d7ebfe402426afd89e30cdc6924f61` = order base_sha) |
| `sha256sum ARCHITECTURE.md PLAN.md` (at base) | PASSED (equal to order source_hashes `8483a070…` / `d03eb297…`) |
| `gh pr view 62` / `gh issue view 61` / `gh api …head_sha=065cf891…` | PASSED (PR62 MERGED; issue61 CLOSED; both runs success) |
| scripted allowlist over `git status --porcelain` | PASSED (0 violations; 8 committed paths all allowlisted) |
| `uv run ruff check .` | PASSED (All checks passed!) |
| `uv run ruff format --check .` | PASSED (186 files already formatted) |
| `uv run mypy src` | PASSED (no issues in 119 source files) |
| `git diff --check` | PASSED (clean) |
| `uv run --env-file .env python manage.py check` | PASSED (0 issues) |
| `uv run --env-file .env python manage.py makemigrations --check --dry-run` | PASSED (No changes detected) |
| projection clause preservation (programmatic line-by-line compare, 38 clauses + routing section) | PASSED (38/38 byte-identical; routing byte-identical) |
| `wc -c` read-set measurement (6 files) | PASSED (32251 <= 50000; projection 17328 <= 20000) |
| local full product suite | NOT RUN (not ordered for a governance-only round; no local full-suite success claimed; CI `test` job is the authoritative full result: 619 passed at the exact head) |
| exact-head CI (5 checks) | PASSED (section 5) |

Environment: uv-managed CPython 3.13 (repo venv). No database, container,
browser or network resource was used by any local step; only file digests,
git state and read-only GitHub API queries were performed locally.

## 5. CI observed before authoring

Observed at authoring time, at implementation head
`6373aba6729ca94e5eabf79d65a2649c24f8de86` (structured check/job data from
`gh run view`; headSha equality verified from the API):
- CI workflow run 37176857062 (`pull_request`, conclusion `success`):
  `quality` success (job 111361162593: uv sync --locked, ruff check, ruff
  format --check, mypy src, git diff --check), `test` success (job
  111361162400: `619 passed in 177.76s` on real PostgreSQL 17 plus
  Playwright chromium, including spectacular --validate --fail-on-warn and
  makemigrations --check), `security` success (job 111361162522: pip-audit
  and production-settings fail-closed check), `container` success (job
  111361162467).
- oap workflow run 37176857071 (`pull_request`, conclusion `success`):
  `oap-harness` success (job 111361162389).

Report-head CI is **NOT YET OBSERVED AT AUTHORING**: this report's own
publication commit postdates the observed head, and no check result at the
report commit is claimed here. Post-publication verification observations
belong to the private execution receipt (CP-07), not to this report.

## 6. Security, data, dependencies and local tools

- No credentials, verifiers, peppers, cookies, CSRF, Authorization data,
  raw payloads, private exports or physical locators were read, written or
  logged. No auth-home copying, no OS sidecars, no real exposure, no
  DNS/TLS/firewall change, no lab/Neumann/production contact, no real
  secrets or production data.
- No new dependency, no lock change, no application/domain/auth/policy/UI/
  migration/runtime-config/workflow/container byte changed; SAR-022
  preserved (stack unchanged); SAR-024 preserved (no exposure change —
  this round is documentation only); SAR-033 preserved (history, prior
  orders/reports, archives untouched); SAR-035 preserved (private
  infrastructure boundary respected; only the private development remote
  via the separately authorized Git publication); SAR-037 preserved
  (canonical sources changed by this order itself, projection hash-bound
  and coverage-mapped); SAR-038 preserved (no release/deployment/ICA
  claim).
- `Decision: NONE` honored: no CRITICAL entry appended, no human
  disposition or gate clearance performed or implied.
- No operational CLAUDE.md/Claude launcher was used or created.

## 7. DHA outcome and unresolved gates

Order declaration: `## Deferred human adjudication` / `- Decision: NONE`.
No CRITICAL entry was appended, no human disposition or gate clearance was
performed or implied, and no D2 boundary was crossed. The only outstanding
development gate is strategic review/development merge of PR #64, which
belongs to strategy. Real internet exposure, DNS/TLS/firewall, identity,
secrets and private data remain human D2; the development sequence in
PLAN P-06 stays DRAFT UNTIL STRATEGIC RECONCILIATION, and the milestone
M-INTERNET-UX-PILOT is selected, not complete.

## 8. Limitations and recommendation

- The order's strongest objection is addressed by construction: A-15 is
  authored as selected-target contract, every new row is
  `UNPROVEN (new milestone)`, the header and A-13/A-14 notes keep intent
  (target) distinct from evidence (point-in-time baseline observations,
  exact-report evidence, fresh ICA), and the original 38 IDs plus their
  source historical labels are preserved (38 projection clauses
  byte-identical; no A-01–A-14 section weakened). A fresh all-47 ICA is
  required before any qualification of this target; the old internal-pilot
  ICA cannot qualify it.
- Semantic mapping limitations: the nine new projection clauses are
  faithful compact statements of the A-15 facets; the full facet wording,
  Inspect/Evidence details and the obligation->ID->clause mapping live in
  root A-15/A-14 and in
  `docs/governance/INTERNET-UX-PROJECTION-REVIEW.md` (hash-bound to the
  full source), not in the routine read set. Strategy-only decisions
  (default-policy field values, proxy selection, abuse-control rates, HSTS
  opt-in, visual iteration, future order issuance, gthread-fix treatment,
  human D2 items) are listed explicitly there and were not decided by this
  round.
- Measured context uses the generation-1 convention (routine transitive
  coding read set excluding the active order and product code); tokens are
  UNMEASURED for lack of a qualified tokenizer. If a later round makes the
  active order part of a routine set, the ceiling arithmetic must be
  revisited by strategy, not by silent expansion.
- No dedicated markdown-links check exists in the current CI; the A-15
  links/pip-audit qualification applies to future rounds (pip-audit itself
  ran green in the security job at the exact head).
- Report-head CI is unobserved at authoring; a failure there routes to a
  strategy suffix, not an amendment of this report.
- No claim is made for later requirements or milestone readiness; this is
  a development merge candidate that records the selected target.
