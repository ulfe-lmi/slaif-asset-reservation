# Contributing

A bounded change is one pull request against a verified current `main`.
Before starting: read [AGENTS.md](AGENTS.md), read the linked issue and the
relevant architecture documents, verify current `main` and existing open PRs,
and do not begin from an unapproved broad feature description.

## Development environment

The executable workflow: Python 3.13 managed by `uv` with the committed
`uv.lock` (never edited by hand), and PostgreSQL 17 through the committed
development Compose file (loopback-only, development settings):

```bash
git clone <private-repo-url> slaif-asset-reservation && cd slaif-asset-reservation
docker compose up -d db                 # development PostgreSQL on 127.0.0.1:5432
uv sync --locked --all-groups           # locked dependencies
cp .env.example .env                    # host-side placeholders; do not commit a real .env
uv run --env-file .env python manage.py migrate
uv run --env-file .env python manage.py runserver
```

Notes:

- Django does not load `.env` automatically; host-side commands pass it
  explicitly with `uv run --env-file .env`. Its `DATABASE_URL` points at the
  loopback-published development database.
- Keep your working tree disposable-safe: run test and rehearsal commands in
  an owned disposable checkout with a synthetic `.env`, never in a valuable
  tree that holds real secrets. See [TESTING.md](TESTING.md).
- The committed Compose file is development-only; deployment uses the
  production-shaped example described in [INSTALL.md](INSTALL.md).

## Verification

The standard command set (exact variants and evidence rules in
[TESTING.md](TESTING.md)):

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run --env-file .env python manage.py check
uv run --env-file .env python manage.py makemigrations --check --dry-run
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test
uv run pip-audit
git diff --check
```

Report passed, failed, skipped, and unrun checks separately — a skipped or
unrun check is not a pass. API changes also require OpenAPI schema
validation; browser/UI boundaries use the explicit Chromium suite documented
in `TESTING.md`.

## Pull requests

- Keep scope and non-goals explicit; explain any operational impact.
- Use `.github/PULL_REQUEST_TEMPLATE.md`, including the verification table
  with exact commands and outcomes.
- Use `Closes #<issue>` when the PR fully satisfies that issue; leave
  incomplete issues open. The workflow's post-merge verification is
  documented in [docs/oap-workflow.md](docs/oap-workflow.md).
- Update user documentation, tests, and behavior together when they change.
- New dependencies need a stated purpose and a reviewed, locked version.

## Architecture changes

An architectural, security-boundary, persistence, authentication, or
deployment change requires an ADR under [docs/decisions/](docs/decisions/). A
feature PR must not smuggle in such a decision without review.

## Secrets and personal data

Do not place credentials, browser cookies, anti-forgery tokens, API tokens,
peppers, private client exports, reservation details, or production data in
commits, issues, PRs, fixtures, screenshots, or logs. The sanitized bootstrap
inventory under `data/bootstrap/` is the only legacy-derived data set the
repository carries, and it stays sanitized.

## Agent contributions

Development runs through the repository's OAP workflow
([docs/oap-workflow.md](docs/oap-workflow.md)): the role router is
[AGENTS.md](AGENTS.md), the active order defines the exact scope, and the
coding role never merges, self-approves, or adjudicates its own work.
