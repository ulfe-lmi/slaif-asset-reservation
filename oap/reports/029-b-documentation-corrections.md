<!-- OAP-META
{
 "kind": "report",
 "id": "029-b",
 "order_path": "oap/orders/029-b-documentation-corrections.md",
 "order_sha256": "f5bab6eb46db91e702e70b3fb322c52fb5be6a7af0f84207c020d8b0a1dcc7f3",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 57,
 "pr_number": 58,
 "branch": "codex/57-oap-029-a-product-documentation",
 "implementation_head": "daa3a332a125adee5a0191430bea8a1e5bed0ecc",
 "base_sha": "f406c612f52f64a50f0a145b27a7f580838c7287",
 "result": "PARTIAL",
 "observed_implementation_ci": {
  "observed_head": "daa3a332a125adee5a0191430bea8a1e5bed0ecc",
  "runs": [
   {"run_id": 37131953823, "workflow": "ci.yml", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "failure", "container": "success"}, "failure_boundary": "security: uv run pip-audit -> urllib3 2.7.0 (locked) PYSEC-2026-4175/4176/4177, fix 2.8.0; pre-existing dev-only chain; lockfile is a forbidden resource of this order"},
   {"run_id": 37131953794, "workflow": "oap.yml", "event": "pull_request", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 029-b report — Documentation corrections (usability, secret handling, operator navigation)

Order digest: `f5bab6eb46db91e702e70b3fb322c52fb5be6a7af0f84207c020d8b0a1dcc7f3`
(committed `oap/orders/029-b-documentation-corrections.md`, state FINAL,
base `f406c612f52f64a50f0a145b27a7f580838c7287`, issue #57, PR mode AMEND
on the existing PR #58 / branch
`codex/57-oap-029-a-product-documentation`, DHA NONE). Active pointer
`oap/active` = `029-b` + LF (6 bytes `3032 392d 620a`), committed with the
implementation head. Verified at start: remote main at the base SHA; PR #58
open at the 029-a report head
`2b2dc31b638f39b6bbab90f288f775e3fdb37d9b`; the exact 029-b order bytes and
the `029-b` pointer were already present in the working tree
(strategy-owned) and are committed verbatim.

Implementation head SHA: daa3a332a125adee5a0191430bea8a1e5bed0ecc

Report publication commit: SELF

## Identity and result

- Repo/issue/branch/PR: `ulfe-lmi/slaif-asset-reservation` / #57 /
  `codex/57-oap-029-a-product-documentation` / PR #58 (AMEND round b;
  `Closes #57`).
- **Result: PARTIAL.** All ordered documentation corrections are complete
  and verified as ordered; product/runtime/dependency bytes are identical
  to base. The single deviation from a COMPLETE report is the required
  `security` CI check at the exact implementation head, which fails for the
  same pre-existing, unchanged reason as in 029-a (locked dev-only
  `urllib3 2.7.0` vs published advisories, fix 2.8.0), which this order
  forbids fixing and explicitly routes to strategy / a pending human scope
  decision.

## Acceptance evidence

1. **Clone/checkout truth and runnable quickstart/dev docs** — PASSED.
   Every clone command now uses the actual
   `https://github.com/ulfe-lmi/slaif-asset-reservation.git`
   (QUICKSTART, CONTRIBUTING, INSTALL step 1). No `<private-repo-url>` or
   `<reviewed-commit-sha>` literal remains. INSTALL step 1 uses an explicit
   `read -r -p` prompt plus a full-40-character-SHA regex before
   `git checkout` (verified in a disposable context: full SHA accepted,
   12-char prefix rejected with a non-zero exit). The QUICKSTART clone step
   was executed as written (disposable shallow clone of the real URL,
   base `f406c612...` retrieved).
2. **No inline-password CLI alternatives; honest interactive account
   creation; curl health checks; plain prose** — PASSED. Both insecure
   inline-password `createsuperuser` alternatives (QUICKSTART step 5,
   INSTALL step 10; `DJANGO_SUPERUSER_PASSWORD=<...>` /
   `admin@example.org`) are removed. The interactive command is documented
   with the exact source-verified prompts: `Email` (USERNAME_FIELD=email,
   field verbose name `email`, verified against the model in the locked
   venv), then `Password` entered twice. No default username/admin claim
   remains. QUICKSTART adds the curl prerequisite and both health checks
   use `curl -fsS` with the expected HTTP 200. The agent-like
   invent-accounts / fake-seed-data / "correct expected behavior" sentences
   are removed; step 7 simply states that staff create an active policy in
   `/manage/` before booking, and step 4 states the sanitized bootstrap set
   is not a hardware verification.
3. **Project-name collision truth; concise quickstart** — PASSED. The
   "can never touch a normal development stack or any other project" claim
   is gone. QUICKSTART section 2 now requires the project name to be
   unused: check `docker compose -p slaif-eval ps` and
   `docker volume ls | grep slaif-eval` before the first run, and if one
   exists, choose another name consistently without adopting or deleting
   it. The default data-preserving teardown and the explicit
   `down -v` destructive warning are retained. QUICKSTART tightened from
   184 to 159 lines.
4. **INSTALL env/secret handling and quiet validation** — PASSED. Step 2
   now: review/reuse an existing `deploy/env.production` (no overwrite),
   and for a fresh file `umask 077` + `install -m 0600` BEFORE real values
   are written (both semantics verified in disposable directories); keep
   the file 0600, secret dir 0700 retained. Step 5 documents
   `docker compose -f compose.production.example.yaml config --quiet` as
   the safe no-output validation (verified: exit 0, zero output bytes),
   and warns that plain `config` prints the resolved environment
   (verified against a disposable copy with synthetic values: resolved
   `SLAIF_DJANGO_SECRET_KEY` / `DATABASE_URL` values appear in the plain
   output). No real secret was generated in this test. The
   hostname + `127.0.0.1` requirement is preserved verbatim in substance;
   the label is corrected to the approved service hostname for the
   internal pilot (in step 2 and the CSRF-origin bullet). Strategy's
   independent production-shaped smoke at source-identical settings
   (omitted 127 -> 400; 127 + X-Forwarded-Proto: https -> 200; 127 without
   header -> 301) is the evidence for this behavior; no settings changed.
5. **INSTALL structure: pointers, banned boilerplate, navigation, stable
   numbering** — PASSED. Sections 3 and 4 are short pointers to
   QUICKSTART/CONTRIBUTING with headings and section numbers preserved for
   inbound references (`docs/deployment.md` cites "INSTALL.md, sections 3
   and 4"; runbooks cite section 5 and its steps 6-17; `docs/deployment.md`
   cites section 6; the immutable audit references cite section 12 / 9
   limitations — all intact). Both banned boilerplate sentences ("No other
   requirements are invented by this document.", "Every command below
   corresponds to current repository behavior.") are removed. A compact
   linked contents list was added near the top (all 15 anchors verified
   against GitHub's slug algorithm, including the em-dash
   `#4-development-installation-uv--development-path`). Section 5 step
   numbering 1-17 is unchanged.
6. **INSTALL operator sections: uninstall, troubleshooting, rollback** —
   PASSED. New section 14 (Uninstall and data retention): default
   `down` (no `-v`) retains the named volume; the destructive
   `down -v` is plainly warned and limited to the operator-owned project
   after a retention decision; image tags, env/secret files, and proxy
   vhost removal are listed; no scheduler is installed. New section 15
   (Troubleshooting) covers: ports; DB password mismatch including the
   verified fact that changing `POSTGRES_PASSWORD_FILE` does not change an
   existing PostgreSQL volume's password (docker-entrypoint initializes it
   only on an empty volume); DisallowedHost/HTTP-400 unhealthy probe from a
   missing `127.0.0.1`/hostname; readiness 503/migrations; proxy
   `X-Forwarded-Proto` and CSRF origin; missing/ambiguous policy
   fail-closed; and backup-tool location (app image has no pg client
   tools; `db`-container native tools or host-side wrappers). Section 9
   gains practical application rollback commands (retag the recorded
   previous commit-addressable image to `internal-alpha`,
   `compose up -d app`, verify `/health/ready` through the proxy plus
   `operational_check`) with the existing rollback semantics kept: the
   previous image must be compatible with the current DB; an incompatible
   DB requires an approved backup restore, not git-revert/migrate
   guessing. All stop/start/status commands use the production compose
   file consistently.
7. **INSTALL backup/restore truth** — PASSED. The PG-container native
   `pg_dump`/`pg_restore` commands are preserved and correct; protected
   destination permissions added (`install -d -m 0700 /backups`);
   off-host copy remains a requirement; wrapper defaults (dry-run
   `restore_drill` et al.) and the no-client-tools-in-app limitation
   retained. Restore now: app stopped first,
   `pg_restore --clean --if-exists --exit-on-error` (`--exit-on-error`
   verified present in the digest-pinned postgres:17 image's actual help:
   "pg_restore (PostgreSQL) 17.11"), and explicit do-not-restart-after-a
   failed-restore guidance with the partial-restore consequence of
   `--clean --if-exists`. No production restore was executed; only
   isolated checks. Step 16's negative API check is now a clear status-only
   expected-401 (`curl -sS -o /dev/null -w '%{http_code}\n'`, expected
   output 401) without `curl -f`, and no longer claims the discarded body
   was inspected.
8. **README** — PASSED. Documentation table gains a direct
   `ARCHITECTURE.md` (canonical) row and an OpenAPI information pointer
   (`/api/schema/` + `/api/docs/`, `SLAIF_ENABLE_API_DOCS` opt-in,
   disabled by default in production, staff-only there when enabled —
   verified against `config/urls.py` `ApiDocumentationPermission` and
   `settings/production.py`: `API_DOCS_ENABLED` default False,
   `API_DOCS_PUBLIC` hard False, `IsAdminUser` when enabled). "reducible"
   replaced with plain cancellable/releasable. No unrelated reference-product
   assumptions present (SmartScheduling references are this project's own
   deferred legacy migration). First 100 raw lines remain product/start;
   the OAP specialist pointer starts at line 143.
9. **docs index navigation** — PASSED. Start here now includes the
   canonical architecture. Users carries the actual token/auth anchors
   (`api-contract.md#authentication-and-scopes`,
   `security-model.md#5-api-token-design`; both anchors verified).
   Operators link directly to the security model, backup/restore runbook,
   pilot preparation and readiness runbooks, and the migration runbook
   (real private cutover remains separate). `READINESS.md` moved from the
   operator path to a labeled governance baseline. Governance now includes
   AGENTS (root router), PLAN, the compact executor architecture
   projection, and CRITICAL. Current canonical docs unchanged.
10. **CONTRIBUTING** — PASSED. Intro is now for the human developer
    (linked issue + ARCHITECTURE/security-model/TESTING + verified current
    main/open PRs; branch-PR expectation). AGENTS/OAP instructions moved
    to the agent section. A Prerequisites section links TESTING.md for the
    required test tooling (incl. the Playwright Chromium build) instead of
    replicating the operator path. Developer commands are accurate
    (real clone URL; `uv sync --locked --all-groups`; `.env` handling;
    migration; runserver).
11. **oap-workflow issue-lifecycle sentence** — PASSED. The single sentence
    now reads: objective PR uses `Closes #<issue>` only when fully
    satisfied; after the merge, strategy verifies the closure, and a
    satisfied issue that remains open is reconciled with a factual
    merged-PR closeout. No new machinery; the rest of the file is
    byte-identical (diff shows only that sentence).

## Verification and negative paths

- Link/anchor validation over the six changed documents (relative links
  and actual heading anchors; anchors computed with GitHub's documented
  slug algorithm and cross-checked against GitHub's own markdown renderer
  for the em-dash edge case): 101 relative links, 0 dangling; 3 external
  links unchanged (README badges).
- Inbound numbered references: INSTALL sections 3/4/5/6/12 and section-5
  steps 1-17 stable; `docs/runbooks/first-internal-alpha-deployment.md`
  ("INSTALL.md, section 5", "steps 11-16") and `docs/deployment.md`
  ("sections 3 and 4", "section 6", rehearsal pointer) intact.
- First-100-README ledger sweep: no OAP/work-order/objective/conversion/
  handoff terms in raw lines 1-100; OAP pointer from line 143.
- `git diff --check`: clean.
- Protected byte identity vs base `f406c612...`: src/, tests/, deploy/,
  .github/, data/, compose.yaml, compose.production.example.yaml,
  Dockerfile, pyproject.toml, uv.lock, .env.example all unchanged; the
  only docs/ changes are the two allowed files (docs/README.md,
  docs/oap-workflow.md — the latter only the lifecycle sentence). The 029-a
  order and report bytes are unchanged (0-line diff vs the 029-a report
  head). Working-tree changes are exactly the allowed paths.
- Amended commands verified in disposable context: real shallow clone as
  written; `read` prompt + full-SHA regex (accept/reject cases);
  `config --quiet` (0 output bytes, exit 0) and plain `config` secret
  printing (synthetic values only, disposable /tmp copy, removed);
  `umask 077`/`install -m 0600`/`install -d -m 0700` mode results (600/600/
  700); `pg_restore` flags against the actual pinned PG 17.11 help;
  rollback retag with an owned synthetic tag (removed afterwards).
- 029-a real-PG17 quickstart/rehearsal evidence (acceptance 3/4 of that
  report) is reused for unchanged behavior (dev compose path, rehearsal
  script semantics, ALLOWED_HOSTS/healthcheck probe); no unchanged
  expensive suite was rerun for prose.
- Local fast checks at the implementation working tree: `uv run ruff
  check .` PASSED; `uv run ruff format --check .` PASSED (185 files);
  `uv run --env-file .env python manage.py check` PASSED (0 issues);
  `uv run --env-file .env python manage.py makemigrations --check
  --dry-run` PASSED (no changes); `git diff --check` PASSED.
- Full local pytest suite: NOT RUN in this round per the order (unchanged
  prose); the CI `test` job at the exact head is the authoritative
  evidence. Prior local full-suite state (610 passed / 1 pre-existing
  environment-sensitive failure, clean-env oap harness 154/154) is
  historical context, not a sum and not a claim for this head.
- No failed check is labeled passed; no future push or check success is
  claimed.

## CI observed before authoring

At implementation head `daa3a332a125adee5a0191430bea8a1e5bed0ecc`
(all runs completed before authoring; job conclusions from the structured
CI data):

- Run 37131953823 (workflow `ci.yml`, event pull_request, head daa3a332):
  quality success, test success (full suite incl. browser at this head),
  container success, **security failure** — failed in `uv run pip-audit`
  (job failed in 15s): urllib3 2.7.0 (locked, dev-only chain via
  requests/pip-audit/pytest-playwright) with PYSEC-2026-4177,
  PYSEC-2026-4176, PYSEC-2026-4175, fix 2.8.0 — the same pre-existing
  boundary as 029-a; this order forbids the lockfile change and routes
  the disposition to a separate pending human scope decision.
- Run 37131953794 (workflow `oap.yml`, event pull_request, head daa3a332):
  oap-harness success.

Report-head CI: NOT YET OBSERVED AT AUTHORING (the report-only commit's
checks are reported by strategy; none are claimed here).

## Superseded 029-a interpretation

029-a stated the urllib3 advisories were "published after the last green
base CI 35664329877 (2026-09-21)". This round supersedes that
interpretation: upstream publication (2026-09-15) predates that green CI.
What was actually observed in both rounds is the current `pip-audit`
failure versus the historical green CI, without establishing why the
historical data differed. No security waiver is claimed; the boundary is
unchanged and remains strategy/human-owned. The immutable 029-a report
itself was not edited.

## Security, data, dependencies and local tools

No secrets, tokens, peppers, private exports, or personal data in this
report, the PR, or any changed file. All disposable resources were owned
and cleaned up (two /tmp scratch trees removed, one owned synthetic docker
tag removed, /tmp JSON artifacts); the real repository was cloned
read-only in /tmp and removed. No production/lab/Neumann/SmartScheduling/
DNS/TLS/public-exposure boundary crossed. No new dependencies; no tools
installed beyond the locked environment. No real secret generated in any
test (synthetic values only, outside the repository).

## DHA outcome and unresolved gates

- Decision: NONE (as declared in the order). No CRITICAL entry appended,
  no gate cleared, no adjudication performed.
- Unresolved gate for strategy: the pre-existing `pip-audit`/`security`
  CI failure (locked urllib3 2.7.0, dev-only chain, 3 advisories, fix
  2.8.0). Resolution requires a dependency/lockfile decision under a
  separate order / human scope disposition; this round neither fixed nor
  waived it.

## Limitations

- Strongest unresolved limitation: the `security` CI job cannot pass at
  this head without a forbidden lockfile change, so the PR cannot be
  strategy-accepted under an all-green-CI policy until that boundary is
  handled separately.
- All ordered documentation corrections are complete and verified against
  source and disposable-context execution evidence; no runtime behavior
  changed in any byte.
- No merge, release, or self-certification is claimed or implied.
