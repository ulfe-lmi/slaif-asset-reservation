<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "057-a",
  "order_path": "oap/orders/057-a-external-smtp-config.md",
  "order_sha256": "e580b0835d2fd8f9eca0101b2b6ca00f3b4f44c7d9d4a33c010c3ad717ca9520",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 118,
  "pr_number": 119,
  "branch": "codex/118-oap-057-a-external-smtp-config",
  "implementation_head": "cdb3f68978d7650ee34960808c0ff8bfedc74883",
  "base_sha": "2df6341d4d89dd45c835e3ac1af67ce076e54346",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "cdb3f68978d7650ee34960808c0ff8bfedc74883",
    "runs": [
      {
        "run_id": 42926939885,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "test": "success",
          "security": "success",
          "container": "success"
        }
      },
      {
        "run_id": 42926940132,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1391 passed, 1 warning in 616.30s (0:10:16)",
    "warning": "tests/test_product_entry.py:568 UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unrelated)",
    "oap_harness_summary": "Ran 160 tests in 29.877s - OK"
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 057-a — execution report: validated external SMTP transport for onboarding

Implementation head SHA: cdb3f68978d7650ee34960808c0ff8bfedc74883
Report publication commit: SELF

## Identity and result

COMPLETE for order 057-a (D0, `Decision: NONE`), a fresh round: issue #118,
PR #119 (CREATE_OR_RESUME, no prior PR/branch on the remote), branch
`codex/118-oap-057-a-external-smtp-config`. Before the first write, all twelve
order `source_hashes` (ARCHITECTURE.md, PLAN.md,
ARCHITECTURE-for-agents.md, the four settings files, config/env.py,
deploy/env.production.example, INSTALL.md, docs/deployment.md) were verified
SHA-256-byte-identical against the order base
`2df6341d4d89dd45c835e3ac1af67ce076e54346`, which equals `origin/main` at
start (fetched). `oap/active` was exactly `057-a\n`; the order file bytes are
the strategy-published FINAL bytes (SHA-256
`e580b0835d2fd8f9eca0101b2b6ca00f3b4f44c7d9d4a33c010c3ad717ca9520`).
Governance revision `14fc20b1ff52788974fd3f282322afc9d71362f9` is in main's
history. The wrapper had already consumed the control OK; it was not consumed
again.

The single implementation commit `cdb3f68978d7650ee34960808c0ff8bfedc74883`
(first parent exactly base `2df6341d4d89dd45c835e3ac1af67ce076e54346`)
changes exactly the eleven ordered non-report paths:
`src/slaif_reservation/config/email.py` (new),
`src/slaif_reservation/config/env.py`,
`src/slaif_reservation/config/settings/base.py`,
`src/slaif_reservation/config/settings/local.py`,
`src/slaif_reservation/config/settings/production.py`,
`deploy/env.production.example`, `INSTALL.md`, `docs/deployment.md`,
`tests/test_account_email_settings.py` (new), `oap/active`
(`056-b` → `057-a`), `oap/orders/057-a-external-smtp-config.md`. No
accounts/web/api/management/admin/model/migration change, no dependency,
lock, Compose, proxy, CI, ARCHITECTURE/PLAN/projection, CRITICAL or OAP
helper change; the foreign PR113 was not touched.

## Numbered acceptance evidence

1. **Disabled-by-default capability and canonical URL settings.**
   `base.py` declares `ACCOUNT_EMAIL_ENABLED = False`,
   `PUBLIC_BASE_URL = None` and the dummy `EMAIL_BACKEND`; `env.py` gains
   `validate_canonical_service_url` (bare https origin only: no userinfo,
   path, query, fragment or whitespace; explicit valid host; canonical
   normalization; category-only messages); new `config/email.py` resolves the
   operator keys `SLAIF_ACCOUNT_EMAIL_ENABLED`, `SLAIF_PUBLIC_BASE_URL`,
   `SLAIF_SMTP_HOST/PORT/USERNAME/PASSWORD/FROM/USE_SSL/STARTTLS/TIMEOUT_SECONDS`
   into Django's built-in SMTP backend settings with no new package or
   Gateway dependency. `local.py` and `production.py` call the resolver after
   their host/origin lists are validated. `test_production_settings_disabled_email_preserves_startup_and_dummy_backend`
   and `test_production_settings_disabled_ignores_configured_smtp_junk`
   (subprocess settings load) prove a production install without SMTP config
   starts and reports the dummy backend even with junk transport values
   present; admin creation behavior is untouched (no accounts files changed).
   PASSED.
2. **Production-enabled fail-closed validation.** When enabled in
   production the resolver requires an explicit host, sender and port
   1-65535, username/password set together, exactly one of `SLAIF_SMTP_USE_SSL`
   / `SLAIF_SMTP_STARTTLS` (plaintext never permitted), a bounded 1-60 s
   timeout (default 30) and a canonical https base URL whose host is listed
   in `SLAIF_ALLOWED_HOSTS` and whose origin in `SLAIF_CSRF_TRUSTED_ORIGINS`;
   links may only later derive from that configured origin, never request
   Host. `test_production_settings_enabled_valid_maps_smtp_backend` proves
   the exact mapped values (EMAIL_HOST/PORT/HOST_USER/HOST_PASSWORD set/
   DEFAULT_FROM_EMAIL/USE_SSL/USE_TLS/TIMEOUT, canonical PUBLIC_BASE_URL);
   21 negative cases — missing host/from/port/base URL, non-https, path,
   userinfo, host-not-allowed, origin-not-trusted, port 0/65536/non-int,
   timeout 0/61/non-int, username-only, password-only, both TLS modes,
   neither TLS mode, host-with-port, ambiguous enabled flag — are asserted
   both in-process (`test_resolver_production_matrix_fails_closed`) and at
   the real settings-load boundary in a subprocess
   (`test_production_settings_enabled_matrix_fails_closed`), each with the
   category-only needle and explicit assertions that the synthetic
   credential/username/sender values appear in neither stderr nor stdout.
   Importing settings never attempts an SMTP connection (the subprocess
   loads succeed with the sink never involved). `DEBUG=False`, proxy,
   cookie, DB and secret behavior unchanged (all pre-existing
   `tests/test_settings.py` re-passed). PASSED.
3. **Synthetic local transport; no real relay, no account email.**
   `tests/test_account_email_settings.py` runs a stdlib-socket, loopback-only
   `_FakeSmtpSink`: under test overrides only, Django's SMTP backend delivered
   one simple message (`mail from` / `rcpt to` / `data` transcript, subject
   and body captured, exactly the single synthetic
   `onboarding-test@example.invalid` recipient seen), and a disabled
   (dummy) configuration opened zero connections. Test settings retain the
   locmem backend (unchanged `test.py`); local settings may use a
   plaintext loopback sink (`test_resolver_local_permits_plaintext_synthetic_sink`)
   while production never can (`neither-tls-mode` and `both-tls-modes`
   negatives). No queue, Celery, scheduler or notification system added; no
   account-creation email exists or was sent; `uv run python manage.py
   makemigrations --check --dry-run` → "No changes detected". No credential
   or body value is logged/echoed anywhere (asserted). PASSED.
4. **Truthful protected example and docs.** `deploy/env.production.example`
   carries a commented opt-in block (safe placeholders, no real secret) with
   the fail-closed contract summarized; the file keeps mode-relevant content
   only and is never loaded by Django. `INSTALL.md` adds one concise optional
   pre-user-creation step plus a configuration-details bullet, both pointing
   to the `docs/deployment.md` section-4 transport/security reference and
   both stating that account delivery itself arrives in the next
   implementation objective (no claim that current admin creation emails).
   `docs/deployment.md` lists all ten new variables under Implemented, adds
   the "Account email transport (SAR-055)" reference, and removes the now
   implemented "canonical external URL, email relay" from Deferred. `docker
   compose -f compose.production.example.yaml config --quiet` PASSED locally
   (topology unchanged; the CI container job re-renders at head). PASSED.
5. **Focused suites, five CI jobs, truthful immutable report.** Focused
   `tests/test_account_email_settings.py`: 71 tests PASSED (15.93s). Existing
   settings/project/HTTPS-boundary suites re-passed: 110 passed, 9 skipped
   (pre-existing HTTPS-boundary rehearsal prerequisite skips). Full local
   product suite at the implementation head: 1381 passed, 9 skipped, 1
   failed — the single failure is the pre-existing local-environment oap
   harness test
   `tests/oap/test_ba38_39_tmux_config.py::Ba39OperationPrereqs::test_ba39_strategic_same_prerequisites`,
   verified failing identically on a clean worktree of the unmodified base
   (2df6341), exactly as documented in the 056-b report. All five normal CI
   jobs at the exact implementation head `cdb3f68978d7650ee34960808c0ff8bfedc74883`
   were observed terminal and green before this report: CI run
   42926939885 (quality, test, security, container success; test job
   "1391 passed, 1 warning in 616.30s", the warning being the pre-existing
   intentional DB-unavailable negative test in
   `tests/test_product_entry.py:568`) and oap run 42926940132
   (oap-harness success, "Ran 160 tests in 29.877s - OK"). PR #119 carries
   `Closes #118`. CODING did not merge, self-approve or enable auto-merge;
   strategy reviews the frozen head and only then conditionally merges.
   PASSED.

## Local exact-head runs (evidence index, not CI)

At implementation head `cdb3f68978d7650ee34960808c0ff8bfedc74883` (local,
real PostgreSQL17 via the owned development `.env`; no real SMTP
relay/recipient/credential anywhere — synthetic canaries only):

- `uv sync --locked --all-groups` → clean (68 packages).
- `uv run ruff check .` → "All checks passed!"; `uv run ruff format --check .`
  → "246 files already formatted".
- `uv run mypy src` → "Success: no issues found in 142 source files".
- `uv run --env-file .env python manage.py check` → "System check identified
  no issues (0 silenced)"; `... makemigrations --check --dry-run` → "No
  changes detected".
- `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test
  tests/test_account_email_settings.py -q` → 71 passed in 15.93s.
- Focused regression: `tests/test_settings.py tests/test_django_project.py
  tests/test_https_boundary.py` → 110 passed, 9 skipped.
- Full local suite (same command over all tests) → 1381 passed, 9 skipped,
  1 failed in 777.82s (pre-existing local-environment oap harness failure,
  baseline-verified above).
- `uv run pip-audit` → "No known vulnerabilities found".
- `git diff --check` → clean.
- `docker compose -f compose.production.example.yaml config --quiet` → exit 0.

## Uncertainty, limits and notes

- Report-head CI is separate from and unobserved at authoring; this report
  claims no report-head check results. The implementation CI above was
  observed at exactly the implementation head before writing this report.
- The nine local skips are the pre-existing HTTPS-boundary rehearsal
  prerequisite skips (prerequisites absent on this host; none faked) and the
  single local failure is the pre-existing, baseline-verified oap harness
  environment failure; neither is related to this change. Both run green in
  CI (test job 1391 passed / oap-harness 160 OK).
- No real SMTP relay, recipient, credential, DNS, TLS termination, firewall,
  identity or deployment action was performed; the sink is a local
  stdlib-socket fixture and all canary values are synthetic sentinels kept
  out of diagnostics beyond the asserted-absence checks.
- Account delivery itself (commit-inactive, one login-details email,
  activation after SMTP accept, reissue rotation — SAR-055/056 behavior)
  arrives in the next implementation objective (058); nothing in this round
  sends an account email, creates an active short-password account, or adds a
  user model/migration, six-character credential, password-change route,
  public reset/self-registration, or general notifications.
- The order's `source_hashes`, `base_sha`, governance revision and FINAL
  state were all verified; no DHA entry was declared or appended
  (`Decision: NONE`). Prior 056-a/056-b orders and reports remain immutable
  and untouched.
