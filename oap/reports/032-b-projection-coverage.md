<!-- OAP-META
{
 "kind": "report",
 "id": "032-b",
 "order_path": "oap/orders/032-b-projection-coverage.md",
 "order_sha256": "1b1e94656fae3bf123c0300b5cc209e8b1d499c972679fc9eb40befa12ce4b05",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 63,
 "pr_number": 64,
 "branch": "codex/63-oap-032-a-internet-ux-contract",
 "implementation_head": "277b0090637a35092a8a43da6c0e0c153717dcf2",
 "base_sha": "3abe17d026d7ebfe402426afd89e30cdc6924f61",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "277b0090637a35092a8a43da6c0e0c153717dcf2",
  "runs": [
   {"run_id": 37178374614, "workflow": "CI", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 37178374619, "workflow": "oap", "event": "pull_request", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 032-b report — preserve executor obligation facets (projection coverage)

Order digest: `1b1e94656fae3bf123c0300b5cc209e8b1d499c972679fc9eb40befa12ce4b05`
(committed `oap/orders/032-b-projection-coverage.md`, strategy-published order bytes as
found in the working tree; `state: FINAL`, `pr_mode: AMEND`, `previous_round: 032-a`,
`decision_class: D0`, `Decision: NONE`). Active pointer `oap/active` = `032-b` + LF
(verified by xxd: `3033 322d 620a`, 6 bytes).

Implementation head SHA: 277b0090637a35092a8a43da6c0e0c153717dcf2

Report publication commit: SELF

**Result: COMPLETE** — all six numbered acceptance criteria met. The round changes exactly
the three ordered documentation files and publishes the round bytes (order + active pointer)
on the same objective PR #64 (AMEND). Zero product, runtime, test, dependency, migration,
workflow, container, archived-snapshot, governance-law or ICA-report byte changed. The
previous 032-a report and order are immutable and untouched. SAR-039–SAR-047 remain
selected-target obligations, initially UNPROVEN until a fresh isolated ICA at the exact
merged revision; no control is claimed implemented and no D2 boundary was crossed.

## 1. Starting state and E-list reconciliation (verify, do not assume)

Ordered reads completed: root router -> `oap/coding-instructions/AGENTS.md` ->
`ARCHITECTURE-for-agents.md` -> `OAP-COMMUNICATION-coding-agent.md` -> exact active order
(pointer `oap/active` = `032-b` + LF ->
`oap/orders/032-b-projection-coverage.md`) -> `SECURITY-CORE.md` / `TESTING-CORE.md` ->
only the order's scoped subtree (the three ordered documentation files as committed, the
prior 032-a order/report, root A-15 and the relevant PLAN P-06 text). No wildcard,
source-book, future-draft or whole-roadmap loading. The wrapper had already consumed the
control wake-up; it was not consumed again.

Reconciliation before edit (remote/local, C-06; AMEND round b on objective issue 63):
- Local branch `codex/63-oap-032-a-internet-ux-contract` head = remote PR #64 head =
  `e149971c08ec813581130785c29e0a5124498857` (the frozen 032-a report commit). PR #64 is
  OPEN, unmerged, base `main`, mergeable. `origin/main` =
  `3abe17d026d7ebfe402426afd89e30cdc6924f61` = order `base_sha`. Same objective, same
  round branch, same PR across restart — no renumbering, no new PR.
- Source hashes verified against the order via `sha256sum` in this checkout before edit:
  `ARCHITECTURE.md` `06dd0f50e778b9843e2a709caa0ae1f0c97f48baee726f4e3a1397cc6a198d8c`,
  `PLAN.md` `c39f3f82b8493f751cb57388b46e4f61e1be1c82be1c9613ec09c3715634d0fc` (both
  equal to the order's `source_hashes`).
- E-list items independently re-observed: the 032-a frozen report commit
  `e149971c08ec813581130785c29e0a5124498857` is the remote PR #64 head with
  implementation commit `6373aba6729ca94e5eabf79d65a2649c24f8de86` as first parent; the
  032-a projection measured 17328 bytes (byte-verified via `wc -c` on the committed
  bytes). The order's claim that the 032-a clauses lacked explicit full-qualification/
  surface-inventory and several must/condition facets, and that the coverage record's
  qualification row mapped to the header classification rather than a verification
  clause, was confirmed by direct inspection (section 2).
- Working tree at start: branch head plus the ordered round bytes only — `oap/active`
  modified (`032-a` -> `032-b`) and untracked
  `oap/orders/032-b-projection-coverage.md`. No foreign/dirty files existed to preserve;
  no reset/clean/stash/force-push performed.

## 2. Acceptance evidence (ordered criteria)

**Criterion 1 — Explicit compact Selected target qualification clause. PASSED.**
New clause `Selected target qualification (A-15)` added to
`ARCHITECTURE-for-agents.md` after SAR-047 (final projection bytes section 3), carrying
directly: real unit/integration tests; PostgreSQL concurrency/rollback; browser HTTP
auth/CSRF/privacy; real Gunicorn positive plus old-sync negative; disposable Internet
HTTPS proxy; shared abuse controls; production-settings negatives; container/Compose/
health; fresh+upgrade policy init; default/custom branding; standard five exact-head
checks plus links/pip audit; exact source/revision/evidence statuses with no
mocked-boundary pass; the full browser-surface inventory (criterion 2); real Playwright
capture/view/iterate at ~1440/1024/768/390 desktop/mobile default/custom with mandatory
STRATEGIC visual review; durable semantic assertions; privacy-safe screenshots; no
brittle pixel CI unless stability proven; final fresh isolated full-architecture ICA over
all SAR-001..SAR-047 at the exact merged revision AFTER implementation; old internal
audit historical; bounded repair then FULL architecture-to-current-main re-audit (not
closed-findings-only review); human acceptance/release/D2 real resources separate;
product-first docs without ledger or public-production claims. The header now states
SAR-039..SAR-047 carry their executor-relevant conditions directly and root A-15 is
reference only (not a mandatory read).

**Criterion 2 — Compact all selected browser surfaces. PASSED.**
The qualification clause lists: anonymous landing/login/admin login; member
dashboard/assets list+detail/availability/reservation create+list+detail/profile/token
list+create; staff management/policy list+detail+form/blackout list+detail+form/
reservations/audit list+detail+export controls; admin index/user list+change/asset
list+change/relevant protected models — matching the A-15 qualification paragraph's
representative fixtures. The SAR-046 clause keeps the design system and points the
surface inventory at the qualification clause instead of restating it abstractly.

**Criterion 3 — Facet conditions preserved explicitly. PASSED.**
SAR-039..SAR-047 rows rewritten as compact explicit conditions (per-row "Enforce A-15"
prefixes and "UNPROVEN (new milestone)" filler removed; the existing header classification
— "SAR-039..SAR-047 are new A-15 facets, initially UNPROVEN until a fresh ICA at the exact
merged revision" — applies to all new rows): 039 adds normal HTTPS endpoint, Linux amd64,
Caddy-or-equivalent, private-loopback non-root app, private DB, never direct-Internet
Gunicorn, attacker-forwarding rejection, client IP/TLS normalization, debug off, safe
errors/headers/logs/health, docs/schema disabled-staff-only, HSTS deliberate opt-in,
administration on the same hardened boundary, configurable extras with no LAN assumption;
040 adds generous legitimate-agent throughput, cross-process coordination (no multiplied
per-process in-memory bounds), multi-process negative proof, proxy read/idle/body bounds;
041 adds explicit preservation of existing operator policies incl. deliberate inactive
configuration, no silent overwrite, reactivation support, dry-upgrade predictability and
visible/documented caps; 043 states the browser-only branding prohibition with technical
imports/docs allowed; 044 adds raw filters AND every editable field/non-obvious choice
with actually-rendered accessible help; 045 adds primary/compact logo, favicon where
practical, CSS-after-defaults, safe fallback; 046 names the exact CURRENT reference URLs
(slaif.si/doc.slaif.si/edu.slaif.si/trainings) with local-packaged assets and no
runtime-critical hotlinking; 047 adds preserve-foreign-fix-or-reproduce-before-change,
six idle/slow held clients with bounded /health/live and login, old-sync sensitivity,
owned cleanup, proxy rationale, and records PR62 as independently reproduced and
remediated (evidence indexed, not future work or a new ICA). A scripted presence check
verified every mandated condition string appears in the final projection (0 failures).

**Criterion 4 — Ceilings, coverage record, digests, strategy-only decisions. PASSED.**
- Measured on the final working-tree bytes: projection 19982 <= 20000 (ceiling holds;
  headroom 18); routine transitive read set 34905 <= 50000 (AGENTS.md 1058 +
  oap/coding-instructions/AGENTS.md 6403 + projection 19982 +
  OAP-COMMUNICATION-coding-agent.md 4105 + SECURITY-CORE 1410 + TESTING-CORE 1947);
  conservative wider sum (projection + PLAN.md + review = 19982 + 15523 + 12353) = 47858
  <= 50000. No normative law truncated; no hidden mandatory link introduced (root A-15 is
  reference-only; the only internal cross-reference is projection-internal, SAR-046 ->
  the qualification clause). Tokens UNMEASURED (no qualified tokenizer; same convention).
- `docs/governance/INTERNET-UX-PROJECTION-REVIEW.md` updated: qualification facet now
  maps to the new `Selected target qualification (A-15)` clause (header-only mapping
  removed); projection digest updated to
  `09d2157df1a57a312071f818fcb2600bee65abce213aa268f657fb67ab3b3cf3`, PLAN digest to
  `b19219e2d727af5a9554e011ba45a786f1bb61f25c001011fc18006cae665d08`; canonical full-
  source SHA-256 carried unchanged from 032-a (`06dd0f50…`), not a hash rewrite; byte
  table and semantic limitations updated; header records 032-b as a strategic second
  pass, not an ICA.
- Strategy-only decision list: item 7 (whether PR62 is the "foreign fix") removed as
  resolved — the bounded search found no foreign Gunicorn fix in the repository; the old
  sync starvation was independently reproduced and remediated by 031-a/PR62, merged on
  main; preserve any foreign fix if later found. The remaining items are labeled
  properly scoped future D0 decisions decided only when their objective is strategy-
  issued.

**Criterion 5 — PLAN bounded sequence and M-LOCAL truth. PASSED.**
`PLAN.md` P-06 corrected: (a) sequence row 1 runtime now records the threaded Gunicorn
baseline as delivered by merged PR62 (031-a) on main, not future backlog, with the
remaining SAR-047 consistency facets swept in the final qualification line; (b) row 2 is
renamed "architecture contract" and scoped documentation-only (this PR) with an explicit
non-authorization of deployment/configuration changes; (c) row 3 is renamed "proxy +
production security" and now owns the deployment configuration (Compose, allowed hosts/
CSRF origins, private docs/schema, fail-closed production settings) for a future order;
(d) the preamble marks all future orders DRAFT UNTIL STRATEGIC RECONCILIATION with live
authority, code controls UNPROVEN until the later fresh ICA, no new feature
implementation claimed; (e) M-LOCAL-PILOT-EVIDENCE keeps the bootstrap-date annotation
and now states the old controlled-internal alpha work is implemented and audited, with
report `docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-a9c3133.md` (file existence verified)
historical and superseded by the selected target, not available as queued replay, and no
human milestone acceptance inferred from its audit counts. Sequence is otherwise
unchanged (rows 4-9 byte-identical).

**Criterion 6 — Verification, immutable sequence, claims. PASSED.**
- Semantic comparison: clause-by-clause against root A-15/A-14 facets performed
  deliberately (section 2 criteria 1-3); the scripted facet-presence check found all
  mandated condition strings. No mirror implementation tests were added for prose.
- Old-38 byte identity: programmatic line comparison of the committed 032-a projection
  against the final bytes: 38/38 SAR-001..SAR-038 clauses byte-identical; Component
  routing, Current API boundaries and Verification cautions sections intact; the only
  non-clause text movement is the header scope reflow (intentional).
- Link check: internal document references in the changed files exist
  (`docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-a9c3133.md`,
  `docs/bootstrap/archive/CONTEXT-BUDGET.md`, `docs/audit/ICA-PROTOCOL.md`,
  `docs/audit/ICA-REQUIREMENT-MATRIX-TEMPLATE.md`, `ARCHITECTURE.md`); the pre-existing
  `SOURCE-MAP.md` reference in P-07 resolves to
  `docs/bootstrap/1/inputs/SOURCE-MAP.md` (unchanged, not introduced by this round);
  slaif.si/doc.slaif.si/edu.slaif.si/trainings are external design references, not
  verifiable offline, and remain reference-only.
- Local quality gates at the implementation bytes (section 4 table): ruff check, ruff
  format --check, mypy, git diff --check, manage.py check, makemigrations --check all
  PASSED.
- Standard five exact-head checks at implementation head
  `277b0090637a35092a8a43da6c0e0c153717dcf2` (section 5): quality, test, security,
  container (CI run 37178374614) and oap-harness (oap run 37178374619) all SUCCESS
  before this report was written. The unchanged product suite ran through the CI `test`
  job on real PostgreSQL 17 (619 passed in 174.84 s), guarding preservation; it does not
  implement/qualify the new target. pip-audit ran green in the `security` job; no
  dedicated markdown-links CI job exists (032-a observation still valid), so the links
  facet is evidenced here by the file-existence check above.
- Immutable sequence: AMEND round b reused objective issue 63 / branch / PR #64; the
  032-a order and report bytes are untouched; the implementation commit changes only the
  five ordered paths; this report is committed as the only changed file with the
  implementation head as first parent. Pending at authoring (not claimed as done): push,
  remote verification, exact response OK, exit. No further mutation in this round after
  publication. Coding never merges.

## 3. Changed files and scope

Implementation commit `277b0090637a35092a8a43da6c0e0c153717dcf2` (first parent
`e149971c08ec813581130785c29e0a5124498857`; 5 files, +172/-46):
- `ARCHITECTURE-for-agents.md` — 17328 -> 19982 bytes (criterion 1-3, 4).
- `PLAN.md` — 15201 -> 15523 bytes (criterion 5).
- `docs/governance/INTERNET-UX-PROJECTION-REVIEW.md` — 10191 -> 12353 bytes (criterion 4).
- `oap/orders/032-b-projection-coverage.md` — new, strategy-published order bytes as-is
  (SHA-256 `1b1e94656fae3bf123c0300b5cc209e8b1d499c972679fc9eb40befa12ce4b05`).
- `oap/active` — pointer bytes `032-b` + LF as-is (was `032-a`).

No file under `src/`, `tests/`, `deploy/`, `data/`, `.github/`, `pyproject.toml`,
`uv.lock`, `Dockerfile`, `compose*`, `oap/governance/`, `oap/bin/`,
`oap/coding-instructions/`, `oap/strategic-instructions/`, `docs/bootstrap/`,
`docs/audit/reports/`, `docs/audit/requests/`, `oap/orders/` (other orders) or
`oap/reports/` (prior reports) was touched; `ARCHITECTURE.md` unchanged (SHA-256
`06dd0f50e778b9843e2a709caa0ae1f0c97f48baee726f4e3a1397cc6a198d8c` re-verified after
edit). CRITICAL register untouched.

## 4. Commands and results (summary)

| Command (exact) | Result |
| --- | --- |
| `sha256sum ARCHITECTURE.md PLAN.md` (before edit) | PASSED (equal to order source_hashes `06dd0f50…` / `c39f3f82…`) |
| `git rev-parse origin/main` / PR #64 head via `gh pr view 64` | PASSED (base = `3abe17d…`; PR head = local head `e149971…`; PR OPEN, unmerged, mergeable) |
| `xxd oap/active` | PASSED (`3033 322d 620a`, 6 bytes = `032-b` + LF) |
| `sha256sum oap/orders/032-b-projection-coverage.md` | PASSED (`1b1e9465…`) |
| clause-level replacement script (each old string found exactly once) | PASSED (all 5 files' intended edits; 0 accidental replacements) |
| programmatic old-38 clause comparison vs committed 032-a bytes | PASSED (38/38 byte-identical; sections intact) |
| scripted facet-presence check (criterion 1-3 condition strings) | PASSED (0 failures) |
| internal link/file-existence check | PASSED (all internal refs exist; external references noted) |
| `wc -c` ceiling measurements (post-edit, pre-commit) | PASSED (projection 19982 <= 20000; read set 34905 <= 50000; wider sum 47858 <= 50000) |
| `uv run ruff check .` | PASSED (All checks passed!) |
| `uv run ruff format --check .` | PASSED (186 files already formatted) |
| `uv run mypy src` | PASSED (no issues in 119 source files) |
| `git diff --check` | PASSED (clean) |
| `uv run --env-file .env python manage.py check` | PASSED (0 issues) |
| `uv run --env-file .env python manage.py makemigrations --check --dry-run` | PASSED (No changes detected) |
| local full product suite | NOT RUN (not ordered for a governance-only round; no local full-suite success claimed; CI `test` job is the authoritative full result: 619 passed at the exact head) |
| exact-head CI (5 checks) | PASSED (section 5) |

Environment: uv-managed CPython 3.13 (repo venv). No database, container, browser or
external network resource was used by any local step; only file digests, git state and
read-only GitHub API queries were performed locally.

## 5. CI observed before authoring

Observed at authoring time, at implementation head
`277b0090637a35092a8a43da6c0e0c153717dcf2` (structured check/job data from `gh run
view`; headSha equality verified from the API):
- CI workflow run 37178374614 (`pull_request`, conclusion `success`):
  `quality` success (job 111365684087), `test` success (job 111365684266:
  `619 passed in 174.84s` on real PostgreSQL 17), `security` success (job
  111365684243, pip-audit and production-settings fail-closed check), `container`
  success (job 111365684251).
- oap workflow run 37178374619 (`pull_request`, conclusion `success`):
  `oap-harness` success (job 111365684004).

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
  the separately authorized Git publication); SAR-037 preserved (canonical PLAN changed
  by this order itself, projection hash-bound and coverage-mapped, full source
  unchanged); SAR-038 preserved (no release/deployment/ICA claim).
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

- The order's strongest objection (compact detail inflating context while still losing
  conditions) is addressed by construction: the explicit facet conditions, the
  qualification clause with the surface inventory, the measured byte ceilings (all
  within limits with margin) and the clause-level byte-identity proof for the old 38
  rows. The projection is still a condensation — the full facet wording remains in root
  A-15 (reference only) and in the coverage mapping, which is the designed division of
  labor, not a gap.
- This is a strategic second pass, not an ICA: SAR-039–SAR-047 remain initially UNPROVEN;
  no runtime behavior was exercised for the new target beyond the unchanged product
  suite guarding preservation.
- Measured context uses the generation-1 convention (routine transitive coding read set
  excluding the active order and product code); tokens are UNMEASURED for lack of a
  qualified tokenizer. The conservative wider sum (projection + PLAN + review = 47858
  bytes) is recorded for transparency even though it is outside the routine set.
- No dedicated markdown-links CI job exists; the links facet is evidenced by the
  internal file-existence check. pip-audit itself ran green in the security job at the
  exact head.
- Report-head CI is unobserved at authoring; a failure there routes to a strategy
  suffix, not an amendment of this report.
- No claim is made for later requirements or milestone readiness; PR #64 (now carrying
  both 032-a and 032-b) remains a development merge candidate that records the selected
  target.
