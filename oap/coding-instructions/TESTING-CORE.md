# Executor testing core

TC-01. Ordered tests plus dangerous negative paths; PASSED only if actually executed successfully.
Name exact source/report head, commands/counts and FAILED/SKIPPED/NOT RUN/BLOCKED/PENDING/MISSING.
TC-02. Harness: stdlib unittest suite in tests/oap with fake clients/remotes and real temporary POSIX
FIFOs/Git; no model calls/real remote writes. Product invariants: real PostgreSQL17/concurrency,
real adapter/browser for CSRF/privacy, actual dump/restore for restore claims; mocks do not prove
replaced boundary. Read-only row counts alone cannot prove absence of updates/deletes/reinserts.
TC-03. Run product suites sequentially against owned disposable DBs; never simultaneous independent
pytest on same test DB. Wait for DB health with bounded timeout. No unknown compose down -v.
TC-04. Baseline commands: uv sync --locked --all-groups; uv run ruff check .; uv run ruff format
--check .; uv run mypy src; uv run --env-file .env python manage.py check; ... makemigrations --check
--dry-run; uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test; uv run pip-audit;
git diff --check; sha256sum -c MANIFEST.sha256. Full exact variants live in TESTING.md when ordered.
TC-05. Browser/UI boundary: separately uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test
--browser chromium tests/browser. API changes require spectacular --validate --fail-on-warn. Container
changes require build, UID:GID10001:10001, static/bootstrap, rendered ports and actual smoke evidence.
TC-06. Four required CI jobs quality/test/security/container at exact reviewed head; no missing/
skipped/cancelled check passes. Report implementation CI separately from report-head checks. No
manifest refresh grants source-change authority. Independent ICA and human release are separate.
