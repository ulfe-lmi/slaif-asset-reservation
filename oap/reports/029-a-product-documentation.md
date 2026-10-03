<!-- OAP-META
{
 "kind": "report",
 "id": "029-a",
 "order_path": "oap/orders/029-a-product-documentation.md",
 "order_sha256": "a8027aeb6e2ea4b974abefae7b8e2459448de9d0d3497fa3c92aea64115f5d24",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 57,
 "pr_number": 58,
 "branch": "codex/57-oap-029-a-product-documentation",
 "implementation_head": "b2998a9bae1424f411c1cbfc6c4cc4f59a642e28",
 "base_sha": "f406c612f52f64a50f0a145b27a7f580838c7287",
 "result": "PARTIAL",
 "observed_implementation_ci": {
  "observed_head": "b2998a9bae1424f411c1cbfc6c4cc4f59a642e28",
  "runs": [
   {"run_id": 37130103563, "workflow": "ci.yml", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "failure", "container": "success"}, "failure_boundary": "security: uv run pip-audit -> urllib3 2.7.0 (locked) PYSEC-2026-4175/4176/4177, fix 2.8.0; advisories published after last green base CI 35664329877 (2026-09-21); pre-existing, lockfile is a forbidden resource of this order"},
   {"run_id": 37130103499, "workflow": "oap.yml", "event": "pull_request", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 029-a report — Product-first documentation and repository hygiene

Order digest: `a8027aeb6e2ea4b974abefae7b8e2459448de9d0d3497fa3c92aea64115f5d24`
(committed `oap/orders/029-a-product-documentation.md`, the FINAL
strategy-published order; state FINAL, base
`f406c612f52f64a50f0a145b27a7f580838c7287`, issue #57, PR mode
CREATE_OR_RESUME, DHA NONE). Active pointer `oap/active` = `029-a` + LF
(6 bytes `3032 392d 610a`; sha256
`97158dabcf18e04c95b33ed10dcbadfa0b8ae68ac8854fdeeb5c101fa8a3d1db`).
Verified at start: remote and local main both at the base SHA; no open PR
and no prior branch for this objective before this round.

Implementation head SHA: b2998a9bae1424f411c1cbfc6c4cc4f59a642e28

Report publication commit: SELF

## Identity and result

- Repo/issue/branch/PR: `ulfe-lmi/slaif-asset-reservation` / #57 /
  `codex/57-oap-029-a-product-documentation` / PR #58 (`Closes #57`).
- **Result: PARTIAL.** All documentation work of the order is complete,
  executed and verified as ordered; product bytes are identical to base.
  The single deviation from a COMPLETE report is one required CI check at
  the exact implementation head: the `security` job fails in `uv run
  pip-audit` for a **pre-existing** reason (newly published advisories for
  the locked `urllib3 2.7.0`), which this order forbids fixing (lockfile is
  a forbidden resource) and explicitly routes to strategy.

## Acceptance evidence

1. **Five entry docs meet scope** — PASSED. `README.md` rewritten as a
   product landing page (purpose/value, Get started to QUICKSTART/INSTALL,
   mermaid how-it-works, human/agent/staff capabilities, supported runtime
   with verified locked versions Django 5.2.17 / DRF 3.17.2 / Python 3.13 /
   PostgreSQL 17, documentation table, concise limitations, developers,
   Apache-2.0 license, optional CI/Python/license badges, OAP only as a
   bottom specialist pointer). `QUICKSTART.md` new (dedicated
   `-p slaif-eval` project, detached start, deliberate migrations, optional
   import dry-run/apply, interactive createsuperuser, login + both health
   endpoints, policy fail-closed explanation, data-preserving teardown with
   a visible `down -v` warning, collision guidance that never stops foreign
   services). `INSTALL.md` operator guide (section numbering and section-5
   step semantics preserved for inbound runbook references; added the
   verified `SLAIF_ALLOWED_HOSTS` implication and the unauthenticated
   `/api/v1/me/` failure check at step 16; section 6 documents the opt-in
   `deployment-rehearsal.yml`; section 12 lists 9 operator-relevant
   limitations incl. the shared privileged PG role). `docs/README.md`
   task-oriented (Start here; Users/API clients; Operators; Developers;
   Governance/history last; canonical architecture = root ARCHITECTURE.md;
   API contract described as implemented). `CONTRIBUTING.md` concise actual
   developer path; stale pre-adoption claims removed.
2. **First-glance/ledger regression** — PASSED. Raw README lines 1–100 are
   entirely product (OAP pointer begins line 141 of 146). Searches for WO
   ranges, objective ranges, old SHAs, audit counts, PR chronology, and
   conversion/handoff prose across README/QUICKSTART/INSTALL found only:
   the product feature "audit/auditable/audit trail" (justified product
   terminology, not OAP audit narrative) and the bottom-of-README history
   pointer to `docs/work-orders/` + `docs/project-handoff.md` (justified:
   the order requires the OAP/history specialist pointer near the bottom).
   No other exceptions.
3. **QUICKSTART executed on owned disposable resources** — PASSED with
   disclosed adaptations. Disposable clone at base `f406c612...` in
   `/tmp/slaif-029-eval-1791037065`; real PostgreSQL 17 (digest-pinned
   image from `compose.yaml`) and real HTTP. Exact sequence: `docker
   compose -p slaif-eval-029a -f compose-eval-ports.yaml up -d` (build);
   `ps` (db healthy, app running); `exec app python manage.py migrate
   --noinput` (all migrations OK incl. btree_gist + exclusion constraint);
   `import_bootstrap_assets` dry-run then `--apply` (`mode=dry-run`
   planned=47 created=47 excluded=1 conflicted=0, then same on apply);
   `createsuperuser --noinput --email ...` via `DJANGO_SUPERUSER_PASSWORD`
   (documented non-interactive equivalent — disclosed test adaptation for
   the interactive command); administrator login over real HTTP with CSRF
   (GET /login/ 200, POST 302 -> /, dashboard 200); `/health/live` 200 and
   `/health/ready` 200; reserve page for a reservable exclusive asset with
   zero policies renders "WARNING: No unambiguous active reservation policy
   applies to this asset." (fail-closed confirmed); `stop`/`start` and
   `down`/`up -d` preserve the 47 imported assets; `down -v` (own project
   only) deletes the volume and the fresh database returns `/health/ready`
   503 until migrations run (destructive semantics confirmed). Disclosed
   adaptations: (a) this host has a foreign service on 127.0.0.1:5432 which
   was never touched; the run used an uncommitted test-only variant file in
   the disposable checkout whose only diff vs checked-in `compose.yaml` is
   two host-port lines (5432->54329, 8000->8010); checked-in compose bytes
   unaltered; (b) the admin password was generated, held in a mode-0600
   file inside the disposable checkout, and never printed.
4. **INSTALL cross-check + production-shaped rehearsal** — PASSED. Every
   INSTALL command cross-checked against source/help: management-command
   syntax (`migrate --noinput`, `import_bootstrap_assets --input ...
   [--apply]`, `createsuperuser [--noinput --email ...]`,
   `operational_check`, `pilot_readiness_check --strict`,
   `backup_database/restore_database --apply`, `restore_drill`,
   `purge_expired_idempotency_records`), URLs, compose service/env names,
   and `deploy/env.production.example`/`deploy/Caddyfile.example` contents.
   ALLOWED_HOSTS implication verified against `settings/production.py` +
   the compose healthcheck (probe = in-container
   `http://127.0.0.1:8000/health/live` with `X-Forwarded-Proto: https`;
   `127.0.0.1` must be in `SLAIF_ALLOWED_HOSTS`; no settings weakened).
   Full rehearsal executed in a second disposable clean clone at base:
   `deploy/rehearse_internal_alpha_deployment.sh` (default port 18080,
   PID-unique project) ended `rehearsal=ok` with every stage logged
   (config render, build, `runtime_user=10001:10001`, `image_assets=ok`,
   migrations, bootstrap import validation, `operational_check`, OpenAPI
   validation, `health_and_login=ok`, `anonymous_manage_redirect=ok`,
   `api_auth_failure=ok`); `--status` reported no rehearsal-owned residue;
   `deploy/` left clean; script safety inspected before execution (refuses
   real env/secret overwrite, scoped project labels, port precheck that
   never kills foreign occupants). Real TLS/DNS exposure, a real
   deployment, and backup execution against live data: NOT RUN by design.
   Changed normative deployment instruction for strategy's post-merge
   freshness assessment: INSTALL step 2 (ALLOWED_HOSTS must include
   `127.0.0.1`) and step 16 (added unauthenticated API probe); both are
   documentation of existing behavior, no config change.
5. **Link validation and inbound references** — PASSED. All relative links
   and anchors in the six changed Markdown files verified programmatically
   (67 file links, 0 dangling; external branding logo
   https://www.slaif.si/assets/slaif-logo.svg returns 200 image/svg+xml).
   Inbound references preserved: INSTALL sections 3/4/5/6/12 and
   section-5 steps 6–17 keep their meaning for
   `docs/runbooks/first-internal-alpha-deployment.md` and
   `docs/deployment.md`; immutable audit references to "INSTALL.md section
   12 / 9 known alpha limitations" now match (section 12 lists 9 items).
6. **Product byte identity + standard checks + required CI** — PARTIAL.
   `git diff` vs base is exactly the eight allowed paths; no
   product/runtime/dependency/workflow/test/inventory byte changed. Local
   standard checks at the working tree (own disposable PG17 on a free
   loopback port; temp env file kept in /tmp, never committed): see
   "Commands and results". Required CI at exact implementation head: 4 of 5
   success; `security` FAILED at its first step (pre-existing urllib3
   boundary, see below). Per the order: boundary located, no forbidden file
   touched, no waiver, reported here to strategy.
7. **One issue / one PR / report content** — PASSED. Issue #57, single PR
   #58 with `Closes #57` and actual scope/evidence/limitations; this report
   identifies changed paths, all verification results incl. failures and
   adaptations, the strongest unresolved limitation, and explicit zero
   runtime-source changes. Implementation CI is reported separately from
   report-head CI (not yet observed at authoring).

## Changed files and scope

Implementation commit `b2998a9bae1424f411c1cbfc6c4cc4f59a642e28` (single
non-report commit, first and only implementation commit of the round):

- `README.md` (modified), `QUICKSTART.md` (new), `INSTALL.md` (modified),
  `CONTRIBUTING.md` (modified), `docs/README.md` (modified),
  `docs/oap-workflow.md` (modified — status paragraph + one closing-keyword/
  post-merge issue-lifecycle sentence only), `oap/orders/029-a-product-documentation.md`
  (committed exact order bytes), `oap/active` (committed pointer bytes).

No other file changed. Zero application, source, migration, test,
dependency, lockfile, workflow, config, or inventory changes.

## Commands and results

Environment: this development host (Linux x86_64, Docker 29.1.3, Compose
2.40.3, uv 0.12.5); owned disposable PostgreSQL 17 container on
127.0.0.1:54331 for the product suite; foreign 127.0.0.1:5432 service
present and never touched.

- `uv sync --locked --all-groups` — PASSED (68 packages checked).
- `uv run ruff check .` — PASSED (all checks passed).
- `uv run ruff format --check .` — PASSED (185 files already formatted).
- `uv run mypy src` — PASSED (no issues in 119 source files).
- `uv run python manage.py check` — PASSED (0 issues, 0 silenced).
- `uv run python manage.py makemigrations --check --dry-run` — PASSED (no
  changes detected).
- `uv run pytest --ds=slaif_reservation.config.settings.test` (full suite
  incl. 8 browser tests on owned disposable PG17) — 610 passed, 1 failed in
  196.97s. The single failure
  (`tests/oap/test_ba38_39_tmux_config.py::Ba39OperationPrereqs::test_ba39_strategic_same_prerequisites`)
  reproduces identically on a clean base checkout: the test inherits the
  coding session's `OAP_ROLE=CODING` into a subprocess it does not scrub
  (launcher then correctly refuses "conflicting OAP_ROLE=CODING"). With
  `OAP_ROLE` unset: `python3 -m unittest discover -s tests/oap -p
  'test_*.py'` — PASSED 154/154. Pre-existing test-environment issue,
  outside allowed paths; CI `oap-harness` job (clean environment) PASSED.
- `uv run python manage.py spectacular --file <tmp> --validate
  --fail-on-warn` — PASSED.
- `git diff --check` — PASSED (clean).
- `uv run pip-audit` — FAILED (pre-existing): `urllib3 2.7.0
  PYSEC-2026-4175/4176/4177, fix 2.8.0`. First failing boundary is the
  locked dependency set; the base CI run 35664329877 (head f406c61,
  2026-09-21) was 4/4 success, so the advisories were published after the
  last green base CI. Lockfile changes are a forbidden resource of this
  order; reported to strategy, not waived.
- QUICKSTART execution and rehearsal: see acceptance evidence 3 and 4
  (both PASSED; exact stage outputs recorded there).
- Link/anchor validation script over the six changed Markdown files —
  PASSED (67 links, 0 dangling).
- Real TLS/DNS exposure, real deployment, restore on live data — NOT RUN.
- No browser/UI capture artifacts containing secrets; evaluation
  administrator credentials never printed or committed.

## CI observed before authoring

At implementation head `b2998a9bae1424f411c1cbfc6c4cc4f59a642e28`:

- Run 37130103563 (workflow `ci.yml`, event pull_request): quality
  success, test success, container success, **security failure** — failed
  at `uv run pip-audit` (13s): urllib3 2.7.0, PYSEC-2026-4175/4176/4177,
  fix 2.8.0 (pre-existing locked-dependency boundary).
- Run 37130103499 (workflow `oap.yml`, event pull_request): oap-harness
  success.

Report-head CI: NOT YET OBSERVED AT AUTHORING.

## Security, data, dependencies and local tools

No secrets, tokens, peppers, private exports, or personal data in this
report, the PR, or any changed file. All disposable resources were owned
and cleaned up after use (container `slaif-029-testdb`, evaluation project
`slaif-eval-029a` incl. its volume, both built images, both disposable
checkouts, /tmp artifacts); the foreign 127.0.0.1:5432 service was never
stopped, modified, or even probed beyond a TCP connectability check. No
production/lab/Neumann/SmartScheduling/DNS/TLS/public-exposure boundary
crossed. No new dependencies; no tools installed beyond what the locked
environment already provided.

## DHA outcome and unresolved gates

- Decision: NONE (as declared in the order). No CRITICAL entry appended,
  no gate cleared, no adjudication performed.
- Unresolved gate for strategy: the pre-existing `pip-audit`/`security`
  failure (locked urllib3 2.7.0 vs newly published advisories, fix 2.8.0).
  Resolution requires a dependency/lockfile decision and its own order;
  this round neither fixed nor waived it.
- Second observation for strategy (no action within this order's scope):
  `tests/oap/test_ba38_39_tmux_config.py::test_ba39_strategic_same_prerequisites`
  is environment-sensitive to an inherited `OAP_ROLE` (passes in CI).

## Limitations and recommendation

- Strongest unresolved limitation: the `security` CI job cannot pass at
  this head without a forbidden lockfile change; the PR therefore cannot
  be strategy-accepted under an all-green-CI policy until that boundary is
  handled by a separate strategic decision/order.
- All documentation deliverables are complete and verified; the
  documentation truth (including the ALLOWED_HOSTS healthcheck
  implication) is asserted against source and execution evidence, not
  assumption.
- Recommendation (evidence-backed, not a next order): strategy decides the
  urllib3 advisory disposition (locked upgrade vs recorded risk) and then
  re-verifies this PR's head or requests a suffix round if any doc
  correction is desired. No merge, release, or self-certification is
  claimed or implied.
