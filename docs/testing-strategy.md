# Testing Strategy

**Status:** required evidence model for all implementation PRs

## 1. Testing goals

Tests must prove domain invariants, authorization, concurrency, API stability, migration safety, and critical human workflows. Code volume or nominal coverage alone is not evidence.

## 2. Test layers

### Pure unit tests

Use for:

- interval validation and half-open semantics;
- policy resolution and denial reasons;
- scope parsing;
- token formatting/verifier helpers;
- time-zone conversion and ambiguous/nonexistent local time handling;
- canonical request hashing for idempotency;
- capability filter validation.

These tests should be fast and avoid the database where database behavior is not the subject.

### Django/database integration tests

Use PostgreSQL for:

- models and constraints;
- migrations;
- exclusion constraint behavior;
- transaction rollback;
- idempotency uniqueness/locking;
- audit write coupling;
- policy counters;
- release/cancellation effects;
- query authorization.

Do not use SQLite as proof of PostgreSQL-specific invariants.

### Concurrent tests

At minimum:

- two transactions race for the same exclusive range; exactly one commits;
- back-to-back reservations both commit;
- idempotent duplicate requests return one reservation;
- same idempotency key with a different request fails;
- simultaneous policy-limit requests cannot exceed the limit where the limit is enforced as hard policy.

Avoid tests that serialize the race accidentally through one transaction or one connection.

### API contract tests

Cover:

- authentication and scopes;
- filtering/pagination;
- exact create/read/cancel/release schemas;
- problem detail shape and stable `code`;
- 401/403/404/409/422 distinctions as accepted;
- request/correlation IDs;
- idempotency;
- OpenAPI generation and schema validation;
- no secret fields.

### Human web tests

Django view/form tests cover server behavior. Playwright covers selected end-to-end paths after UI exists:

- login/logout;
- browse/filter assets;
- create reservation;
- conflict response;
- cancel and release;
- token create-once and revoke;
- authorization boundaries;
- keyboard/accessibility smoke path.

Work Order 0005 adds token lifecycle tests for model constraints, scope validation, one-time
display, browser Back/history recovery, redaction, secret-safe object representations, Django
exception-report redaction, recursive audit metadata rejection, ORM bypass protection,
bearer-authenticator negative paths, exact expiry and last-use behavior, owner-only web routes,
CSRF, and Playwright creation/revocation coverage. The authenticator remains directly tested
without being enabled on API endpoints.

Work Order 0006 adds API tests for bearer endpoint authentication, scope checks, `/api/v1/me/`,
availability privacy, owner-only reservation list/detail/create/cancel/release, problem-details
shape, correlation IDs, idempotency replay/conflict behavior, and PostgreSQL-backed concurrent
idempotent creates.

### Migration tests

- bootstrap YAML schema validation;
- dry-run import creates no writes;
- import is idempotent;
- resource IDs and display names map correctly;
- disabled/excluded records remain correctly classified;
- no private clients are included;
- reconciliation totals and unmapped rows are reported;
- rollback/cutover procedure is tested on synthetic exports.

### Deployment smoke tests

- container image builds;
- migrations run against empty database;
- static assets collect/serve;
- liveness/readiness endpoints work;
- production settings fail fast when required secrets are absent;
- backup and restore drill against disposable data;
- upgrade from previous tagged schema once releases exist.

## 3. Critical test matrix

| Area | Positive evidence | Negative evidence |
|---|---|---|
| Reservation | valid exclusive range commits | overlap and invalid range reject |
| Boundaries | adjacent ranges commit | one-second overlap rejects |
| Policy | allowed user/duration commits | horizon, duration, group, concurrency deny |
| Auth | valid session/token works | expired/revoked/wrong-scope token fails |
| Ownership | owner cancels/releases | another user cannot mutate |
| Idempotency | replay returns same result | reused key with changed body conflicts |
| Audit | mutation creates safe event | rollback leaves no orphan event |
| Time | UTC and local display agree | DST ambiguous/nonexistent input not guessed |
| Inventory | verified asset filters correctly | inactive/hidden asset fails closed |
| Secrets | token shown once | token absent from DB/log/API afterward |

## 4. Property-based testing

Hypothesis is appropriate for:

- interval-overlap truth tables;
- duration and horizon boundaries;
- time-zone conversion cases;
- canonicalization/idempotency request hashing;
- policy precedence.

Property tests complement explicit examples and must be deterministic in CI with failure seeds reported.

## 5. Time control

Use a reviewed clock abstraction or a library such as `time-machine` for service tests. Avoid monkeypatching unrelated modules or relying on the wall clock. Database timestamps and application clock assumptions must be explicit.

## 6. Coverage

Set a meaningful baseline after core code exists. Suggested initial target:

- overall line coverage at least 85%;
- higher branch coverage for reservation, auth, policy, and token modules;
- no coverage target may justify shallow tests or excluding risky modules.

CI should publish a coverage artifact or summary. Coverage changes are reviewed, not blindly gated from the first scaffold PR.

## 7. Static and security checks

Expected tool categories:

- Ruff lint and formatting;
- mypy with Django typing support;
- Django system checks;
- migration drift check;
- dependency vulnerability audit;
- secret-pattern scan appropriate to the repository;
- `git diff --check`;
- YAML/JSON schema validation for bootstrap data.

A finding is triaged; do not silence a check merely to make CI green.

## 8. Standard commands

The scaffold PR establishes these exact commands:

```bash
uv sync --locked --all-groups
uv run playwright install --with-deps chromium
uv run ruff check .
uv run ruff format --check .
uv run mypy src
DATABASE_URL=postgres://slaif:slaif@localhost:5432/slaif_reservation uv run python manage.py check
DATABASE_URL=postgres://slaif:slaif@localhost:5432/slaif_reservation uv run python manage.py makemigrations --check --dry-run
DATABASE_URL=postgres://slaif:slaif@localhost:5432/slaif_reservation TEST_DATABASE_URL=postgres://slaif:slaif@localhost:5432/slaif_reservation uv run pytest
DATABASE_URL=postgres://slaif:slaif@localhost:5432/slaif_reservation TEST_DATABASE_URL=postgres://slaif:slaif@localhost:5432/slaif_reservation uv run pytest --browser chromium tests/browser
```

Provide `make` aliases only as conveniences; CI should use transparent commands or clearly report aliases.

Additional scaffold checks:

```bash
mkdir -p build/openapi
DATABASE_URL=postgres://slaif:slaif@localhost:5432/slaif_reservation uv run python manage.py spectacular --file build/openapi/schema.yaml --validate --fail-on-warn
uv run pip-audit
docker compose config
docker build --tag slaif-asset-reservation:local .
docker image inspect slaif-asset-reservation:local --format '{{.Config.User}}'
```

## 9. CI stages

Recommended initial jobs:

1. `quality`: Ruff, formatting, mypy, file/schema checks.
2. `test`: PostgreSQL service, migrations, pytest, coverage.
3. `security`: dependency audit and production-setting checks.
4. `container`: build smoke test after Dockerfile exists.

Required check names must remain unique and stable once branch protection references them.

## 10. Test-data rules

- synthetic users and reservations only;
- no copied SmartScheduling clients, appointments, emails, phone numbers, cookies, or secret URLs;
- hardware names from sanitized public inventory are acceptable;
- fake tokens use visibly non-production prefixes;
- screenshots are reviewed for private data before commit.

## 11. Reporting vocabulary

Every PR distinguishes:

- passed;
- failed;
- skipped;
- not run;
- environment blocked.

`All tests passed` is acceptable only when the stated relevant suite actually ran without failures or skips that matter to the acceptance criteria.

## 12. Release verification

Before alpha/beta release, run a verification-only task from the tagged commit in a clean environment. It must not edit files and reports:

- commit SHA;
- environment;
- exact commands/results;
- migrations;
- OpenAPI generation;
- container/deployment smoke;
- backup/restore evidence where required;
- unresolved warnings and limitations.
