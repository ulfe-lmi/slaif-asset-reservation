<!-- OAP-META
{
 "kind": "report",
 "id": "016-a",
 "order_path": "oap/orders/016-a-security-pip-audit.md",
 "order_sha256": "5d2cb36122a165f9c336077f2555418d00f2d2845d82c604063be536b983c9cf",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 31,
 "pr_number": 32,
 "branch": "codex/31-oap-016-a-security-pip-audit",
 "implementation_head": "7bb45366476209146738202dd9ec4fb20225fce7",
 "base_sha": "34fd6edeaad865d96e495cd10f78e84aabfad626",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "7bb45366476209146738202dd9ec4fb20225fce7",
  "runs": [
   {"run_id": 34795342492, "workflow": "CI", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 34795342487, "workflow": "oap", "jobs": {"oap-harness": "success"}}
  ],
  "security_note": "security job now fully green at the exact head, including the production-settings import step (previously FAIL on the same 20 pip-audit findings)"
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 016-a report — clear the pip-audit findings: minimal dependency upgrades

Order digest: 5d2cb36122a165f9c336077f2555418d00f2d2845d82c604063be536b983c9cf
(commit `oap/orders/016-a-security-pip-audit.md`, byte-identical to the
materialized `.FINAL` source; both copies hashed and compared before commit).

Implementation head SHA: 7bb45366476209146738202dd9ec4fb20225fce7

Report publication commit: SELF

**Result: COMPLETE** — all four pip-audit findings cleared by the smallest
compatible upgrades, no unrelated dependency churn, no product behavior
change, PR before report, DHA untouched (Decision: NONE).

## Reconciliation at start (C-05/C-06/CP-03)

- `oap/active` = `016-a` + LF (exactly one valid ID); `check_state.py --json`
  state `ACTIVE_PENDING`, order state `FINAL`, PR mode `CREATE_OR_RESUME`.
- Local `main` = remote `origin/main` = `34fd6edeaad865d96e495cd10f78e84aabfad626`
  (order `base_sha`; PR #30 merged). Worktree clean except the round's own
  bytes (order source + pointer), all on `allowed_paths`.
- No pre-existing branch `codex/31-oap-016-a-security-pip-audit`
  (`git ls-remote`) and no PR for issue #31 → fresh CREATE (no resume state).
- Order internally consistent: `previous_round: null` with CREATE_OR_RESUME;
  single DHA declaration `Decision: NONE`.

## Criterion 1 — inspected pre-change state (PASSED)

`pyproject.toml` constraint lines at base (exact):

- `  "django>=5.2,<5.3",` (unchanged by this round)
- `  "djangorestframework>=3.16,<3.17",`
- no constraint on `pip` (environment pip installed by `uv sync`)
- no constraint on `sqlparse` (transitive dependency of django)

`uv.lock` pins at base (inspected line-by-line): django `5.2.15`,
djangorestframework `3.16.1`, pip `26.1.2`, sqlparse `0.5.5`; lock header
`version = 1`, `revision = 3`; 71 packages.

Baseline `uv run pip-audit` at base (after `uv sync --locked --all-groups`,
exit 0): **exit 1**, "Found 20 known vulnerabilities in 4 packages" —
django 5.2.15 (PYSEC-2026-2090/2091/2092 fix 5.2.16; PYSEC-2026-3717 fix
5.2.17), djangorestframework 3.16.1 (PYSEC-2026-3827/3828 fix 3.17.2),
pip 26.1.2 (PYSEC-2026-3721 fix 26.2), sqlparse 0.5.5 (PYSEC-2026-3696/3697/
3698/3699/3923 fix 0.6.0). Identical multiset to the order's CI evidence
(run 34793631952).

## What changed (commit 7bb4536, four files, all on allowed_paths)

1. `pyproject.toml` — two hunks (criterion 3):
   - `  "djangorestframework>=3.16,<3.17",` → `  "djangorestframework>=3.16,<3.18",`
     Upper bound only — the `<3.17` bound was the blocker for the 3.17.2 fix.
     The lower bound `>=3.16` is intentionally unchanged per scope item 3 /
     criterion 3 ("ONLY the djangorestframework upper bound ... every changed
     line explained"); the locked/resolved version 3.17.2 satisfies scope
     item 2's target state, and every verification path (local, CI, image)
     uses `uv sync --locked`, so the lock is the authoritative pin.
   - `[tool.uv]` gains `constraint-dependencies = ["pip>=26.2,<27"]` — the
     chosen pip constraint mechanism (criterion 3 "if chosen"). Rationale:
     uv's documented *constraint* mechanism (uv book, "Constraints"), which
     constrains resolution of the environment pip already present in
     `uv.lock` (a normal lock package) **without adding a declared project
     dependency** — the strictest reading of the forbidden "new
     dependencies". Alternative considered and rejected: adding
     `pip>=26.2,<27` to `[project] dependencies` would create a new declared
     dependency edge (package manager as app dependency); the constraint is
     the smaller documented mechanism. The `<27` upper bound follows the
     repo's next-major pinning style (cf. `gunicorn>=23,<24`).
2. `uv.lock` — regenerated with the bounded, documented per-package
   re-resolution
   `uv lock --upgrade-package django --upgrade-package djangorestframework --upgrade-package sqlparse --upgrade-package pip`
   (a plain `uv lock` would have kept the still-satisfiable vulnerable pins;
   `--upgrade` (all) would churn unrelated packages). Result: exactly four
   version changes, 71 packages before and after, no package added or
   removed, lock header `version = 1` / `revision = 3` unchanged (readable by
   CI's pinned uv 0.11.23 — proven by the container job building the image
   from this lock).
3. `oap/orders/016-a-security-pip-audit.md` — published round bytes,
   byte-identical to the materialized `.FINAL` source (sha256
   5d2cb361…3c9cf on both copies).
4. `oap/active` — pointer `015-b` → `016-a` (round activation byte).

## Numbered acceptance evidence

**1. Pre-change state recorded — PASSED** (section above, exact lines/pins).

**2. pip-audit passes at fixing versions, no churn — PASSED.**
`uv run pip-audit` at the implementation head: **exit 0**, "No known
vulnerabilities found". Resolved versions (lock = environment,
`uv sync --locked --all-groups` exit 0):

| package | old | new | fix version (order E) |
|---|---|---|---|
| django | 5.2.15 | 5.2.17 | 5.2.16 / 5.2.17 |
| djangorestframework | 3.16.1 | 3.17.2 | 3.17.2 |
| sqlparse | 0.5.5 | 0.6.0 | 0.6.0 |
| pip | 26.1.2 | 26.2.1 | 26.2 |

All at or above fix versions; django is the highest 5.2.x < 5.3. `git diff
uv.lock` shows only these four package entries (version + their sdist/wheel
URLs/hashes) plus the root-project DRF specifier metadata line
(`>=3.16,<3.17` → `>=3.16,<3.18`). No other package version changed; no
unavoidable transitive consequences occurred (all four packages have
unchanged dependency sets in the lock; 71 → 71 packages).

**3. pyproject diff limited — PASSED.** `git diff pyproject.toml` is exactly
the two hunks above; no other constraint, dependency or tooling line touched
(django, drf-spectacular, drf-spectacular-sidecar, gunicorn, jsonschema,
psycopg, pyyaml, whitenoise, dev group, all `[tool.*]` tables unchanged).
Every changed line is explained in the "What changed" section.

**4. Full local product verification at implementation head — PASSED.**
Against a fresh owned disposable PostgreSQL 17.11 (dedicated `postgres:17`
container, loopback port 54330, synthetic CI-equivalent disposable
credentials; pytest-django created `test_slaif_reservation`; container torn
down at round end):

- `uv sync --locked --all-groups` — exit 0.
- `env -u OAP_ROLE uv run --env-file .env pytest
  --ds=slaif_reservation.config.settings.test` — **571 passed, 0 failed in
  139.61s** (full suite incl. browser suite; chromium installed locally via
  `uv run playwright install --with-deps chromium`, recorded per T-02;
  sequential, single test DB).
- `uv run --env-file .env python manage.py makemigrations --check --dry-run`
  — "No changes detected".
- `uv run --env-file .env python manage.py check` — "System check identified
  no issues (0 silenced)".
- `uv run --env-file .env python manage.py operational_check` — all
  dimensions ok (database/migrations/static/bootstrap/
  idempotency_cleanup_command/operational_check), after the same
  `migrate --noinput` + `import_bootstrap_assets` setup the CI test job runs
  (bootstrap import: planned=47 created=47 excluded=1, the documented
  exclusion).
- `mkdir -p build/openapi && uv run --env-file .env python manage.py
  spectacular --file build/openapi/schema.yaml --validate --fail-on-warn` —
  exit 0.
- `uv run ruff check .` — "All checks passed!"; `uv run ruff format --check
  .` — "179 files already formatted"; `uv run mypy src` — "Success: no
  issues found in 118 source files"; `git diff --check` — clean.

Environment note (truthful): the first local full-suite run inherited
`OAP_ROLE=CODING` from the coding wrapper environment and showed exactly one
failure — `tests/oap/test_ba38_39_tmux_config.py::Ba39OperationPrereqs::
test_ba39_strategic_same_prerequisites`. Root cause reproduced in isolation:
the launcher fixture invokes `oap_launch.py strategic …`, whose role guard
refuses with "conflicting OAP_ROLE=CODING; refusing" — an environmental
artifact of running the stdlib-only launcher fixture inside a CODING
session, with no connection to the four upgraded packages. Re-run with
`OAP_ROLE` unset (CI-equivalent; CI runs without OAP_ROLE): 571 passed,
0 failed, and the CI test job confirms the same count (571 passed in
104.25s in the CI log).

**5. Container/config validation — PASSED.** `docker compose config --quiet`
ok; `deploy/rehearse_internal_alpha_deployment.sh --config-only` →
"rehearsal: config-only=ok"; `docker build --tag slaif-asset-reservation:ci
.` ok (Dockerfile pins uv 0.11.23 and runs `uv sync --locked --no-dev` from
this lock); `docker image inspect … Config.User` = `10001:10001`; all five
CI image file checks pass (`/app/staticfiles/web/site.css`,
`/app/staticfiles/admin/css/base.css`,
`/app/staticfiles/drf_spectacular_sidecar/swagger-ui-dist/
swagger-ui-bundle.js`, `/app/data/bootstrap/assets.yaml`,
`/app/data/bootstrap/assets.schema.json`). Supplemental: in-image
`django 5.2.17`, `rest_framework 3.17.2`, `sqlparse 0.6.0`, in-image
`pip --version` → 26.2.1.

**6. CI at the exact reviewed head — PASSED.** At implementation head
7bb45366476209146738202dd9ec4fb20225fce7 (observed at authoring):

- CI run 34795342492: **quality success, test success, security success,
  container success**. The security job is now fully green including the
  production-settings import step (previously the failing job; its failure
  at base was exactly the 20 findings this round clears).
- oap run 34795342487: **oap-harness success**.

Deviation from the order's prediction (stated for exact-head review):
criterion 6 said the oap path-gated workflow "is not expected to run (no
oap/ or tests/oap/ change)". In fact the round's own publication bytes
(`oap/orders/016-a-security-pip-audit.md`, `oap/active` — both on
`allowed_paths` and required to be committed by the coding sequence, C-11)
fall under the gate's `oap/**` path, so the oap-harness job ran and
succeeded. That is the path gate working as designed for the paths actually
changed; all four required product CI jobs (quality/test/security/container)
pass at the exact head, which is what criterion 6 requires.

**7. Compatibility fixes — PASSED (zero fixes).** No `src/` or `tests/` file
was changed. No test or runtime failure referencing a changed package's API
occurred at any point in this round; the expected outcome (zero fixes) held.

**8. Compatibility consequences (observed vs assumed, separated).**

- **djangorestframework 3.16.1 → 3.17.2** (minor). Observed: full product
  suite (571 tests incl. API, idempotency-replay, token and browser suites)
  passes locally and in CI; `spectacular --validate --fail-on-warn` passes
  with the generated schema unchanged in behavior (no schema edit needed);
  DRF's lock dependency set unchanged (django only). Not individually
  reviewed line-by-line: upstream 3.17 release notes (assumption-free
  statement: this report does not certify every upstream note; the risk
  surface is bounded by the passing full suite + schema validation).
- **django 5.2.15 → 5.2.17** (patch within 5.2.x; `<5.3` bound unchanged).
  Observed: `makemigrations --check --dry-run` clean; full suite passes;
  lock dependency set unchanged (asgiref/sqlparse/tzdata(win32)).
- **sqlparse 0.5.5 → 0.6.0** (transitive via django; no pyproject
  constraint). Moved by the bounded `--upgrade-package sqlparse`
  re-resolution rather than by a django lower-bound change (django 5.2.17's
  sqlparse requirement in the lock is unchanged); observed full-suite pass.
- **pip 26.1.2 → 26.2.1** (environment pip in the uv venv, audited by
  `pip-audit` in the security job). Mechanism: `[tool.uv]
  constraint-dependencies = ["pip>=26.2,<27"]` (chosen and explained in
  "What changed"). Observed: local `uv run pip-audit` exit 0; CI security
  job success; `uv sync --locked` exit 0 (lock consistent with the
  constraint); image `pip --version` 26.2.1.
- **Lock/uv compatibility**: lock header unchanged (version 1, revision 3);
  the container job built the image with CI-pinned uv 0.11.23 from this lock
  — cross-verified CI-compatible.

## Negative paths

- No ignore/vendoring/pinning-out: the audit genuinely passes at passing
  versions (criterion 2 evidence).
- No incompatible-upgrade stop condition triggered; no forced version jump
  (all upgrades within the existing major lines; the only bound change is
  the DRF upper bound to `<3.18`, which the order itself prescribes).
- PR publication not blocked; PR #32 opened at the exact implementation
  head before this report.
- No merge, auto-merge, approval, or protection change by coding.

## Uncertainty, privacy, dependencies, DHA, limits

- Report-head CI (post-report-commit) is NOT YET OBSERVED AT AUTHORING; it
  is separate from the observed implementation-head CI and is not claimed.
- `verify_report.py` / remote publication verification results are recorded
  in the private execution receipt (CP-07), not in this immutable report.
- No credentials, tokens, peppers, verifiers, cookies or private exports
  appear in this report or in any committed file; the disposable DB used
  synthetic CI-equivalent test credentials only.
- No new or removed dependencies; the only pyproject changes are the two
  explained hunks. No production dependency or alternate stack added
  (SAR-022 preserved).
- DHA: the order's single declaration is `Decision: NONE`; no CRITICAL.md
  change, no append, no human disposition by coding.
- The materialized source `oap/orders/016-a-security-pip-audit.FINAL.md`
  was left untracked in the worktree (preserved, not committed); the
  committed order bytes under the allowed-path name are byte-identical
  (sha256 compared on both copies).
- Coding never merges; strategy merges under delegated authority after
  exact-head review; this report is not a strategic acceptance.

## Commands (exact, as run at implementation head)

```
uv sync --locked --all-groups
uv run pip-audit                                   # exit 0
uv lock --upgrade-package django --upgrade-package djangorestframework \
        --upgrade-package sqlparse --upgrade-package pip
uv run ruff check .
uv run ruff format --check .
uv run mypy src
git diff --check
uv run --env-file .env python manage.py check
uv run --env-file .env python manage.py makemigrations --check --dry-run
uv run --env-file .env python manage.py migrate --noinput   # fresh DB setup (as CI)
uv run --env-file .env python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml
uv run --env-file .env python manage.py operational_check
mkdir -p build/openapi && uv run --env-file .env python manage.py \
    spectacular --file build/openapi/schema.yaml --validate --fail-on-warn
env -u OAP_ROLE uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test
uv run playwright install --with-deps chromium     # local test tool install (T-02)
docker compose config --quiet
deploy/rehearse_internal_alpha_deployment.sh --config-only
docker build --tag slaif-asset-reservation:ci .
```
