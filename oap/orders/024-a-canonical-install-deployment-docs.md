<!-- OAP-META
{
 "id": "024-a",
 "round": "a",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "base_sha": "e963881172c23bd2a43e6aa1af5de8677bc57ac7",
 "issue_number": 47,
 "branch": "codex/47-oap-024-a-canonical-install-deployment-docs",
 "pr_mode": "CREATE_OR_RESUME",
 "previous_round": null,
 "allowed_paths": [
  "INSTALL.md (NEW, root)",
  "README.md",
  "STATUS.md",
  "docs/README.md",
  "docs/deployment.md",
  "docs/project-handoff.md",
  "docs/roadmap.md",
  "docs/runbooks/first-internal-alpha-deployment.md",
  "Dockerfile (base-image pin only, plus the digest comment line)",
  "compose.production.example.yaml (app healthcheck block only)",
  ".github/workflows/ci.yml (ONLY if the ordered CI review finds one concrete material gap; record why)",
  "oap/orders/024-a-canonical-install-deployment-docs.md",
  "oap/active",
  "oap/reports/024-a-canonical-install-deployment-docs.md"
 ],
 "forbidden_resources": [
  "any other src/ change (no features, no refactors, no behavior change; the single narrow exception below is the only permitted src/ touch)",
  "any change under tests/ (no new or modified tests; no product test churn)",
  "pyproject.toml, uv.lock, or any dependency change",
  "any other .github/ change",
  "any change under oap/bin/ (helpers stay untouched)",
  "any other oap/ file (no OAP expansion: no new canary, protocol, transport, role, or governance document)",
  "compose.yaml (dev compose is unchanged; its loopback-only local credentials are documented dev convenience, not a defect to fix)",
  "deploy/rehearse_internal_alpha_deployment.sh (only via the narrow exception if it actually obstructs a documented path; otherwise byte-identical)",
  "deploy/env.production.example, deploy/Caddyfile.example (only via the narrow exception if a placeholder/header is actually wrong; otherwise byte-identical)",
  "any other docs/ file, AGENTS.md, ARCHITECTURE*.md, PLAN.md, CRITICAL.md, OAP-*.md, TESTING.md, SECURITY.md, CONTRIBUTING.md, BOOTSTRAP_INSTRUCTIONS.md",
  "data/, migrations, or any product byte",
  "deployment of any kind (the disposable synthetic rehearsal is the established exception; no real DNS/TLS/certificates/hosts)",
  "real secrets in Git, the diff, prompts, or logs (rehearsal creates synthetic git-ignored values only and removes them itself)",
  "Kubernetes, Swarm, Helm, Terraform, Ansible, Celery, Redis, or any new deployment platform",
  "any mutating GitHub operation except pushing this branch and opening this objective's PR",
  "merging or auto-merging any PR (merge is strategy's delegated act after exact-head review)",
  "ICA activity or milestone-completion claims",
  "credentials, auth files, sessions, tokens, auth homes"
 ]
}
-->

# 024-a — Canonical INSTALL.md and Docker deployment-path documentation cleanup

## Goal

Establish ONE clear installation/deployment path for the current internal-alpha
system. A competent Linux administrator who has never seen this repository must
be able to clone it, understand what is supported, and bring up the application
with Docker/Compose from a single canonical root-level `INSTALL.md` — without
reconstructing the procedure from the README plus three runbooks plus the
Compose files. Make Docker/Compose the unambiguous deployment path, keep the
`uv` workflow clearly the development path, correct stale current-state
claims, and apply small deployment-config fixes ONLY where they materially
obstruct or misrepresent the documented path. No product features, no OAP
expansion, no real deployment in this PR.

## Durable provenance and requirements

- H: in-session human principal instruction 2026-09-14 (bounded
  deployment/documentation cleanup task: canonical INSTALL.md, Docker as the
  deployment path, doc rationalization, stale-status correction, reduced
  noise, real verification of the written instructions, one bounded cleanup
  PR; no premature features; precise status language; "do not deploy to a
  real host as part of this cleanup PR").
- A: S-05 (one canonical current document; no silently dropped content),
  S-06 (bounded routine engineering), S-12 (proof-sized objective; H/A/E/I/C),
  S-15 (report boundary; truthful evidence), S-16/S-17 (exact-head review;
  delegated development merge), S-19 (rehearsal is synthetic evidence only;
  name exact commands/results), S-21 (no secrets in artifacts), S-22
  (development acceptance stays separate from deployment).
- E: strategy-verified at live main e963881172c23bd2a43e6aa1af5de8677bc57ac7
  (2026-09-14; coding re-verifies each item and records it — verify, do not
  assume):
  - Files exist as listed in the human task: Dockerfile, compose.yaml,
    compose.production.example.yaml, .dockerignore, deploy/env.production.
    example, deploy/Caddyfile.example, deploy/rehearse_internal_alpha_
    deployment.sh, docs/deployment.md (397 lines), docs/README.md, docs/
    project-handoff.md, docs/roadmap.md, docs/runbooks/{first-internal-alpha-
    deployment.md, internal-alpha-pilot-readiness.md, internal-alpha-pilot-
    preparation.md, backup-and-restore.md, README.md}, backup/restore/
    restore_drill/operational_check/pilot_readiness_check management commands
    (under src/slaif_reservation/{api,assets}/management/commands/),
    production settings, uv dev workflow.
  - Stale claims to correct (all observed in live files at base):
    README.md "Development workflow (conversion candidate, inactive)" section
    and "The one-time conversion adoption (WO0014) remains human-merged"
    (FALSE now: adoption merged by human; Concentrated OAP operational —
    objectives 015-a through 023-a executed, main currently e963881);
    README "Chosen shape" lists "Django REST Framework 3.16" (uv.lock:
    djangorestframework 3.17.2, django 5.2.17); README "Repository workflow"
    says "a human maintainer decides whether to merge" (now: strategy reviews
    and performs delegated development merges per the 2026-09-14 human
    authority file; humans retain D2/release/deployment decisions);
    STATUS.md "Observed repository main: 1fcc2c91... (PR27 merged)" and
    "Conversion candidate is INACTIVE... Adoption remains human-merged (WO0014)"
    (point-in-time bootstrap snapshot of 2026-09-13 — fundamentally historical;
    label, do not patch); docs/project-handoff.md (snapshot date 2026-06-22,
    with a 2026-09-13 conversion note saying "inactive; it is not yet adopted"
    — historical snapshot; label, do not rewrite); docs/deployment.md status
    line "internal pre-alpha operational hardening" (now: internal alpha, CI
    green, no real deployment yet); docs/roadmap.md WO 0012 "Status: current"
    (merged) and WO 0014 "candidate materialized locally and inactive;
    adoption PR human-merged" (adopted and merged; OAP operational since;
    015-a..023-a implemented on top).
  - Deployment-layer observations: Dockerfile base `python:3.13-slim` is a
    FLOATING tag (digest observed 2026-09-14:
    sha256:cc9dffa47c8294ba9bb795a8dfaeb7b76f2b30acade2c52a461a2999d127eb00 —
    re-verify with `docker manifest inspect` at implementation time and pin
    the then-current digest); uv pinned 0.11.23; runtime user 10001:10001;
    statics + data/bootstrap collected at build; compose.production.example.
    yaml: db uses POSTGRES_PASSWORD_FILE + bind-mounted
    deploy/secrets/postgres_password, app uses env_file
    ./deploy/env.production (required:false), app published
    127.0.0.1:${SLAIF_APP_HOST_PORT:-8000}:8000, read_only + tmpfs + user
    10001:10001, NO app healthcheck (dev compose db has one); the database
    password is structurally required in TWO places (db container secret file
    + DATABASE_URL in deploy/env.production) — INSTALL.md must state this
    explicitly, not hide it; the production image tag
    slaif-asset-reservation:internal-alpha is mutable — INSTALL.md must
    document building at a reviewed commit and tagging with the commit SHA
    (retain the previous tag for application rollback; no release platform);
    production settings fail closed (env_required for SECRET_KEY/ALLOWED_
    HOSTS/CSRF_TRUSTED_ORIGINS/DATABASE_URL/PEPPER; DEBUG rejected; pepper
    validated) and hardcode SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO",
    "https"), consistent with deploy/Caddyfile.example forwarding
    X-Forwarded-Proto; migrations install btree_gist (reservations/
    0001_initial.py BtreeGistExtension) so the migrating DB role needs CREATE
    privilege (satisfied by the compose POSTGRES_USER default); /health/live
    and /health/ready exist (config/urls.py); the rehearsal script supports
    full / --config-only / --status / --cleanup-owned, uses synthetic values,
    refuses to start if deploy/env.production or deploy/secrets/postgres_
    password already exist, and removes its own files/volumes on success.
  - Coding environment: Docker 29.1.3 + Compose v2.40.3 available — the FULL
    rehearsal can and must be run locally this round (not only --config-only).
  - CI (ci.yml container job) already: `docker compose config`, rehearsal
    --config-only, `docker build` of the production image, runtime-user
    check, static/bootstrap asset presence checks. It deliberately does NOT
    bring up the production-shaped stack (the local rehearsal covers that);
    keep CI boring — no deployment simulator.
- C: S-19 (synthetic rehearsal evidence only; no real deployment claim),
  S-21 (no secrets), S-22 (do not call it production-ready or deployed),
  SAR invariants preserved: application/product bytes, migrations, lockfile,
  governance tree, and private-data boundaries unchanged.

## Current reconciled state and prerequisites

- Base main (local and remote): e963881172c23bd2a43e6aa1af5de8677bc57ac7
  (023-a quiescent). Worktree clean on main; oap/active absent (INACTIVE).
- Fresh round: no local/remote branch codex/47-oap-024-a-canonical-install-
  deployment-docs, no PR for issue #47 (verify with git ls-remote and gh
  before creation); pr_mode CREATE_OR_RESUME resolves to CREATE. Record the
  GitHub-assigned PR number truthfully.
- The known oap-harness canary flake was fixed in 023-a; if oap-harness fails
  at the implementation head for an unrelated reason, record it truthfully
  and re-run the failed job at the SAME head (no workaround commits).

## Ordered read set

Standard compact read set, plus (read before writing anything):
README.md (in full), STATUS.md, docs/README.md, docs/deployment.md (in full),
docs/project-handoff.md, docs/roadmap.md, docs/runbooks/first-internal-alpha-
deployment.md, docs/runbooks/internal-alpha-pilot-readiness.md, docs/runbooks/
internal-alpha-pilot-preparation.md, docs/runbooks/backup-and-restore.md,
Dockerfile, compose.yaml, compose.production.example.yaml, .dockerignore,
deploy/env.production.example, deploy/Caddyfile.example, deploy/rehearse_
internal_alpha_deployment.sh, src/slaif_reservation/config/settings/
production.py, src/slaif_reservation/config/urls.py (health routes), the
management command listing (operational_check, pilot_readiness_check,
backup_database, restore_database, restore_drill, purge_expired_
idempotency_records, import_bootstrap_assets), pyproject.toml + uv.lock
(django/djangorestframework versions), .github/workflows/ci.yml.

## Scope and allowed paths

1. INSTALL.md (NEW, root) — the canonical installation/deployment document.
   Concise enough to use, complete enough to install. Must cover, at minimum:
   - Supported deployment shape: client -> HTTPS reverse proxy (Caddy or
     equivalent) -> Django/Gunicorn container bound to 127.0.0.1 ->
     PostgreSQL container on the private Compose network; state explicitly
     that loopback binding is intentional and external access comes only via
     the proxy.
   - Prerequisites: what the repository actually requires (Linux host;
     Docker Engine; Docker Compose v2; for real HTTPS: a DNS name + TLS plan;
     persistent disk for the postgres-data volume; outbound connectivity for
     image pulls; the migrating DB role must be able to CREATE the btree_gist
     extension — satisfied by the compose default user). No invented
     requirements.
   - Fast local evaluation: the shortest truthful Docker path (compose.yaml
     dev stack: up db, build/start app, deliberate migrate, bootstrap import,
     createsuperuser, login URL), including exactly which steps are required.
   - Development installation: the existing uv + Python workflow, labeled
     clearly as the DEVELOPMENT path, not the recommended long-running
     service deployment.
   - Internal-alpha Docker deployment: explicit linear procedure: (1)
     clone/checkout the reviewed commit; (2) copy deploy/env.production.
     example to deploy/env.production; (3) create secrets outside Git (env
     file values AND deploy/secrets/postgres_password — state that the
     database password must match in both places and how to generate them);
     (4) build the image at the reviewed commit (tag with the commit SHA,
     e.g. slaif-asset-reservation:$(git rev-parse --short HEAD), and note the
     compose example expects slaif-asset-reservation:internal-alpha —
     document building the example tag at the reviewed commit); (5)
     docker compose -f compose.production.example.yaml config to render/
     validate; (6) start PostgreSQL only; (7) run migrations deliberately
     (docker compose ... run --rm app python manage.py migrate --noinput);
     (8) run operational_check the same way; (9) configure initial assets
     and policies (bootstrap import + staff management UI); (10) create the
     first administrator (createsuperuser via the app container); (11) start
     the app service; (12) configure Caddy or equivalent from deploy/
     Caddyfile.example; (13) verify HTTPS; (14) /health/live; (15)
     /health/ready; (16) /login/; (17) pilot_readiness_check --strict once
     the pilot database is prepared. Every command must correspond to
     CURRENT repository behavior.
   - Rehearsal: what deploy/rehearse_internal_alpha_deployment.sh does and
     does NOT prove; clearly distinguish CI/config validation, synthetic
     local rehearsal, and an actual deployed service. Do not present the
     rehearsal as deployment.
   - Persistence: exactly where PostgreSQL data lives (named volume
     postgres-data under the Compose project) and an explicit warning that
     docker compose down -v DELETES the database.
   - Backup and restore: minimal operational procedure using the real
     commands (backup_database --apply, off-host copy requirement, restore_
     drill for the isolated drill); link to docs/runbooks/backup-and-restore.
     md; explicit warning that an untested backup is not sufficient.
   - Upgrade: supported manual alpha procedure (obtain reviewed revision/
     image; backup; inspect migration plan; migrate deliberately; restart/
     update app; readiness checks; keep the previous image tag for
     application rollback). Do NOT claim automatic rollback.
   - Shutdown/restart: normal stop/start/restart operations that preserve
     persistent data.
   - Security boundaries: never commit deploy/env.production or secret
     files; PostgreSQL never public; Gunicorn loopback/private behind the
     proxy; production settings require real SECRET_KEY/hosts/CSRF origins/
     pepper; local Django accounts are acceptable for the deliberately
     constrained internal alpha but are not the final institutional identity
     solution; public Internet exposure needs additional authentication/
     rate-limit decisions.
   - Known alpha limitations: only operator-relevant true ones (no
     institutional OIDC; no password reset/email workflow; no notification
     system; no execution enforcement; no automatic SmartScheduling cutover;
     no production monitoring stack; plus any other currently true
     operator-impacting limitation). Do not dump the roadmap.
   - Precise status language: "CI-green, production-shaped internal-alpha
     candidate; real deployment not yet evidenced" (or equivalent). Never
     "production-ready" or "repo-complete".
2. README.md — restructure to: concise project introduction, current status
   (truthful, current), a very short development quickstart (or a pointer to
   INSTALL.md's development section), and links to the canonical docs. Fix
   the three stale claims listed in E (OAP conversion is adopted and
   operational; current locked versions; repository workflow now reflects
   delegated development merge with human-reserved D2/release). Move unique
   content to its canonical home (INSTALL.md or docs/) and list every move
   in the report. The README must no longer duplicate the full API endpoint
   list, full command catalog, or full env-var reference — link instead.
3. docs/deployment.md — keep as the deeper deployment reference/rationale.
   Fix the status line (internal-alpha candidate language). Replace the §3
   development-environment command walkthrough with rationale + a pointer to
   INSTALL.md. Replace other duplicated command sequences with links. Keep:
   service layout, configuration reference, container image facts, health
   endpoints, database lifecycle, backup, reverse proxy/TLS, logging/
   monitoring, scheduled work, release process, rollback, readiness gates,
   remaining gaps. Do not make it a second installation walkthrough.
4. docs/README.md — add INSTALL.md (root) as the canonical installation/
   deployment entry point at the top of the index.
5. docs/runbooks/first-internal-alpha-deployment.md — keep its preconditions
   and checklist role; remove the duplicated command steps that INSTALL.md
   now owns (replace with a pointer to the INSTALL.md procedure); keep it
   short.
6. STATUS.md — label explicitly as a HISTORICAL point-in-time snapshot
   (bootstrap generation 1, 2026-09-13): title/header change + a note that it
   is not a live status file and current state must be read from live Git +
   oap/ records. Do NOT rewrite or "update" the historical body.
7. docs/project-handoff.md — label explicitly as a historical snapshot
   (snapshot date 2026-06-22; conversion note 2026-09-13): header note that
   it is historical and superseded (live state: GitHub main + oap/ orders/
   reports). Do NOT rewrite the body.
8. docs/roadmap.md — minimal truthfulness corrections only: WO 0012 status
   (merged, per its PR table entry); WO 0014 section (adoption MERGED by
   human; Concentrated OAP operational; objectives 015-a through 023-a
   implemented on main — one line plus a pointer to oap/orders/); "Next
   roadmap item" (human-selected) updated to reflect the current human
   selection: this cleanup (024-a, current) and then the first real
   internal-alpha deployment (human-authorized, per INSTALL.md). Do not
   restructure the roadmap.
9. Dockerfile — pin the base image to a digest: replace
   `FROM python:3.13-slim` with `FROM python:3.13-slim@sha256:<digest>`
   (digest re-verified at implementation time via `docker manifest inspect
   python:3.13-slim`; keep the tag as a comment). No other Dockerfile change.
10. compose.production.example.yaml — add an app-service healthcheck only:
    a CMD-SHELL python urllib probe of http://127.0.0.1:8000/health/live
    with an `X-Forwarded-Proto: https` header (REQUIRED: production settings
    set SECURE_SSL_REDIRECT=true and trust X-Forwarded-Proto; the slim image
    has no curl; the rehearsal's synthetic env disables SSL redirect, so the
    header is what makes the same probe correct in both worlds), with
    interval/timeout/retries in the same style as the db healthcheck and a
    short start_period. No other change to this file.
11. .github/workflows/ci.yml — ONLY if the CI review (Scope item 12) finds
    one concrete material gap that protects the installation path (e.g. a
    small assertion that the production compose renders with the new
    app healthcheck). Otherwise byte-identical.
12. CI review — review whether CI adequately protects the installation path,
    distinguishing (a) rendering production Compose config, (b) building the
    production image, (c) bringing up the production-shaped stack (local
    rehearsal). Record the conclusion in the report. Do not make CI slow or
    elaborate; do not turn CI into a deployment simulator.
13. Narrow exception (product truthfulness) — IF and only if a command that
    INSTALL.md must document is actually wrong or fails against live main
    (e.g. a flag or env name does not exist), the SMALLEST change that makes
    the documented path truthful is permitted in src/ (or, for a
    rehearsal-script obstruction, in deploy/rehearse_internal_alpha_
    deployment.sh / deploy examples). Failing->passing evidence is required
    for any such change and it must be flagged prominently in the report.
    Strategy expects none; do not use this as a license for product work.
14. Round bytes — oap/orders/024-a-canonical-install-deployment-docs.md
    (rename from the materialized .FINAL source; bytes preserved), oap/active,
    oap/reports/024-a-canonical-install-deployment-docs.md.

## Non-goals

- No product features, no behavior change, no test additions/modifications.
- No OIDC, email, notifications, calendar redesign, SmartScheduling
  production migration, execution gateway, monitoring stack, secret-manager
  infrastructure, Kubernetes/Swarm/Helm/Terraform/Ansible/Celery/Redis.
- No OAP expansion (no new canary/protocol/transport/role/governance doc);
  no ICA; no milestone claims.
- No real deployment, no real DNS/TLS/certificates, no public exposure.
- No release platform, no image registry, no automated deployment.
- No merge, auto-merge, approval, or settings change.

## Numbered acceptance criteria

1. The report records a verification table: every "current fact" from the
   human task and the E list, verified against live main at base e963881
   (observed, not assumed), with any discrepancy and how the documentation
   reflects it.
2. INSTALL.md exists at the root and covers ALL section groups in Scope item
   1, uses the precise status language, contains no invented requirements,
   and every documented command corresponds to current repository behavior —
   with the report recording, per command, HOW it was verified (executed
   locally in which mode — including the full rehearsal; verified via
   `python manage.py help <cmd>`; or verified via compose config rendering).
3. README.md is trimmed per Scope item 2: introduction + current status +
   very short development quickstart + canonical links; the three stale
   claims corrected; the report lists every piece of unique content moved
   (from -> to) and explicitly names anything intentionally dropped as
   duplicative (with the canonical copy location). No unique information is
   lost.
4. Documentation ownership established per Scope items 3-5: docs/README.md
   indexes INSTALL.md; docs/deployment.md no longer contains a competing
   step-by-step walkthrough (rationale/reference + links); first-internal-
   alpha-deployment.md keeps preconditions/go-no-go with the duplicated
   command sequence replaced by a pointer. The report lists each removed
   duplication (file + section).
5. Stale-status corrections complete per Scope items 6-8: STATUS.md and
   docs/project-handoff.md explicitly labeled historical (bodies preserved
   byte-identical apart from the label change); docs/roadmap.md WO 0012/0014
   and next-item truthful; docs/deployment.md status line fixed.
6. Docker layer: Dockerfile base pinned to a digest (report records the
   digest, its `docker manifest inspect` source, and that it was re-verified
   at implementation time); the image builds from the pinned base (exercised
   by the rehearsal build); the production compose renders with the new app
   healthcheck (docker compose -f compose.production.example.yaml config);
   all other Dockerfile/compose/deploy bytes unchanged (prove by diff).
7. Local evidence at the implementation head: FULL rehearsal
   (deploy/rehearse_internal_alpha_deployment.sh, no flag) completes
   successfully with synthetic values and cleans up (post-run --status shows
   no rehearsal-owned residue; deploy/env.production and deploy/secrets/
   absent afterwards); the fast local evaluation path from INSTALL.md was
   actually exercised (dev compose db+app, migrate, superuser, login URL,
   health endpoints) and torn down afterwards; full pytest green; ruff
   check + ruff format --check; mypy; makemigrations --check --dry-run;
   manage.py check; operational_check; spectacular --validate --fail-on-
   warn; pip-audit. If the narrow exception (Scope 13) was used: failing->
   passing evidence for the specific command.
8. CI at the exact implementation head: quality/test/security/container and
   oap-harness all success.
9. The diff touches only allowed_paths.
10. The PR description contains exactly these items: (a) which documentation
    was authoritative before; (b) what is authoritative after; (c) which
    stale statements were corrected; (d) whether any deployment code/config
    changed and why (Dockerfile pin; compose healthcheck; any CI item; any
    narrow exception); (e) the exact verification performed; (f) the
    remaining blockers before a real internal-alpha deployment.
11. The report's remaining-blockers section is truthful: name what a real
    deployment still needs (human-authorized host, DNS/TLS plan, real secrets
    from the human's secret store, first administrator creation by/with the
    human, backup destination, operator assignment) and does NOT claim any
    deployment was performed.

## Deferred human adjudication

- Decision: NONE
