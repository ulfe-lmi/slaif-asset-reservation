# TESTING — existing application and Concentrated OAP

This extends, not replaces, docs/testing-strategy.md. The normal coding read set uses TESTING-CORE;
load this full file only for the relevant ordered verification. Tests prove the exercised boundary,
not every requirement adjacent to it.

## T-01. Harness qualification

Run pure helper tests without a product DB or real model:
`python3 -m unittest discover -s tests/oap -p 'test_*.py' -v` (its own path-gated
`oap-harness` CI job). The surviving slim-round suites — state, orders, publish, fifo,
wrapper, report, DHA, privacy, continuity, round-trip canary — require named
implementation tests, finite timeout and owned cleanup. Actual disposable Git
commits/FIFOs/tmux test sockets exercise transport/history; fake clients/remotes/CI
exercise invocation and publication contracts. No real GitHub write, model call or
lab access in the harness. Check slim-order schema/superset-acceptance,
read-set/role/authority/active/recovery/report/DHA/ICA and no-self-merge contracts.
Historical BA case numbers are preserved in surviving files; removed BA files covered
archived bootstrap machinery (see docs/bootstrap/archive/ARCHIVE-NOTE.md).

## T-02. Existing application regression (separately authorized adoption/development)

Use an owned disposable checkout and PostgreSQL17 project, not a valuable working tree containing
real .env/deploy secrets. Audit the baseline operational tests/rehearsal before execution: they use
repository deployment paths and cleanup. Do not run independent pytest processes concurrently on
the same test DB. A Docker daemon reachable from the current context may be remote; qualify it.
Never use unscoped `docker compose down -v` or production DATABASE_URL. Wait for DB health with
finite timeout and record which actual project/database is owned. No change to project data needed.

Standard commands, with a synthetic .env in the disposable test copy:

```bash
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run --env-file .env python manage.py check
uv run --env-file .env python manage.py makemigrations --check --dry-run
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test --browser chromium tests/browser
uv run pip-audit
git diff --check
uv run --env-file .env python manage.py spectacular --file build/openapi/schema.yaml --validate --fail-on-warn
uv run --env-file .env python manage.py operational_check
```

Install Playwright browser/system dependencies inside the approved disposable environment when
needed, record tools installed, and do not ask the human for routine setup. No real service calls.
The original four CI job names remain quality/test/security/container. Required current-head checks
must actually succeed. Pending/missing/cancelled/skipped are not success. Separate implementation
head CI from final report head CI; no future result invented in a report-only commit.

## T-03. Required product proof families

| Boundary | Existing suites / required scope |
|---|---|
| PostgreSQL reservation integrity | test_reservations_models/services/concurrency; exclusion and btree_gist inspection; real races |
| Time and privacy | reservation time, accounts validators, human MVP; DST/naive/malformed timezone, owner isolation |
| API and idempotency | test_api_v1_reservations.py/test_api_schema.py; actual auth, scope, replays/Location/expiry, negative filters |
| Token security | test_api_tokens.py; verifier/pepper/expiry, one-time history, repr/exception/audit/log redaction, ORM protection |
| Management | test_management_ui.py; every mutation CSRF/GET, staff/owner split, policy/blackout rollback/export |
| Synthetic import | test_legacy_import.py; parser/mapping/dry-run/apply/idempotency/stale plan/actual report/privacy |
| Operations | test_operational_hardening.py/test_settings.py/health suites; failure and real entry points |
| Readiness helper | test_pilot_readiness_check.py; DB-down/unmigrated/count failure, strict/JSON/read-only, not only row counts |
| Browser | tests/browser explicit Chromium; no secret-bearing capture artifacts |

Use current tree to discover exact filenames rather than invent missing paths. A mocked database
cannot prove exclusion, row locks or rollback; a fake HTTP adapter cannot prove auth/CSRF; a parsed
Compose file cannot prove actual sockets; a dump file cannot prove restore. No dangerous failure
may be excluded because the happy-path suite is green.

## T-04. Container and recovery evidence

Build reviewed image; check UID:GID10001:10001, member/admin/Swagger static assets and sanitized
bootstrap files. Render production example using owned synthetic configuration only; never overwrite
an existing deploy/env.production or secret file. Rehearsal runs only after owned-resource safety
qualification, on a unique isolated project/port. Check actual resources/ports and cleanup, not
just stub output. Current backup/restore wrapper refusal/dry-run evidence is not a successful restore
drill; a selected recovery order must execute real PostgreSQL tools into a distinct disposable target.

## T-05. Reports and release

Name commands/revision/counts/duration measured if available, exact failures/blocked tools and
what was NOT RUN. Do not sum overlapping focused/full suites as additional unique coverage. The
historical419-test report is not a current measurement. M-CONVERSION and local-pilot ICA use full
architecture matrices with actual evidence and independent provenance; no test count grants release.
