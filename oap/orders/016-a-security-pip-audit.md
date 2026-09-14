<!-- OAP-META
{
 "id": "016-a",
 "round": "a",
 "base_sha": "34fd6edeaad865d96e495cd10f78e84aabfad626",
 "issue_number": 31,
 "branch": "codex/31-oap-016-a-security-pip-audit",
 "pr_mode": "CREATE_OR_RESUME",
 "previous_round": null,
 "allowed_paths": [
  "pyproject.toml",
  "uv.lock",
  "src/",
  "tests/",
  "oap/orders/016-a-security-pip-audit.md",
  "oap/active",
  "oap/reports/016-a-security-pip-audit.md"
 ],
 "forbidden_resources": [
  "any dependency change beyond the four affected packages (django, djangorestframework, pip, sqlparse) and their unavoidable transitive consequence",
  "new dependencies or removed dependencies",
  "product behavior, API, model, migration, template or settings changes except strictly required compatibility fixes (see criterion 7)",
  ".github/workflows, Dockerfile, compose files, deploy/, data/, docs/",
  "production databases, real lab/Neumann machines, real SmartScheduling data",
  "credentials, auth files, sessions, tokens, auth homes",
  "DNS/TLS/firewall changes, public exposure, repository visibility or branch-protection changes",
  "any mutating GitHub operation except pushing this branch and opening this objective's PR",
  "merging or auto-merging any PR (merge is strategy's delegated act after review)",
  "model provider endpoints other than the configured qwen-neumann role profile"
 ]
}
-->

# 016-a — Clear the pip-audit findings: minimal dependency upgrades

## Goal

Make the security CI job pass by applying the smallest compatible dependency
upgrades that clear the four known package findings at main 34fd6ede, with no
unrelated dependency churn and no product behavior change. This is the
human-designated immediate next engineering problem (2026-09-14).

## Durable provenance and requirements

- H: in-session human principal instruction 2026-09-14 — the failing security
  CI is the immediate next engineering problem; smallest compatible upgrades;
  pip-audit must pass; one PR with exact evidence.
- E: CI run 34793631952 at main 34fd6edeaad865d96e495cd10f78e84aabfad626 —
  security job FAIL in `uv run pip-audit`: 20 known vulnerabilities in 4
  packages — django 5.2.15 (PYSEC-2026-2090/2091/2092/3717; fix 5.2.16/5.2.17),
  djangorestframework 3.16.1 (PYSEC-2026-3827/3828; fix 3.17.2), pip 26.1.2
  (PYSEC-2026-3721; fix 26.2), sqlparse 0.5.5 (PYSEC-2026-3696/3697/3698/3699/
  3923; fix 0.6.0). All other jobs at that head PASS.
- A: OAP-PROTOCOL OP-09/OP-10/OP-11 (PR-before-report, report verification,
  merge gate).
- C: S-16 (exact-head review), S-17 (delegated development merge; side
  effects verified 2026-09-14, CI-only on main).
Requirements: SAR-032 (evidence before readiness), SAR-033 (preserve existing
project), SAR-035 (private infrastructure boundary), SAR-036 (deferred scope
stays visible — no new surfaces).

## Current reconciled state and prerequisites

- Base main (local and remote): 34fd6edeaad865d96e495cd10f78e84aabfad626
  (PR #30 merged). Worktree must be clean on main before starting.
- Known constraint facts (verify, do not assume): pyproject.toml has
  `django>=5.2,<5.3` (5.2.17 already permitted) and
  `djangorestframework>=3.16,<3.17` (the <3.17 bound blocks the fix and
  requires a constraint change); sqlparse is a transitive dependency of
  django; pip is the environment pip installed by `uv sync` (no explicit
  constraint exists — clear the finding by the smallest documented
  constraint mechanism).
- Current lockfile pins: django 5.2.15, djangorestframework 3.16.1, sqlparse
  0.5.5, pip 26.1.2 (record the actual inspected values in the report).

## Ordered read set

Standard compact read set, plus pyproject.toml, the four packages' lockfile
entries, .github/workflows/ci.yml (test/security/container jobs), TESTING.md,
and only ordered excerpts of code that actually breaks.

## Scope and allowed paths

1. Inspect the actual current pyproject.toml constraints and uv.lock pins
   first; record them in the report.
2. Minimal compatible upgrades clearing all four findings: django to a 5.2.x
   >= 5.2.16 (prefer the highest 5.2.x that is <5.3), djangorestframework to
   >= 3.17.2 within a new <3.18 bound, sqlparse to >= 0.6.0 (transitively,
   unless django 5.2.17 requires a different lower bound), pip to >= 26.2 via
   the smallest documented constraint mechanism (explicit dependency or uv
   constraint — pick one, document why).
3. pyproject.toml: change ONLY the djangorestframework upper bound (and the
   pip constraint mechanism if that is the chosen one). No other constraint,
   dependency or tooling change.
4. uv.lock: regenerate with uv (locked, all groups) so it reflects exactly the
   intended changes.
5. If and only if the upgraded packages break existing code or tests at a
   changed API: minimal strictly-required compatibility fixes under src/ or
   tests/ (see criterion 7). No other product changes.
6. The round bytes (order, pointer) and the final report.

## Non-goals

- No feature work, refactors, new dependencies, version jumps outside the
  four packages, workflow/CI changes, container/Dockerfile changes, docs
  changes, or unrelated lockfile churn.
- No merge, auto-merge, approval or settings change. No deployment of any
  kind. No lab/Neumann/production contact.
- No OAP/governance changes; no workflow-canary work.

## Numbered acceptance criteria

1. The report records the inspected pre-change state: exact pyproject
   constraint lines and exact uv.lock versions of the four packages.
2. `uv run pip-audit` exits 0 locally; the four packages are at or above the
   fix versions; no new packages; no other package version changed except
   unavoidable transitive consequences of the four (listed in the report with
   old->new versions).
3. pyproject.toml diff is limited to the djangorestframework upper bound and,
   if chosen, the pip constraint mechanism; every changed line explained in
   the report.
4. Full existing product suite passes locally at the implementation head:
   `uv run pytest` (all of it, including the browser suite) against a fresh
   owned disposable test database; `makemigrations --check --dry-run` shows no
   drift; `manage.py check`, `manage.py operational_check`, and
   `spectacular --validate --fail-on-warn` pass; `ruff check .`,
   `ruff format --check .`, `mypy src`, `git diff --check` clean.
5. Container/config validation passes locally as CI does:
   `docker compose config`, `deploy/rehearse_internal_alpha_deployment.sh
   --config-only`, `docker build`, and the static/bootstrap file checks.
6. CI at the exact reviewed head: quality, test, security and container all
   PASS (security now fully green including the production-settings import
   step). The oap path-gated workflow is not expected to run (no oap/ or
   tests/oap/ change) — its absence is the gate working, not a skipped
   check, and the report states so.
7. Any src/ or tests/ compatibility fix (if any) is strictly caused by a test
   or runtime failure that directly references a changed package's API; each
   is listed in the report with the exact failing command/trace that forced
   it. Zero such fixes is the expected outcome.
8. The report documents all compatibility consequences of the upgrades
   (DRF 3.16 -> 3.17 behavior notes, Django patch notes, sqlparse
   transitive movement, pip mechanism choice), truthfully separating
   observed results from assumptions.

## Verification

- `uv sync --locked --all-groups`
- `uv run pip-audit` (exit 0 required)
- `uv run pytest` (full suite, fresh owned test DB, sequential)
- `uv run python manage.py makemigrations --check --dry-run`
- `uv run python manage.py check`; `uv run python manage.py operational_check`
- `mkdir -p build/openapi && uv run python manage.py spectacular --file build/openapi/schema.yaml --validate --fail-on-warn`
- `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src`; `git diff --check`
- `docker compose config`; `deploy/rehearse_internal_alpha_deployment.sh --config-only`; `docker build --tag slaif-asset-reservation:ci .` plus the CI container file checks
- CI at the exact head (criterion 6).

## Negative paths

- Do not "fix" pip-audit by ignoring, vendoring or pinning out vulnerable
  versions; the audit must genuinely pass at passing versions.
- If a required upgrade proves incompatible with the product (not a small
  compatibility fix), stop and report BLOCKED with the exact evidence; do
  not force a larger version jump or redesign around it.
- If PR publication is blocked: truthful local evidence, no completion
  signal, no fabricated PR identity.
- No self-merge, auto-merge, check approval or protection bypass.

## Documentation

The report carries all compatibility documentation. No repository doc files
are changed by this order.

## Recovery

Interrupted round: same ID 016-a, same branch, issue #31, PR; resume from the
current branch head without renumbering; oap/RECOVERY.md applies; a lost
response after remote report means strategy review, not rerun.

## Deferred human adjudication

- Decision: NONE

## Publication and reporting

PR created before report composition; literal implementation head; report-only
first-parent commit; Report publication commit SELF; truthful implementation-CI
vs report-head-CI separation; remote verification receipt in the private home;
exact two-byte response OK; then no further mutation this round. Coding never
merges; strategy merges under delegated authority after exact-head review.
