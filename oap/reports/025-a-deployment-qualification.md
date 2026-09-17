<!-- OAP-META
{
 "kind": "report",
 "id": "025-a",
 "order_path": "oap/orders/025-a-deployment-qualification.md",
 "order_sha256": "2e4ed0e4a03da4ea3cb810e42c8ccd8ea82aecaaa9db8a0bf2268220192932b4",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 49,
 "pr_number": 50,
 "branch": "codex/49-oap-025-a-deployment-qualification",
 "implementation_head": "ccd11d17228aeaacbfd343f33659bb753c027c53",
 "base_sha": "e94d95e985412f9fc2fa27508be6ae36d606c4ce",
 "result": "PARTIAL",
 "observed_implementation_ci": {
  "observed_head": "ccd11d17228aeaacbfd343f33659bb753c027c53",
  "runs": [
   {"run_id": 35172972425, "workflow": "CI", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success", "deployment-rehearsal": "skipped (event-gated by design)"}},
   {"run_id": 35172972426, "workflow": "oap", "event": "pull_request", "jobs": {"oap-harness": "success"}},
   {"run_id": 35172286354, "workflow": "CI", "event": "workflow_dispatch", "jobs": {"quality": "success", "security": "success", "container": "success", "test": "failure (pre-existing oap-harness FIFO-journaling flake; 610 passed, 1 failed)", "deployment-rehearsal": "skipped (ordered if-condition evaluated false; candidate concern, section 7)"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 025-a report — Deployment qualification: document truth, image reproducibility, opt-in full-rehearsal CI

Order digest: `2e4ed0e4a03da4ea3cb810e42c8ccd8ea82aecaaa9db8a0bf2268220192932b4`
(committed `oap/orders/025-a-deployment-qualification.md`; the materialized
`.FINAL` source was moved to the canonical name with `mv` before committing,
byte-identical, as in every prior round; `sha256sum` of the committed file:
`2e4ed0e4a03da4ea3cb810e42c8ccd8ea82aecaaa9db8a0bf2268220192932b4`).

Implementation head SHA: ccd11d17228aeaacbfd343f33659bb753c027c53

Report publication commit: SELF

**Result: PARTIAL** — all ordered implementation work is complete, pushed, and
evidenced locally and in CI at the exact implementation head: the 11
document-truth fixes, the INSTALL.md section-2 architecture statement, the
PostgreSQL digest pins in all three places, and the opt-in
`workflow_dispatch` + `deployment-rehearsal` job. The four standard CI jobs are
green at the implementation head with head_sha verified (run 35172972425), and
the oap-harness is green (run 35172972426). PARTIAL because criterion 7's
dispatch half did not produce the ordered "end-to-end proof of the new job":
in the exactly-one permitted `workflow_dispatch` run (35172286354, head
verified), the `deployment-rehearsal` job was **skipped** under the exact
ordered `if` bytes triggered by the exact ordered command (root-cause
candidates and alternatives reported to strategy in section 7 — coding does
not adjudicate or alter ordered `if` bytes), and the same run's `test` job hit
a pre-existing oap-harness FIFO-journaling flake (out of scope: `tests/`
forbidden this round). The full rehearsal was instead proven end-to-end
locally at the exact implementation bytes (section 6). No product bytes, no
src/, no tests/, no dependency, no Dockerfile, no migration, no OAP-machinery
change. No deployment was performed. No merge.

## 1. Documentation-drift table (acceptance criterion 1)

All 11 ordered fixes (Scope 1–8), verified line-by-line against base
`e94d95e985412f9fc2fa27508be6ae36d606c4ce` before editing (every E-list line
matched; no STOP condition):

| # | File | Base line | Exact old text | Exact new text |
|---|------|-----------|----------------|----------------|
| 1 | README.md | 12 | `OAP objectives 015-a through 023-a` | `OAP objectives 015-a through 024-a` |
| 2 | docs/roadmap.md | 190 | `objectives 015-a through 023-a have been implemented` | `objectives 015-a through 024-a have been implemented` |
| 3 | docs/roadmap.md | 209–211 | `Current human selection: the canonical installation/deployment documentation cleanup` + `(objective 024-a, current), then the first real internal-alpha deployment, human-authorized and` + `performed per \`INSTALL.md\`. The slice after that remains human-selected.` | `Current human selection (2026-09-17): objective 024-a (the canonical installation/deployment documentation cleanup) is complete; the current selection is deployment qualification for the first controlled internal-alpha Docker deployment (objective 025-a and the independent closure audit that follows), then the first real internal-alpha deployment, human-authorized and performed per \`INSTALL.md\`. The slice after that remains human-selected.` |
| 4 | PLAN.md | 56 | `Django5.2/DRF3.16` | `Django5.2/DRF3.17` |
| 5 | PLAN.md | 60 | `are in ARCHITECTURE.md and specifications/REQUIREMENTS.json.` | `are in ARCHITECTURE.md (SAR index, SAR-001 through SAR-038).` |
| 6 | SECURITY.md | 5 | `The project is in pre-alpha/bootstrap stage and is not approved for production use.` | `The project is in internal-alpha stage and is not approved for production use.` |
| 7 | docs/human-ui.md | 3 | `internal pre-alpha human MVP` | `internal-alpha human MVP` |
| 8 | docs/api-contract.md | 3 | `pre-alpha implementation contract` | `internal-alpha implementation contract` |
| 9 | docs/audit/ICA-PROTOCOL.md | 27 | `Materialize templates/request drafts and a complete initial matrix from specifications/REQUIREMENTS.json.` | `Materialize templates/request drafts and a complete initial matrix from the ARCHITECTURE.md SAR requirement index (SAR-001 through SAR-038).` |
| 10 | ARCHITECTURE.md | 66 (A-03) | `` `>=3.16,<3.17` `` | `` `>=3.16,<3.18` `` |
| 11 | ARCHITECTURE.md | 526 (SAR-022 body) | `DRF3.16` | `DRF3.17` |

No current-state document changed beyond these: `git diff --name-only
e94d95e..ccd11d1` lists exactly the 12 allowed product/config files plus the
round bytes (`oap/orders/025-a-deployment-qualification.md`, `oap/active`);
`git diff ccd11d1 --stat` against the forbidden sets (docs/bootstrap,
docs/work-orders, docs/decisions, STATUS.md, docs/project-handoff.md,
docs/discovery-brief.md, Dockerfile, pyproject.toml, uv.lock, src, tests,
data, .github/workflows/oap.yml, oap machinery) is empty. Historical E-list
files proven byte-identical by `git diff --quiet` (all UNCHANGED:
docs/discovery-brief.md, docs/work-orders/0001-application-scaffold.md,
docs/decisions/0001-django-modular-monolith.md, STATUS.md,
docs/project-handoff.md, docs/bootstrap/1/inputs/PLAN.md, Dockerfile,
pyproject.toml, uv.lock).

## 2. ARCHITECTURE.md (acceptance criterion 2)

Exactly the two ordered token fixes (the file's `git diff` contains precisely
two single-line hunks: A-03 line 66 `` `>=3.16,<3.17` `` → `` `>=3.16,<3.18` ``,
matching pyproject.toml:10 `djangorestframework>=3.16,<3.18`; SAR-022 line 526
`DRF3.16` → `DRF3.17`, matching uv.lock `djangorestframework 3.17.2` /
`django 5.2.17`). No rewording, no structure change, no new content.

Post-change SHA-256 of ARCHITECTURE.md:
`182d9cf924931e846bc7965a079482b6753de762af807196ca0b87f8dffdf863` — recorded
as the input to the next round's (026-a) ICA request, per the order's I-list.

Harness impact verified before editing: `tests/oap/fixture_digests.py`
asserts `INPUT_DIGESTS` only against archived snapshots under
`docs/bootstrap/1/inputs/` (tests/oap/test_ba01_inputs.py); the `ARCH_SHA`
constant is defined but not asserted against the live ARCHITECTURE.md by any
test (grep-verified). The oap-harness is green at the implementation head
(run 35172972426), confirming no harness impact.

## 3. INSTALL.md (acceptance criterion 3)

Changed only in section 2 (Prerequisites); the file diff shows exactly two
hunks, both inside section 2:

- Added one bullet (after "A Linux host."): supported host architecture
  Linux, x86_64 (amd64) only; application runtime image built from
  `python:3.13-slim` pinned to a linux/amd64 digest in the `Dockerfile`;
  PostgreSQL service image pinned to a linux/amd64 digest in the Compose
  files; other architectures (for example arm64) not supported or verified
  for the documented deployment path.
- Updated the outbound-connectivity bullet: no longer implies `postgres:17`
  is pulled as a floating tag; now states the PostgreSQL service image is
  pinned by digest in the Compose files.

No other INSTALL.md byte changed.

## 4. Postgres digest pinning (acceptance criterion 4)

Resolution command: `docker buildx imagetools inspect postgres:17`,
cross-checked with `docker manifest inspect postgres:17` (both agree):

- Index: `docker.io/library/postgres:17`
  (`sha256:67f41722b7a8cbdb868a44a4995c846eddfdc2973bccb291ce937dce88ad5675`)
- Chosen linux/amd64 manifest digest:
  `sha256:d13db94ae661d517c5ed57c509a578d5ea64aae639871ba25294f4f42d83de28`
- Tag resolves to PostgreSQL **17.11** (annotation
  `org.opencontainers.image.version: 17.11`; created 2026-08-25; base
  debian:trixie-slim) — confirmed live: the pinned image was pulled and the
  rehearsal DB and a disposable test-DB container both reported
  `PostgreSQL 17.11 (Debian 17.11-1.pgdg13+2)`.

The SAME digest is present in all three places: `compose.yaml` line 3
(`image: postgres:17@sha256:d13db94ae661d517c5ed57c509a578d5ea64aae639871ba25294f4f42d83de28`),
`compose.production.example.yaml` line 3, and the ci.yml test service
(line 29 → `postgres:17@sha256:d13db94ae661d517c5ed57c509a578d5ea64aae639871ba25294f4f42d83de28`).

`docker compose config` — OK (compose.yaml); `docker compose -f
compose.production.example.yaml config` — OK (production-shaped rendered,
`required: false` env file absent as expected pre-deployment).

## 5. .github/workflows/ci.yml (acceptance criterion 5)

Exactly the three ordered changes (the file diff contains exactly three
hunks; the four pre-existing jobs are byte-identical apart from the test
service image pin):

1. Test service image pin (section 4 digest).
2. `on:` gains `workflow_dispatch` with one boolean input
   `run_full_rehearsal` (default true, description: "Run the full
   production-shaped deployment rehearsal (opt-in, used at deployment-gate
   time)").
3. One new job `deployment-rehearsal` (name: deployment-rehearsal) with
   `if: github.event == 'workflow_dispatch' && inputs.run_full_rehearsal`,
   `runs-on: ubuntu-24.04`, steps: `actions/checkout@v4` then
   `deploy/rehearse_internal_alpha_deployment.sh` (no flags).

YAML-parse clean (`yaml.safe_load`; triggers `pull_request`, `push`,
`workflow_dispatch` with the input parsed as boolean default true; jobs
`quality`, `test`, `security`, `container`, `deployment-rehearsal` with the
`if` and steps exactly as specified). `bash -n
deploy/rehearse_internal_alpha_deployment.sh` clean (script unchanged, mode
100755 preserved). The "not on pull_request/push" requirement is proven by
observation: in the PR-event run 35172972425 the job concluded `skipped`
while all four standard jobs ran.

## 6. Local evidence at the implementation head (acceptance criterion 6)

Environment: local dev host, Docker Engine 29.1.3 + Compose v2 2.40.3;
disposable owned test container `slaif-025a-testdb` (loopback-only
127.0.0.1:54330, matching `.env`, built from the pinned digest) created for
the suite and removed afterwards.

- `uv sync --locked --all-groups` — PASSED ("Resolved 71 packages").
- `uv run ruff check .` — PASSED ("All checks passed!").
- `uv run ruff format --check .` — PASSED ("185 files already formatted").
- `uv run mypy src` — PASSED ("Success: no issues found in 119 source files").
- `uv run --env-file .env python manage.py check` — PASSED ("System check
  identified no issues (0 silenced).").
- `uv run --env-file .env python manage.py makemigrations --check
  --dry-run` — PASSED ("No changes detected").
- `uv run --env-file .env pytest
  --ds=slaif_reservation.config.settings.test` — 610 passed, 1 failed in
  191.86s. The single failure is a session-environment artifact, not a code
  defect: this CODING session's environment carries `OAP_ROLE=CODING`, which
  the harness CLI subprocesses inherit; `test_ba39_strategic_same_prerequisites`
  simulates a STRATEGIC launch and the wrapper correctly refuses
  ("conflicting OAP_ROLE=CODING; refusing"). With `OAP_ROLE` unset the same
  suite is fully green (next item). CI runners do not set `OAP_ROLE`; the
  same test is green in run 35172972426 (oap-harness) and its sibling
  `test_ba26` is green in run 35172972425's pytest (611 passed).
- `env -u OAP_ROLE python3 -m unittest discover -s tests/oap -p 'test_*.py'`
  — PASSED: "Ran 154 tests in 35.257s / OK".
- `uv run pip-audit` — PASSED ("No known vulnerabilities found").
- `uv run --env-file .env python manage.py migrate --noinput` (on the
  disposable test DB) then `... manage.py operational_check` — PASSED
  ("database=ok, migrations=ok, static=ok, bootstrap=ok,
  idempotency_cleanup_command=ok, operational_check=ok").
- `uv run --env-file .env python manage.py spectacular --file
  build/openapi/schema.yaml --validate --fail-on-warn` — PASSED.
- `git diff --check` — PASSED (clean).
- **FULL rehearsal** `deploy/rehearse_internal_alpha_deployment.sh` (no flag)
  at the implementation bytes — PASSED: exit 0; log shows sanitized
  bootstrap import (mode=dry-run, planned=47, created=47, excluded=1,
  conflicted=0), `operational_check=ok`, OpenAPI validation, app start,
  `health_and_login=ok`, `anonymous_manage_redirect=ok`,
  `api_auth_failure=ok`, final line `rehearsal: rehearsal=ok`.
- Self-cleanup verified: post-run `--status` → "rehearsal: no
  rehearsal-owned projects found" (exit 0); `deploy/env.production` absent;
  `deploy/secrets` absent; host port 18080 free; `deploy/` contains only the
  tracked files (Caddyfile.example, env.production.example,
  rehearse_internal_alpha_deployment.sh).

## 7. CI at the exact implementation head (acceptance criterion 7)

All runs below verified from the GitHub API with `head_sha` =
`ccd11d17228aeaacbfd343f33659bb753c027c53` (the implementation head):

- **Run 35172972425 (CI, pull_request, PR #50, run 88): success.** Jobs:
  quality success, test success (3m14s — full 611-test suite), security
  success, container success; deployment-rehearsal **skipped** (event-gated
  by design on pull_request). This satisfies "the four standard jobs all
  green with head_sha verified".
- **Run 35172972426 (oap, pull_request, run 42): success.** oap-harness
  success (154 tests).
- **Run 35172286354 (CI, workflow_dispatch, run 87): failure** — triggered
  exactly once, per the order, with the exact ordered command
  `gh workflow run ci.yml -f run_full_rehearsal=true --ref
  codex/49-oap-025-a-deployment-qualification`. Jobs: quality success,
  security success, container success, **test failure** at `uv run pytest`:
  single failure
  `tests/oap/test_ba26_27_40_41_wrapper.py::Ba26ZeroIdle::test_ba26_consumption_journalized`
  — `AssertionError: 'invoked' not found in ['control_consumed']` (610
  passed, 1 failed, 108.84s). **deployment-rehearsal: skipped** (zero steps
  executed; condition evaluated false at run start, 2026-09-17T01:53:31Z).

Candidate concern A — `deployment-rehearsal` skipped under the ordered
bytes. The job uses exactly the ordered condition `if: github.event ==
'workflow_dispatch' && inputs.run_full_rehearsal` and the run used exactly
the ordered trigger command; the remote workflow bytes were verified
identical to the committed file. Per GitHub's documented expression coercion
(falsy: false/0/-0/""/''/null; everything else truthy) the string `"true"`
is truthy, and GitHub's own contexts documentation shows
`if: ${{ inputs.perform_deploy }}` as the pattern for manually triggered
workflows — so under those semantics the job should have run. The skip is
consistent with either (a) the CLI field not reaching the run's `inputs`
context, or (b) GitHub's long-documented string-typed dispatch-input
semantics (actions/runner#1483, where the robust pattern is
`inputs.x == 'true'`). Dispatch input values are not exposed by the
public REST/GraphQL API, so the root cause cannot be isolated from the
available surface without a second trigger — which the order forbids
("exactly one workflow_dispatch run"). **Coding does not adjudicate and did
not alter the ordered `if` bytes.** Alternatives for strategy/human:
(i) re-trigger via the GitHub web UI checkbox (isolates CLI-field delivery);
(ii) a strategy amendment to the `if` (e.g. explicit
`inputs.run_full_rehearsal == 'true'`); (iii) both, then a fresh
order-suffixed round re-runs the single dispatch. Meanwhile the new job's
steps were proven end-to-end locally at the exact implementation bytes
(section 6: full rehearsal exit 0, rehearsal=ok, self-clean), and its
event-gating was proven by observation on the PR event (skipped in run
35172972425).

Candidate concern B — pre-existing oap-harness FIFO-journaling flake. The
dispatch run's `test` job failure is a race in
`test_ba26_consumption_journalized` (the polling loop exits as soon as
`control_consumed` is journaled, before the wrapper writes the `invoked`
event — same flake family as round 023-a's FIFO write fix). Not caused by
this diff (no `oap/bin` or `tests/` bytes changed; the test passed 154/154
locally in a clean environment, and is green in both PR-event runs 35172972425
and 35172972426 at the same head). `tests/` is forbidden in this round, so no
fix was made; a dedicated order is needed to harden the test.

## 8. Implementation diff scope (acceptance criterion 8)

`git diff --name-status e94d95e..ccd11d1` (implementation head vs base)
touches exactly: README.md, PLAN.md, SECURITY.md, ARCHITECTURE.md,
INSTALL.md, compose.yaml, compose.production.example.yaml,
docs/roadmap.md, docs/human-ui.md, docs/api-contract.md,
docs/audit/ICA-PROTOCOL.md, .github/workflows/ci.yml (the 12 allowed
product/config files) plus round bytes oap/orders/025-a-deployment-
qualification.md (new) and oap/active (new). No src/, tests/, dependency,
Dockerfile, migration, or OAP-machinery change (proven empty diff against
those paths).

## 9. PR (acceptance criterion 9)

PR **#50** opened (base main, head
`codex/49-oap-025-a-deployment-qualification` = implementation head, not
draft). The description contains: why each change group is needed, the
drift table (section 1), the digest-resolution evidence (section 4), the
workflow_dispatch run evidence with per-job outcomes and the two candidate
concerns (section 7), the exact local verification results (section 6), and
the remaining blockers before a real internal-alpha deployment in truthful
language (CI-green candidate at best; real deployment not yet evidenced
anywhere; deployment remains human-authorized and performed per
INSTALL.md).

## 10. DHA outcome (acceptance criterion 10)

Decision: NONE. No CRITICAL.md entry was appended or altered; no human
disposition or gate clearance was performed.

## Changed files and scope

See section 8. The final report commit changes only this report file, with
the implementation head `ccd11d17228aeaacbfd343f33659bb753c027c53` as first
parent.

## Security, data, dependencies and local tools

No secrets, verifiers, peppers, credentials, or private data entered Git,
this report, or logs. The rehearsal used only its own synthetic git-ignored
values (created and removed by the script; verified absent after the run).
The disposable test-DB container used a local synthetic password matching
`.env` and was removed after the suite. No real deployment, DNS/TLS,
public exposure, lab/Neumann/production contact, or real export. No
dependency changes (uv.lock byte-identical). Local tools: Docker Engine
29.1.3, Docker Compose v2 2.40.3 (both pre-existing), gh CLI (read + the three
ordered publication operations: branch push, PR open, one workflow_dispatch
trigger). No OS sidecars.

## CI observed before authoring

See section 7. Report-head CI is NOT YET OBSERVED AT AUTHORING: this report
commit becomes the new PR head, and its checks have not run (and are not
claimed) at authoring. Later publication verification goes to the private
execution receipt, not to a report rewrite.

## Limitations and recommendation

- The `deployment-rehearsal` CI job has not yet run on CI under any
  observed configuration (skipped in the only permitted dispatch run;
  event-gated off on PR/push). Gate-time CI proof of the job awaits the
  candidate-concern adjudication (section 7, concern A); local
  end-to-end rehearsal evidence at the exact implementation bytes stands
  in the meantime.
- The oap-harness flake (concern B) remains a latent CI flake risk for the
  `test` job; hardening it requires a dedicated order (tests/ scope).
- This PR is development acceptance of qualification inputs only. It is not
  deployment, not release, and not a milestone acceptance; the real
  internal-alpha deployment remains human-authorized per INSTALL.md.

## Deferred human adjudication

- Decision: NONE
