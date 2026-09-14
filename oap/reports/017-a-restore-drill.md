<!-- OAP-META
{
 "kind": "report",
 "id": "017-a",
 "order_path": "oap/orders/017-a-restore-drill.md",
 "order_sha256": "7e8b4be43cb71675d0299dff9aa7441fc0f862a1ee3785ba8a2af98dab2d2a19",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 33,
 "pr_number": 34,
 "branch": "codex/33-oap-017-a-restore-drill",
 "implementation_head": "8f83dcbc311230385cfab7f68a85865b242b62d5",
 "base_sha": "bb06f81cbae815cbee9550af2a4ee7df3902137b",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "8f83dcbc311230385cfab7f68a85865b242b62d5",
  "runs": [
   {"run_id": 34798373837, "workflow": "CI", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 34798373830, "workflow": "oap", "jobs": {"oap-harness": "success on run_attempt 2"},
    "note": "attempt 1 (job 103835836872) failed with BrokenPipeError in the pre-existing flaky tests/oap/test_roundtrip_canary.py, a file this round does not touch; rerun of the failed job (job 103836498214) passed"}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 017-a report — codify and prove the isolated backup/restore drill

Order digest: 7e8b4be43cb71675d0299dff9aa7441fc0f862a1ee3785ba8a2af98dab2d2a19
(committed `oap/orders/017-a-restore-drill.md`; byte-identical to the
materialized `.FINAL` source — the strategic workorder journal's
`order_written` event records the same sha256 for the `.FINAL` path, and both
copies were hashed and compared before commit).

Implementation head SHA: 8f83dcbc311230385cfab7f68a85865b242b62d5

Report publication commit: SELF

**Result: COMPLETE** — the runbook's restore drill is codified as the
`restore_drill` management command (dry-run default) and proven with a real
`pg_dump` → `pg_restore` round trip against real PostgreSQL 17, both locally
and in the CI test job (9 drill tests, not skipped). No product behavior
change, no dependencies, no migrations. PR #34 opened at the exact
implementation head before this report. DHA untouched (Decision: NONE).

## Reconciliation at start (C-05/C-06/CP-03)

- `oap/active` = `017-a` + LF (exactly one valid ID);
  `check_state.py --repo .` → `state=ACTIVE_PENDING` (valid final order
  active), order `017-a` round `a`, branch `codex/33-oap-017-a-restore-drill`;
  `pr_mode` CREATE_OR_RESUME; single DHA declaration `Decision: NONE`.
- Local `main` = remote `origin/main` = `bb06f81cbae815cbee9550af2a4ee7df3902137b`
  = the order's `base_sha`; worktree clean apart from the round's own bytes
  (order + pointer), all on `allowed_paths`.
- No pre-existing branch `codex/33-oap-017-a-restore-drill` and no PR for
  issue #33 → fresh CREATE (no resume state).
- Wrapper had already consumed the control OK (journal: `order_written`,
  `control_consumed`, `invoked` for 017-a); it was not consumed again (CP-03).
- The order's meta `allowed_paths` names
  `oap/orders/017-a-restore-drill.md` while the wrapper materialized
  `oap/orders/017-a-restore-drill.FINAL.md`. The `.FINAL` source was verified
  byte-identical to the canonical name (sha256 `7e8b4be4…d2a19` on both
  copies; the journal's `order_written` event records the same digest for the
  `.FINAL` path), the canonical name was committed, and the untracked
  `.FINAL` duplicate was then removed from the worktree (bytes durable in git
  and in the journal).

## Inspected pre-change state (criterion 1) — PASSED

All facts verified directly at base `bb06f81cbae815cbee9550af2a4ee7df3902137b`:

- **Backup CLI** (`backup_database.py`): `--output` (required, "Backup
  artifact path to create.") and `--apply` (store_true, "Run pg_dump. Omit
  for validation-only dry-run."); `pg_dump --format=custom`; dry-run default;
  refuses missing DATABASE_URL / missing tools; never prints the password.
- **Restore CLI** (`restore_database.py`): `--input` (required) and
  `--apply`; `pg_restore --clean --if-exists --no-owner`; same dry-run/refusal
  posture.
- **Existing test coverage** (`tests/test_operational_hardening.py` lines
  296–343): exactly four tests — `test_backup_database_refuses_missing_database_url`,
  `test_backup_database_dry_run_does_not_print_password`,
  `test_restore_database_refuses_missing_database_url`,
  `test_restore_database_dry_run_does_not_print_password`. Dry-run/refusal
  paths only; no real dump/restore round trip anywhere.
- **Runbook "Restore Drill"** (`docs/runbooks/backup-and-restore.md`): the
  "Never restore over production without a separate human-approved incident
  plan." warning; a dry-run `restore_database --input …` validation line;
  `--apply` + `operational_check`; and a prose line to "compare user, asset,
  reservation, token, idempotency, blackout, and audit row counts against the
  source environment where appropriate." Procedure only — no codified command.
- **CI test job** (`.github/workflows/ci.yml`): `postgres:17` service
  (POSTGRES_DB/USER/PASSWORD `slaif`), port 5432:5432, `DATABASE_URL` /
  `TEST_DATABASE_URL` at `localhost:5432/slaif_reservation`, ubuntu-24.04
  runner with no pg client tools on the host (the base workflow has no
  pg-tools step).
- **Baseline local full suite at base**: 571 tests total — 570 passed plus 1
  failure, `tests/oap/test_ba38_39_tmux_config.py::test_ba39_strategic_same_prerequisites`,
  an environment artifact: that launcher fixture inherits the coding wrapper's
  `OAP_ROLE=CODING`, whose role guard refuses. With `OAP_ROLE` unset
  (CI-equivalent; CI does not carry the variable) the baseline is fully
  green. Not a code defect; this round does not touch that fixture.

## What changed (commit 8f83dcb, 7 files, +1329/−6, all on allowed_paths)

1. `src/slaif_reservation/api/management/commands/restore_drill.py` (new,
   623 lines) — the codified isolated drill, dry-run default:
   - CLI: `--source-url` (default `DATABASE_URL`), `--target-url` (required;
     the named database must not exist yet), `--workdir` (default the
     git-ignored `<repo>/build/restore-drill`), `--apply`.
   - Refusals (dry-run and `--apply`): unparseable/non-PostgreSQL source or
     target URL; target database not distinct from the source database on the
     same server; target database already existing on the target server
     (isolation means drill-created — the drill never drops or restores over
     pre-existing data); missing `pg_dump`/`pg_restore` on PATH; unwritable
     workdir; stale `drill.dump` artifact from a previous run.
   - `--apply` (all real, no mocks): `pg_dump --format=custom` into
     `<workdir>/drill.dump`, reusing `backup_database` by import;
     `CREATE DATABASE <target>` on the target server's maintenance database
     (the drill records that it created it); `pg_restore --clean
     --if-exists --no-owner` into the target, reusing `restore_database` by
     import.
   - Verification (structured key=value output; never prints passwords or
     credential-bearing URLs): per-table row counts (users, assets,
     reservation policies, reservations, maintenance blackouts, audit events,
     API tokens, idempotency records, `django_migrations`) with
     `row_counts_equal=true`; the named GiST exclusion constraint
     `reservation_no_overlap_per_asset` present and actually blocking an
     attempted conflicting overlapping INSERT (expected named exclusion
     violation, rolled back); optional API token round trip through the real
     verifier path (`parse_bearer_token` / `api_token_verifier` /
     `api_token_verifier_matches`, owner/revoked/expiry checks) against the
     restored database via a temporary Django database alias; point-in-time
     probe (a reservation created on the source after the dump must be absent
     from the target); source-unchanged accounting (the source gains exactly
     the drill's probe reservation and its audit event; all pre-drill
     reservations remain); migration equality.
   - Scoped cleanup: `DROP DATABASE` for the drill-created target only and
     workdir removal on success; on failure the drill drops the drill-created
     target (when it created one) and retains the artifact path in the output
     for operator inspection.
   - **D0 decision (routine in-scope mechanic, C-07)**: the token-probe
     plaintext is read from the `RESTORE_DRILL_TOKEN_PROBE` environment
     variable — deliberately not from argv (process-listing secrecy) and
     never printed; when unset the drill prints `token_round_trip=skipped`
     and completes the other verifications. The order fixes the property to
     prove (a restored token authenticates through the real verifier path
     using the restored DB's stored verifier) and prescribes no plaintext
     transport.
2. `tests/test_restore_drill.py` (new, 404 lines) — 9 tests, all
   `TransactionTestCase` (the drill needs committed data for `pg_dump`),
   running against real PostgreSQL (CI: the `postgres:17` service; the target
   database is created and dropped by the drill itself):
   - `test_real_round_trip_verifies_and_cleans_up` — seeds the source through
     real product entry points (bootstrap asset import,
     `User.objects.create_user`, the `create_policy` / `create_reservation` /
     `create_blackout` service functions, `issue_api_token`, and one real
     `POST /api/v1/reservations/` with Bearer authorization +
     Idempotency-Key → 201), runs the drill `--apply` with the token-probe
     environment variable set, and asserts every scope-1d verification line,
     the cleanup (target database absent, workdir removed) and the absence of
     URL/credential strings in the output.
   - `test_target_equal_to_source_refused`; `test_preexisting_target_refused_and_untouched`
     (sentinel table in the pre-existing target database, byte-identical after
     the refusal); `test_dry_run_has_zero_side_effects` (no artifact, no
     target database, no source write); `test_missing_pg_tools_refused` (PATH
     simulation); `test_non_postgres_urls_refused`;
     `test_unwritable_workdir_refused` (skipped when euid==0);
     `test_stale_artifact_refused`; `test_no_credential_leak_in_failure_output`
     (canary password in the URL must not appear in captured output).
3. `.github/workflows/ci.yml` — exactly one step added in the test job after
   `uv sync`: `Install postgresql-client-17` (PGDG key `ACCC4CF8.asc`
   dearmored to `/etc/apt/trusted.gpg.d/pgdg.gpg`, `noble-pgdg main`
   repository, `apt-get install postgresql-client-17`, plus `/usr/local/bin`
   symlinks pinning `pg_dump`/`pg_restore` — required for determinism, since
   the distro `pg_wrapper` resolves to an older client when one is present).
   Documented in a comment. CI log at the head: `pg_dump (PostgreSQL) 17.11`.
4. `docs/runbooks/backup-and-restore.md` — the "Restore Drill" section now
   documents the codified command: exact invocations (dry-run and `--apply`),
   the `RESTORE_DRILL_TOKEN_PROBE` environment variable (including the probe
   side effect: the drill leaves one confirmed probe reservation on the
   source; cancel or release it through the normal paths), the refusal list,
   the CREATEDB requirement, the structured verification output, and
   on-failure artifact retention. The manual `backup_database` /
   `restore_database` procedure is kept as fallback; the production warning
   stays.
5. `docs/runbooks/internal-alpha-pilot-preparation.md` — exactly one
   success-criterion line changed: the isolated restore drill is "planned" →
   "codified as the `restore_drill` management command (see
   `docs/runbooks/backup-and-restore.md`)".
6. `oap/orders/017-a-restore-drill.md` + `oap/active` — the round bytes
   (commit message records the sha256 and byte-identity, mirroring the 016-a
   convention).

## Numbered acceptance evidence

**1. Pre-change state recorded — PASSED.** See "Inspected pre-change state"
above; every fact verified directly at base `bb06f81`.

**2. `restore_drill` exists, dry-run default, every refusal + apply flow,
reuse by import, no existing command changed — PASSED.** File/CLI as in
"What changed" item 1; omitting `--apply` is the validation-only dry run.
Reuse by import: `backup_database.Command` and `restore_database.Command`
imported and invoked via `Command(stdout=StringIO()).handle(...)` under a
temporary `DATABASE_URL` environment override — no subprocess/env logic
duplicated. `git diff bb06f81..8f83dcb --stat` shows
`backup_database.py`, `restore_database.py`, `_postgres_tools.py` and
`operational_check.py` untouched, and `pyproject.toml` / `uv.lock` untouched.

**3. Real round trip against real PostgreSQL 17 in CI (not skipped) and
locally — PASSED.** CI test job at the head (run 34798373837, job
103835836987): the `Install postgresql-client-17` step prints `pg_dump
(PostgreSQL) 17.11` / `pg_restore (PostgreSQL) 17.11`; `tests/test_restore_drill.py`
shows 9 passing dots (not skipped); job summary "580 passed in 116.64s".
Local at the head, re-run at authoring against the owned disposable
PostgreSQL 17.11 container (see "Security, data, dependencies and local
tools"): **580 passed in 168.63s, 0 failed**. The round-trip test asserts
every scope-1d line: row-count equality for all nine tables including
`django_migrations`; exclusion constraint present + blocking a conflicting
INSERT (rolled back); token round trip through the real verifier against the
restored DB; post-backup probe absence; source-unchanged accounting;
migration equality; cleanup (target database absent, workdir removed).

**4. Negative tests — PASSED.** `test_target_equal_to_source_refused`;
`test_preexisting_target_refused_and_untouched` (pre-existing database left
byte-identical: sentinel table survives); `test_dry_run_has_zero_side_effects`
(no artifact, no target database, no source write); `test_missing_pg_tools_refused`;
`test_non_postgres_urls_refused`; `test_unwritable_workdir_refused`;
`test_stale_artifact_refused`; `test_no_credential_leak_in_failure_output`
(canary). All executed and passing in both the local run and the CI test job
at the head.

**5. Full suite + quality gates + CI green at the exact implementation head —
PASSED.** CI run 34798373837 at head `8f83dcb`: quality success (ruff check,
ruff format --check, mypy src, git diff --check), test success (migrate,
import_bootstrap_assets, operational_check, purge_expired_idempotency_records,
makemigrations --check --dry-run, manage.py check, spectacular --validate
--fail-on-warn, then full pytest "580 passed in 116.64s" including the drill
tests), security success, container success. Local at the head, re-verified
at authoring: `uv sync --locked --all-groups` exit 0 (lock untouched);
`uv run ruff check .` clean; `uv run ruff format --check .` clean;
`uv run mypy src` clean; `manage.py check` — 0 issues;
`makemigrations --check --dry-run` — "No changes detected";
`operational_check` — all dimensions ok; `spectacular --file
build/openapi/schema.yaml --validate --fail-on-warn` — exit 0;
`git diff --check` clean; full suite 580 passed / 0 failed.

**6. Runbook changes exactly scope item 4 — PASSED.** `git diff --stat` shows
exactly the two runbook files changed under `docs/`; the
backup-and-restore change is confined to the "Restore Drill" section (manual
fallback retained), the pilot-preparation change is exactly the one
success-criterion line; no other doc file changed.

**7. Diff limited to allowed_paths; zero product behavior change; zero
dependencies; zero migrations — PASSED.** `git diff bb06f81..8f83dcb --stat`
= exactly the 7 files above, all on `allowed_paths`. No `src/` change other
than the new command file; no `pyproject.toml` / `uv.lock` change (no new or
removed dependencies); no migrations (makemigrations check clean at the head,
locally and in CI).

## CI observed before authoring (implementation head)

- CI run **34798373837** (workflow `CI`, head `8f83dcbc…`): quality success
  (job 103835836789), container success (job 103835836941), test success (job
  103835836987), security success (job 103835837100).
- oap run **34798373830** (workflow `oap`, same head): oap-harness success on
  **run_attempt 2** (job 103836498214). Attempt 1 (job 103835836872) failed
  with `BrokenPipeError` at `tests/oap/test_roundtrip_canary.py:268` — the
  pre-existing timing flake in the OAP harness's own round-trip canary
  (duplicate-wake-up FIFO race), a file this round does not touch and which is
  outside this round's scope. The failed-job rerun (same run, attempt 2)
  passed. The flake is not run-as-failure evidence for this round: every one
  of this round's tests passed in the CI test job (580 passed), and the oap
  harness passed at the head on the observed attempt.
- Report-head CI (post-report-commit): **NOT YET OBSERVED AT AUTHORING.**
  Post-publication verification (remote head/PR/report bytes/parent) is
  recorded in the private execution receipt (CP-07), not in this report.

## Security, data, dependencies and local tools

- No credentials, tokens, peppers, verifiers, cookies or private exports
  appear in this report or in any committed file. The drill's output contract
  (no passwords, no credential-bearing URLs) is itself tested by the canary
  test (evidence 4).
- Local disposable infrastructure (SAR-031; owned, explicit identity): docker
  container `slaif-oap017-pg17` (`postgres:17` image, PostgreSQL 17.11),
  loopback-only `127.0.0.1:54330→5432`, synthetic CI-equivalent disposable
  credentials, no volume. It served as the local target server for the drill
  tests. It is owned by this round and is removed after this report's
  publication steps (`docker rm -f slaif-oap017-pg17`). No
  production/lab/Neumann/SmartScheduling contact, no DNS/TLS/firewall
  changes, no public exposure.
- Local test-tool install (C-09 routine permitted, documented here): the
  host's `pg_dump`/`pg_restore` were PostgreSQL 16 and cannot read server-17
  custom dumps (hard block for the drill tests), so `postgresql-client-17`
  (17.11, PGDG) was installed on the local host with `/usr/local/bin` symlinks
  pinning `pg_dump`/`pg_restore` to the 17 binaries. Test-tooling only; no
  product, dependency or CI configuration change.
- No new or removed project dependencies; `pyproject.toml` / `uv.lock`
  untouched (SAR-022 preserved).
- Environment artifact (not a code defect): the coding wrapper's process
  environment carries `OAP_ROLE=CODING`, which breaks one OAP-harness test
  (`test_ba39_strategic_same_prerequisites`, whose launcher fixture
  inherits it) in local full runs; CI does not carry the variable and passes.
  Local full runs therefore use `env -u OAP_ROLE`.

## DHA outcome and unresolved gates

- The order's single declaration is `Decision: NONE`. No `CRITICAL.md`
  change, no append, no human disposition by coding, no gate clearance.
- No unresolved gates from this round.

## Limitations and recommendation

- The `--apply` drill leaves one confirmed probe reservation on the **source**
  (point-in-time artifact; its id is printed). Cancel or release it through
  the normal product paths after the drill. In the tests the source is a
  disposable test database, so no pilot-data impact.
- The token round trip is optional by design: with `RESTORE_DRILL_TOKEN_PROBE`
  unset the drill prints `token_round_trip=skipped` and completes the other
  verifications. The runs cited here set the variable, so the full line is
  asserted.
- The pre-existing-target precheck requires the connecting user to open the
  target server's `postgres` maintenance database (to enumerate
  `pg_database`); the drill is documented to run with a CREATEDB-capable user
  on a disposable server.
- The source-unchanged retention check is bounded to the pre-drill
  reservation UUID set (`id__in`) — pilot-scale; a full row-image diff was not
  the ordered scope.
- The pre-existing `test_roundtrip_canary` harness flake (OAP machinery,
  untouched by this round) failed once in CI and passed on rerun; its repair
  is out of scope here and belongs to the OAP-machinery owner.
- Recommendation: strategy review of PR #34 at the exact head and delegated
  development merge if accepted. No merge, auto-merge, approval or milestone
  claim by coding; this report is not strategic acceptance, and not release or
  ICA acceptance (SAR-032: this produces the recovery-evidence pillar only —
  readiness remains strategy's and the human's call).

## Commands (exact, as run at implementation head 8f83dcb)

```
# local disposable environment (SAR-031; removed after the round)
docker run -d --name slaif-oap017-pg17 -p 127.0.0.1:54330:5432 \
    -e POSTGRES_USER=<synthetic> -e POSTGRES_PASSWORD=<synthetic> postgres:17
sudo apt-get install -y postgresql-client-17    # PGDG repo; /usr/local/bin pin

uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
git diff --check
uv run --env-file .env python manage.py check
uv run --env-file .env python manage.py makemigrations --check --dry-run
uv run --env-file .env python manage.py migrate --noinput
uv run --env-file .env python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml
uv run --env-file .env python manage.py operational_check
mkdir -p build/openapi && uv run --env-file .env python manage.py \
    spectacular --file build/openapi/schema.yaml --validate --fail-on-warn
env -u OAP_ROLE uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test -q
env -u OAP_ROLE uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test -q \
    tests/test_restore_drill.py
python3 -m unittest discover -s tests/oap -p 'test_*.py' -v    # oap harness (CI job equivalent)
```
