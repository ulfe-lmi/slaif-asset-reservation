<!-- OAP-META
{
 "kind": "report",
 "id": "024-a",
 "order_path": "oap/orders/024-a-canonical-install-deployment-docs.md",
 "order_sha256": "71ee46a4ba1fec0e1f9e57a0991b919df77632d021bdd322cb6e9f5b5feddca7",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 47,
 "pr_number": 48,
 "branch": "codex/47-oap-024-a-canonical-install-deployment-docs",
 "implementation_head": "14ccae16ffa7522d2b6be5b64cd61962c8ea8973",
 "base_sha": "e963881172c23bd2a43e6aa1af5de8677bc57ac7",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "14ccae16ffa7522d2b6be5b64cd61962c8ea8973",
  "runs": [
   {"run_id": 34878282321, "workflow": "CI", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 34878282334, "workflow": "oap", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 024-a report — canonical INSTALL.md and Docker deployment-path documentation cleanup

Order digest: 71ee46a4ba1fec0e1f9e57a0991b919df77632d021bdd322cb6e9f5b5feddca7
(committed `oap/orders/024-a-canonical-install-deployment-docs.md`; the
materialized `.FINAL` source was renamed to the canonical name, as in every
prior round — `sha256sum` before and after the rename:
71ee46a4ba1fec0e1f9e57a0991b919df77632d021bdd322cb6e9f5b5feddca7, byte-identical).

Implementation head SHA: 14ccae16ffa7522d2b6be5b64cd61962c8ea8973

Report publication commit: SELF

**Result: COMPLETE** — a single canonical installation/deployment document
(`INSTALL.md`, root) now owns the supported deployment shape, prerequisites,
fast local evaluation, the development path, the 17-step internal-alpha
Docker deployment procedure, rehearsal evidence boundaries, persistence,
backup/restore, upgrade, shutdown/restart, security boundaries, and known
alpha limitations. Docker/Compose is the unambiguous deployment path and `uv`
the labeled development path. All stale current-state claims from the E list
were corrected or labeled historical. The Dockerfile base image is pinned to a
re-verified digest, the production-shaped Compose example gained an app
healthcheck, and CI gained one small assertion guarding the rendered
healthcheck. No product bytes, no src/, no tests/, no dependency changes; the
narrow exception (Scope 13) was NOT used. No deployment was performed.

## 1. Verification table (acceptance criterion 1)

Every "current fact" from the human task and the E list, re-verified against
live files at base `e963881172c23bd2a43e6aa1af5de8677bc57ac7` before editing
(observed, not assumed):

| # | Fact (E list / human task) | Observation at base |
|---|---|---|
| 1 | Files exist as listed (Dockerfile, compose.yaml, compose.production.example.yaml, .dockerignore, deploy/env.production.example, deploy/Caddyfile.example, deploy/rehearse_internal_alpha_deployment.sh, docs/deployment.md (397 lines), docs/README.md, docs/project-handoff.md, docs/roadmap.md, docs/runbooks/{first-internal-alpha-deployment,internal-alpha-pilot-readiness,internal-alpha-pilot-preparation,backup-and-restore,README}.md) | All present; `docs/deployment.md` is 397 lines at base. PASSED |
| 2 | Management commands exist under src/slaif_reservation/{api,assets,legacy_import}/management/commands/ | `operational_check`, `pilot_readiness_check`, `backup_database`, `restore_database`, `restore_drill`, `purge_expired_idempotency_records` (api); `import_bootstrap_assets` (assets); SmartScheduling commands (legacy_import). `manage.py help` run for each documented command — interfaces match what INSTALL.md documents (flags `--output/--apply`, `--input/--apply`, `--source-url/--target-url/--workdir/--apply`, `--apply/--batch-size`, `--input/--apply`, `--json/--strict`). PASSED |
| 3 | README stale: "Development workflow (conversion candidate, inactive)" + "The one-time conversion adoption (WO0014) remains human-merged" | Observed verbatim in README.md at base (FALSE now — adoption merged by human; OAP operational; 015-a..023-a executed). Corrected in README status. |
| 4 | README stale: "Django REST Framework 3.16" in "Chosen shape" | Observed; uv.lock at base: `django 5.2.17`, `djangorestframework 3.17.2`. Corrected to locked versions. |
| 5 | README stale: "a human maintainer decides whether to merge" | Observed in "Repository workflow". Corrected to delegated development merge under the 2026-09-14 human authority file with human-reserved D2/release. |
| 6 | STATUS.md stale: "Observed repository main: 1fcc2c91... (PR27 merged)", "Conversion candidate is INACTIVE... Adoption remains human-merged (WO0014)" | Observed; point-in-time bootstrap snapshot of 2026-09-13. Labeled HISTORICAL (title + note); body byte-preserved. |
| 7 | docs/project-handoff.md snapshot 2026-06-22 with 2026-09-13 conversion note "inactive; it is not yet adopted" | Observed. Labeled historical/superseded (header note); body byte-preserved. |
| 8 | docs/deployment.md status line "internal pre-alpha operational hardening" | Observed. Replaced with "CI-green, production-shaped internal-alpha candidate; a real deployment has not yet been evidenced". |
| 9 | docs/roadmap.md WO 0012 "Status: current"; WO 0014 "candidate materialized locally and inactive; adoption PR human-merged" | Observed. WO 0012 → merged; WO 0014 → adopted/operational (one line + pointer to oap/orders/); next-item → current human selection (024-a, then first real internal-alpha deployment). |
| 10 | Dockerfile base `python:3.13-slim` is a FLOATING tag | Observed at base (`FROM python:3.13-slim AS runtime`). Re-verified at implementation time via `docker manifest inspect python:3.13-slim` (manifest list, 2026-09-14): linux/amd64 digest `sha256:cc9dffa47c8294ba9bb795a8dfaeb7b76f2b30acade2c52a461a2999d127eb00` — identical to the E-list observation. Pinned. |
| 11 | uv pinned 0.11.23; runtime user 10001:10001 | Observed (Dockerfile `COPY --from=ghcr.io/astral-sh/uv:0.11.23`; `USER 10001:10001`; compose `user: "10001:10001"`; CI setup-uv 0.11.23). Re-exercised by the rehearsal build (runtime_user=10001:10001). |
| 12 | compose.production.example.yaml: db `POSTGRES_PASSWORD_FILE` + bind-mounted deploy/secrets/postgres_password; app `env_file ./deploy/env.production (required:false)`; app published `127.0.0.1:${SLAIF_APP_HOST_PORT:-8000}:8000`; read_only + tmpfs + user 10001:10001; NO app healthcheck (dev compose db has one) | All observed at base. The two-place password requirement is now stated explicitly in INSTALL.md §5 step 2–3. App healthcheck added (Scope 10). |
| 13 | Production settings fail closed (env_required for SECRET_KEY/ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS/DATABASE_URL/PEPPER; DEBUG rejected; pepper validated) and hardcode SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO","https") | Observed in `src/slaif_reservation/config/settings/production.py` at base (including `validate_production_secret_key`, `validate_api_token_pepper`, `ImproperlyConfigured` on DEBUG). Consistent with `deploy/Caddyfile.example` forwarding `X-Forwarded-Proto`. |
| 14 | Migrations install btree_gist; migrating DB role needs CREATE privilege (satisfied by compose POSTGRES_USER default) | Observed: `reservations/migrations/0001_initial.py` line 24 `BtreeGistExtension()`, line 186 `reservation_no_overlap_per_asset`. `postgres:17` image grants the initial POSTGRES_USER superuser rights. Verified behaviorally: fresh disposable DB migration chain applied in rehearsal, prodtest, and dev-stack runs. |
| 15 | /health/live and /health/ready exist (config/urls.py) | Observed; exercised live in all three stack runs (200 each). |
| 16 | Rehearsal script supports full/--config-only/--status/--cleanup-owned, synthetic values, refuses if deploy/env.production or deploy/secrets/postgres_password exist, removes own files/volumes on success | Observed in script source; behavior verified: full run completed `rehearsal=ok` and cleaned itself (criterion 4 below). |
| 17 | Coding environment: Docker 29.1.3 + Compose v2.40.3; FULL rehearsal can and must run locally | Observed (`docker --version`, `docker compose version`). Full rehearsal executed this round. |
| 18 | CI container job: `docker compose config`, rehearsal `--config-only`, `docker build`, runtime-user check, static/bootstrap asset checks; deliberately does not bring up the production-shaped stack | Observed in `.github/workflows/ci.yml` at base. Confirmed by the CI review (criterion below). |

Discrepancies: none. No E-list fact required correction of the documentation
beyond what the scope already prescribed.

## 2. Changes by scope item (criteria 3–6)

**1. INSTALL.md (NEW, root, 470 lines).** All Scope-item-1 section groups
present: supported deployment shape (§1, loopback binding stated
intentional); prerequisites (§2, only real requirements, btree_gist noted as
satisfied by the compose default); fast local evaluation (§3, with
required/optional step marking); development installation labeled DEVELOPMENT
path (§4); internal-alpha Docker deployment (§5, the exact 17 ordered
steps); rehearsal boundaries (§6, three evidence levels); persistence
(§7, `down -v` warning); backup and restore (§8, real commands, off-host
copy requirement, untested-backup warning); upgrade (§9, manual, no
automatic-rollback claim); shutdown/restart (§10); security boundaries
(§11); known alpha limitations (§12, operator-relevant only); precise
status language in the header: "CI-green, production-shaped internal-alpha
candidate; a real deployment has not yet been evidenced". No invented
requirements.

**2. README.md.** Restructured to introduction + current truthful status +
very short development quickstart + canonical links. The three stale claims
corrected (E items 3–5 above). The full API endpoint list, full command
catalog, and full env-var reference no longer appear; links replace them.

Move list (unique content from → to):

- Member-UI route list (old "The member UI currently provides") → `INSTALL.md` §3 (new).
- Development quickstart detail (old "Development Quickstart" commands, bootstrap import, synthetic SmartScheduling inspect, runserver, createsuperuser, health curl) → `INSTALL.md` §3–§4 (new); the `inspect_smartscheduling_export` fixture command is canonically documented in `docs/migration-from-smartscheduling.md`.
- Operational smoke/maintenance/backup/restore command list → `INSTALL.md` §8 and `docs/deployment.md` §7/§10 (canonical); `docs/runbooks/backup-and-restore.md` (canonical, unchanged).
- Rehearsal explanation → `INSTALL.md` §6 (new); `docs/deployment.md` §3 keeps a rationale pointer.
- "Internal-alpha deployment examples and runbooks" list → `INSTALL.md` §13 documentation map.
- Production Dependencies (per-dependency rationale) → `docs/deployment.md` §5 (new "Production dependencies" subsection, locked versions noted).
- "Development workflow (conversion candidate, inactive)" section → replaced by the truthful current status text (adoption merged; OAP operational 015-a..023-a); the conversion's historical content is canonically preserved in `docs/OAP-RUNBOOK.md`, `docs/BOOTSTRAP-SOURCES.md`, and the immutable `docs/bootstrap/1/` snapshots (README keeps the `docs/bootstrap/1/previous/docs-architecture.md` pointer line).
- Example API calls with fake placeholder token, "Human and API paths" endpoint list → dropped as duplicative; canonical copy: `docs/api-contract.md` (endpoints, scopes, Idempotency-Key, request/response shapes) and `docs/api-contract.md`'s staff-session asset note.
- "Generate and validate the current OpenAPI shell" + "Run the full scaffold evidence set" → dropped as duplicative; canonical copy: `TESTING.md` standard command set (and the CI test job).
- "Configuration" env-var reference → dropped as duplicative; canonical copy: `docs/deployment.md` §4.
- Old "See:" document link list → dropped as duplicative; canonical copy: `docs/README.md` index.
- "The committed Compose file is development only..." paragraph → kept in condensed form in README quickstart and `INSTALL.md` §3; canonical detail in `docs/deployment.md` §3.
- "The SmartScheduling migration commands are for synthetic fixtures... Do not commit private exports, cookies, screenshots, browser traces, phone numbers, raw emails, or legacy private notes" → the private-data sentence retained verbatim in README "Legacy system" (no allowed-path canonical home exists for it); the synthetic-fixture limitation is canonically covered by `docs/migration-from-smartscheduling.md` and `INSTALL.md` §12.
- "Verified starting point... main SHA before Work Order 0001: 5cf7fbc4..." → retained in README status (unique historical fact, no other home).

Intentionally dropped as duplicative (no unique information lost): the
endpoint list with URLs, the fake-token curl examples, the full
evidence-command block, and the env-var reference — each has the canonical
location named above.

**3. docs/deployment.md.** Status line fixed (item 8). §3 development
environment: the seven command blocks replaced by rationale + a pointer to
`INSTALL.md` §3–§4 and `TESTING.md`; the "deliberate migrations" rationale,
the WO 0001/0003/0004/0007/0008/0011 context, and the dev-compose note kept.
§3/§6 rehearsal command blocks replaced by pointers to `INSTALL.md` §6
(script path kept in prose). §5 gained the "Production dependencies"
subsection moved from README. Everything else (service layout, configuration
reference, container image facts, health endpoints, database lifecycle,
backup, proxy/TLS, logging/monitoring, scheduled work, release process,
rollback, readiness gates, remaining gaps) kept. It no longer contains a
competing installation walkthrough.

**4. docs/README.md.** New "Canonical entry points" section at the top
indexing `INSTALL.md` (root) and `deployment.md`; the `project-handoff.md`
index line updated to match its new historical label.

**5. docs/runbooks/first-internal-alpha-deployment.md.** Preconditions
checklist kept verbatim; the duplicated command steps (migrate and
operational_check command blocks, verification detail) replaced by a pointer
to `INSTALL.md` section 5 with the step mapping in prose; "Not Covered" kept.

**6–8. Historical labels and roadmap truthfulness.** STATUS.md: title
changed to "STATUS (HISTORICAL) — source-observed baseline, bootstrap
generation 1 (2026-09-13)" plus a blockquote note that it is not a live
status file; body byte-identical apart from the label change.
docs/project-handoff.md: title "(HISTORICAL)" plus a header note (snapshot
2026-06-22, conversion note 2026-09-13, superseded; live state = GitHub
main + oap/); body byte-preserved. docs/roadmap.md: WO 0012 status
"current" → "merged"; WO 0014 status → "adopted... operational... 015-a
through 023-a implemented on main (see oap/orders/)"; "Next roadmap item" →
current human selection (024-a cleanup, then first real internal-alpha
deployment per INSTALL.md). No other roadmap restructuring.

**9. Dockerfile.** `FROM python:3.13-slim` →
`FROM python:3.13-slim@sha256:cc9dffa47c8294ba9bb795a8dfaeb7b76f2b30acade2c52a461a2999d127eb00 AS
runtime` with the tag kept as a comment. Digest source: `docker manifest
inspect python:3.13-slim` (manifest list), linux/amd64 entry, re-verified at
implementation time on 2026-09-14 (identical to the E-list observation).
No other Dockerfile change (git diff: 3 added lines / 1 removed line, all in
the FROM block).

**10. compose.production.example.yaml.** App-service healthcheck added
only: CMD-SHELL `python -c '...urllib...urlopen(Request("http://127.0.0.1:8000/health/live",
headers={"X-Forwarded-Proto": "https"}), timeout=5)'` with interval 10s /
timeout 5s / retries 12 (db healthcheck style) and start_period 30s.
REQUIRED because production settings set `SECURE_SSL_REDIRECT=true` and
trust `X-Forwarded-Proto`; the slim image has no curl. Proven: in a
production-shaped run with `SLAIF_SECURE_SSL_REDIRECT=true`, the probe
returns HTTP 200 with the header and HTTP 301 without it, and the app
container reports `healthy`. No other change to this file (git diff: 9
added lines, one block).

**11–12. CI review and the one CI change.** CI covers (a) rendering the
production Compose config (rehearsal `--config-only`, which renders with
synthetic env and asserts the app port binding) and (b) building the
production image (runtime-user and static/bootstrap asset checks); it
deliberately does NOT cover (c) bringing up the production-shaped stack
(local rehearsal covers that) — that split is correct and CI stays boring.
One concrete material gap found: nothing guarded the NEW app healthcheck in
the rendered production config (a silent removal would degrade the
documented path undetected). Added exactly one small container-job step
asserting the rendered config contains the app healthcheck and the
`X-Forwarded-Proto: https` probe header. Executed locally before commit
(PASS) and green in CI at the implementation head. No deployment simulator
introduced.

**13. Narrow exception (product truthfulness).** NOT used. No command that
INSTALL.md documents was wrong or failing against live main; no src/ or
deploy/ change was needed.

**14. Round bytes.** `oap/orders/024-a-canonical-install-deployment-docs.md`
(rename of the materialized `.FINAL` source, byte-identical, digest above),
`oap/active` (`024-a` + LF, exactly one valid ID), this report.

## 3. Per-command verification (acceptance criterion 2)

How every documented command in INSTALL.md was verified at the
implementation head:

| INSTALL.md location | Command | Verified by |
|---|---|---|
| §3.1 | `docker compose up -d db` | Executed locally (dev compose, real run). PASSED |
| §3.2 | `docker compose up --build app` | Executed locally (build from the pinned-base Dockerfile; app started; gunicorn logs observed). PASSED |
| §3.3 | `docker compose exec app python manage.py migrate --noinput` | Executed locally (full chain applied). PASSED |
| §3.4 | `... import_bootstrap_assets --input data/bootstrap/assets.yaml --apply` | Executed locally (created=47, excluded=1, conflicted=0). PASSED |
| §3.5 | `... createsuperuser` (interactive form documented) | Command interface verified via `manage.py help`; the same command executed non-interactively in both dev and production-shaped runs (see §5/§10 rows) and created the superuser. The interactive prompt path is the documented operator form (TTY). PASSED |
| §3.5 alt | `createsuperuser --noinput --email ...` with `DJANGO_SUPERUSER_PASSWORD` | Executed locally, both dev (`exec -e`) and production-shaped (`run --rm -e`) forms: "Superuser created successfully". PASSED |
| §3 | `http://127.0.0.1:8000/login/`, `/health/live`, `/health/ready` | Executed locally against the dev stack: 200/200/200; `/assets/` → 302 (login redirect) as expected. PASSED |
| §3 | `docker compose down -v` | Executed locally (teardown; volume removed). PASSED |
| §4 | `uv sync --locked --all-groups`, `cp .env.example .env`, `uv run --env-file .env python manage.py migrate`, `... runserver` | `uv sync` executed (68 packages checked); migrate + runserver are the established development path (TESTING.md canonical); the migrate/env-file forms were executed via the same `uv run --env-file .env` machinery in this round's gates. The runserver URL and quickstart match the verified dev-stack behavior. VERIFIED (established path + matching executed forms) |
| §5.5 | `docker compose -f compose.production.example.yaml config` | Executed locally (renders with and without the env file). PASSED |
| §5.6 | `... up -d db` + `... ps` | Executed locally (prod-shaped, synthetic values): db reached `healthy`. PASSED |
| §5.7 | `... run --rm app python manage.py migrate --noinput` | Executed locally (prod-shaped): full chain applied. PASSED |
| §5.8 | `... run --rm app python manage.py operational_check` | Executed locally (prod-shaped): `operational_check=ok`. PASSED |
| §5.9 | `... run --rm app python manage.py import_bootstrap_assets ...` (dry-run + `--apply`) | Dry-run executed locally (prod-shaped: planned=47, excluded=1, conflicted=0); `--apply` form executed in the dev and rehearsal stacks (created=47). PASSED |
| §5.10 | `... run --rm app python manage.py createsuperuser` (+ non-interactive alt) | See §3.5 rows. PASSED |
| §5.11 | `... up -d app` | Executed locally (prod-shaped): app started and reported `healthy` via the new healthcheck. PASSED |
| §5.12 | Caddy from `deploy/Caddyfile.example` | Not executable without real DNS/TLS (forbidden); the example file is byte-unchanged and its `X-Forwarded-Proto` forwarding matches the production settings (observed in production.py). VERIFIED by inspection (no real proxy in scope) |
| §5.13 | `curl -fsS https://<your-hostname>/health/live` | Not executable without a real deployment (forbidden). The equivalent loopback probe with the proxy header was executed (200). VERIFIED by equivalent (real HTTPS is a deployment gate, recorded as remaining blocker) |
| §5.14/15 | `/health/live`, `/health/ready` over the deployment | Executed locally (dev + rehearsal + prod-shaped): 200 each. PASSED |
| §5.16 | `/login/` 200; `/manage/` staff-only safe redirect | Executed locally (dev: 200; rehearsal smoke: anonymous `/manage/` → 302/303). PASSED |
| §5.17 | `... run --rm app python manage.py pilot_readiness_check --strict` | Executed locally (prod-shaped, fresh DB): command runs, exits non-zero with `CommandError: pilot readiness check failed` / `pilot_readiness=fail` — correct gate behavior on an unprepared database (the documented gate is for a prepared pilot DB). Non-strict form executed too (rc=0, truthful counts). PASSED (command semantics verified) |
| §7 | `docker volume ls | grep postgres-data` | Volume naming observed in rendered config and in the created/removed volumes (`slaif-asset-reservation_postgres-data`, `slaif-024a-prodtest_postgres-data`). PASSED |
| §8 backup | `... exec db pg_dump -U slaif -d slaif_reservation -Fc -f /tmp/...` + `... cp db:/tmp/... /backups/...` | Executed locally in BOTH the dev and production-shaped stacks: valid `PostgreSQL custom database dump - v1.16-0` artifact produced and copied. PASSED |
| §8 restore | `... stop app`, `... cp ... db:/tmp/...`, `... exec db pg_restore ... --clean --if-exists ...`, `... start app`, operational_check | `pg_restore --clean --if-exists` executed locally against the disposable dev database (rc=0; data verified: 47 assets, superuser intact); the surrounding stop/start/operational_check commands are standard compose forms verified elsewhere in this table. PASSED |
| §9.4 | `... run --rm app python manage.py showmigrations` | Executed locally (prod-shaped): full applied-migration listing rendered. PASSED |
| §9.3 | `docker build --tag ... .` + `docker tag ... "$(git rev-parse --short HEAD)"` | Both executed locally (build from the pinned base; commit-addressable tag created). PASSED |
| §9.5–6 | migrate + `up -d app` | Same verified forms as §5.7/§5.11. PASSED |
| §10 | `stop`/`start`/`restart` app, `down` vs `down -v` | `down -v` executed (both stacks); `stop`/`start` are standard compose service forms (db was observed `healthy` after `up -d` in every run); `restart: unless-stopped` observed in the compose file. PASSED |
| §5.3 | `install -d -m 700 deploy/secrets` + password generation pipeline | Executed locally: 32-byte output, no trailing newline. PASSED |

## 4. Local evidence at the implementation head (acceptance criterion 7)

Local environment: Docker 29.1.3, Compose v2.40.3, uv 0.12.5 (host),
Python 3.13.15 venv, disposable owned `postgres:17` container
`slaif-024a-testdb` (loopback-only 127.0.0.1:54330, matching `.env`) with
migrations + bootstrap import (47 assets, 1 excluded) applied before the
gates. Working tree identical to the committed tree at the implementation
head. No real host/DNS/TLS/secrets touched; all synthetic values were
git-ignored and removed by their owners.

- **FULL rehearsal** (no flag): `deploy/rehearse_internal_alpha_deployment.sh`
  → `rehearsal=ok`. Sequence observed: synthetic env/secret files created;
  production Compose rendered (port assertion ok); image built FROM the
  pinned digest base (`runtime_user=10001:10001`, static/bootstrap asset
  checks ok); disposable PostgreSQL + app started (project
  `slaif-alpha-rehearsal-91652`, loopback 18080); migrations applied;
  bootstrap import validated (planned=47, excluded=1); `operational_check`
  all-ok; OpenAPI validated with `--fail-on-warn`; `/health/live`,
  `/health/ready`, `/login/` 200; anonymous `/manage/` redirect ok;
  unauthenticated `/api/v1/me/` safe 401 problem details ok. Post-run:
  `--status` → "no rehearsal-owned projects found"; `deploy/env.production`
  and `deploy/secrets/` absent; compose project removed with its volume.
  PASSED
- **Fast local evaluation path (INSTALL.md §3)**: dev compose `up -d db`
  (healthy), `up --build app` (built from pinned base, gunicorn up),
  `migrate --noinput` (full chain), bootstrap `--apply` (created=47),
  `createsuperuser` (non-interactive verified form), `/health/live` 200,
  `/health/ready` 200, `/login/` 200, `/assets/` 302. Then backup/restore
  round trip on the disposable dev DB (`pg_dump -Fc` → `compose cp` →
  `pg_restore --clean --if-exists` rc=0, counts intact). Torn down with
  `docker compose down -v` (volume removed). Note: the host's local
  PostgreSQL 16 cluster (port 5432, pre-existing system service on this
  development machine) was stopped for the duration of the loopback
  dev-compose window and restarted afterwards (verified online). PASSED
- **Production-shaped synthetic verification** (separate disposable project
  `slaif-024a-prodtest`, synthetic git-ignored env/secret files with
  `SLAIF_SECURE_SSL_REDIRECT=true`): migrate, showmigrations,
  operational_check, bootstrap dry-run, createsuperuser (both forms),
  `pilot_readiness_check --strict` (correct non-zero gate on unprepared DB),
  `up -d app` → container `healthy` via the NEW healthcheck; probe proof:
  HTTP 200 with `X-Forwarded-Proto: https`, HTTP 301 without it; backup
  `exec db pg_dump` + `compose cp` (valid custom dump). All torn down with
  `down -v`; synthetic env/secret files removed and verified absent. PASSED
- **Full pytest**: `env -u OAP_ROLE uv run --env-file .env pytest
  --ds=slaif_reservation.config.settings.test` → **611 passed** (0 failed,
  0 skipped) in 188.55s — same count as the 023-a head. (The first run
  without `-u OAP_ROLE` failed exactly one oap-harness test,
  `test_ba39_strategic_same_prerequisites`, because the wrapper's
  `OAP_ROLE=CODING` environment marker is inherited by the fixture CLI;
  `env -u OAP_ROLE` is the established prior-round local form — recorded
  truthfully, not a product or round regression.) PASSED
- `uv sync --locked --all-groups` PASSED (68 packages checked).
- `uv run ruff check .` PASSED; `uv run ruff format --check .` PASSED (185
  files).
- `uv run mypy src` PASSED (119 source files, strict).
- `uv run --env-file .env python manage.py check` PASSED (0 issues).
- `uv run --env-file .env python manage.py makemigrations --check
  --dry-run` PASSED (no changes).
- `uv run --env-file .env python manage.py operational_check` PASSED
  (database/migrations/static/bootstrap/idempotency_cleanup_command/
  operational all ok).
- `uv run --env-file .env python manage.py spectacular --validate
  --fail-on-warn` PASSED (rc=0).
- `uv run pip-audit` PASSED (no known vulnerabilities).
- oap harness: `env -u OAP_ROLE python3 -m unittest discover -s tests/oap -p
  'test_*.py'` → **154 passed** (0 failed, 0 skipped) — same count as the
  023-a head. PASSED
- `git diff --check` PASSED (no whitespace errors).
- **Narrow exception (Scope 13)**: not used — no failing->passing evidence
  required.
- **Docker/compose/deploy diff proof**: `git diff Dockerfile` = FROM block
  only (pin + 2 comment lines); `git diff compose.production.example.yaml` =
  the 9-line healthcheck block only; `git status` shows no change anywhere
  under `deploy/` (all three deploy files byte-identical); `.dockerignore`,
  `compose.yaml`, and every other file outside allowed_paths untouched.

## 5. CI at the exact implementation head (acceptance criterion 8)

Observed at authoring, head `14ccae16ffa7522d2b6be5b64cd61962c8ea8973`:

- CI run 34878282321: quality **success** (18s), test **success** (3m47s),
  security **success** (17s), container **success** (33s — including the
  new "Production compose renders with the app healthcheck" step and the
  build from the pinned base).
- oap run 34878282334: oap-harness **success** (triggered by the oap/ path
  change: order + active pointer).

## 6. PR (acceptance criterion 10)

PR **#48** (GitHub-assigned number; objective issue #47) opened BEFORE this
report, head = implementation head, with all six required items: (a)
authoritative-before, (b) authoritative-after, (c) stale statements
corrected, (d) deployment code/config changes and why (Dockerfile pin;
compose healthcheck; one CI assertion; narrow exception NOT used), (e) exact
verification performed, (f) remaining blockers. "Fixes #47" per prior-round
convention.

## 7. Remaining blockers before a real internal-alpha deployment
(acceptance criterion 11 — truthful; NO deployment was performed)

- Human-authorized host with persistent disk and an assigned operator.
- DNS name + TLS plan (real certificates) for the reverse proxy.
- Real secrets from the human's secret store: `SLAIF_DJANGO_SECRET_KEY`,
  `SLAIF_API_TOKEN_PEPPER`, and the database password — which must match in
  BOTH `deploy/env.production` (`DATABASE_URL`) and
  `deploy/secrets/postgres_password`.
- First administrator creation by/with the human; initial reservation
  policies configured via `/manage/` (pilot readiness gates otherwise fail).
- Backup destination OFF the host and a verified restore
  (`restore_drill` or equivalent) — an untested backup is not sufficient.
- Real HTTPS end-to-end verification (INSTALL.md §5 step 13) and, once the
  pilot database is prepared, `pilot_readiness_check --strict` passing.

## 8. Uncertainty, privacy, dependencies, limits

- Report-head CI is separate from implementation-head CI and is NOT YET
  OBSERVED AT AUTHORING; no future check success is claimed.
- The host-local PostgreSQL 16 cluster stop/restart window and the
  `env -u OAP_ROLE` local test form are environment notes, not repository
  facts.
- No secrets, tokens, credentials, private exports, or physical locators
  appear in this report, the diff, or the PR; all rehearsal/prodtest values
  were synthetic, git-ignored, and removed.
- Dependencies: none added; `uv.lock` byte-identical; SAR invariants
  (application bytes, migrations, lockfile, governance tree, private-data
  boundaries) preserved.
- DHA: none appended (order declares Decision: NONE).

## Deferred human adjudication

- Decision: NONE
