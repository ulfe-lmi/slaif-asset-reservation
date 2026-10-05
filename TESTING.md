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
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test tests/test_default_policy.py -v
uv run pip-audit
git diff --check
uv run --env-file .env python manage.py spectacular --file build/openapi/schema.yaml --validate --fail-on-warn
uv run --env-file .env python manage.py operational_check
```

Install Playwright browser/system dependencies inside the approved disposable environment when
needed, record tools installed, and do not ask the human for routine setup. No real service calls.

Gunicorn responsiveness regression (part of the standard `pytest` run):

```bash
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test \
  tests/test_gunicorn_responsiveness.py -v
```

`tests/test_gunicorn_responsiveness.py` launches the real installed Gunicorn with the real
Django routes on unique loopback ports; the anonymous `/health/live` and `/login/` GETs it
exercises need no database. Required evidence: the three supported commands pinned to the
gthread baseline (3 workers, 8 threads, 5 s keep-alive, 30 s timeout); prompt 200s while 6
held idle and while 6 partial-header clients are held; a real old-`sync` negative control in
which held idle clients make bounded probe attempts time out (regression sensitivity); and
child cleanup even after failures.

HTTPS/proxy trust-boundary qualification (part of the standard `pytest` run):

```bash
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test \
  tests/test_https_boundary.py -v
```

`tests/test_https_boundary.py` drives `deploy/rehearse_https_boundary.sh` as
a bounded subprocess (one module-scoped run per suite, 1800 s timeout). The
script qualifies the ACTUAL supported operator path, owned and disposable:
pinned Caddy v2.11.6 on the host (loopback bind, admin off, auto_https off,
1-day synthetic certificate trusted only by the rehearsal clients) in front
of the production image **built from a tracked-file snapshot** of this
repository (never a wholesale copy of the checkout; ignored sentinels are
proved absent from the snapshot), running in an **owned copy** of
`compose.production.example.yaml` under a uniquely named project with
kernel-assigned loopback ports and a private PostgreSQL 17. The bridge
gateway is explicitly discovered (`docker network inspect <project>_default`)
and configured as the `/32` trusted proxy peer — the peer the app actually
sees behind the published port. Every migration/seed/check one-shot runs
via `docker run --env-file` with an explicit minimal synthetic environment;
nothing is inherited (no `DATABASE_URL`, `TEST_DATABASE_URL`, or repository
`.env`); name collisions are refusals, not adoptions, and ownership of what
the run creates is re-verified from compose labels after creation. The
Caddy configuration is derived from the shipped `deploy/Caddyfile.example`
by explicit narrow substitutions (certificate, site address, loopback
listen, short read_header/idle windows, proxy target), and every shipped or
substituted value is asserted against the actual adapted JSON. Exit codes:
0 all checks passed (`https-boundary=ok`), 1 a check failed or cleanup was
incomplete, 42 prerequisites missing (pinned Caddy v2.11.6 / openssl / curl
/ docker) — the wrapper converts 42 into an honest skip, never a fake pass.
The rehearsal proves, end to end: real TLS login with Secure cookies and
CSRF using the legitimate origin **including the fixture Caddy port**;
the one-time-token response arriving through Caddy with the STRICTER
per-view headers intact (`no-referrer` / `no-store, private` — the edge
default is deferred, not replacing) with the issued secret extracted in
memory only and asserted absent from every captured log; overwrite-not-append
forwarding from the trusted edge (spoofed `X-Forwarded-Proto`, ambiguous
`X-Forwarded-For` chains, `Forwarded` + `X-Real-IP` + `X-Forwarded-Port`
multi-variant, underscore variants dropped at the Gunicorn parser) with
total stripping in both application branches; the normalized CLIENT IP
itself via the safe request-log `client` field (a TLS client bound to
127.0.0.2 is logged as 127.0.0.2, never its spoofed values; the
Gunicorn access line's `peer` field is the POST-middleware REMOTE_ADDR -
the normalized one-hop client for trusted traffic - and the original
socket peer of a trusted dial stays on `request.remote_peer`, unlogged);
an untrusted
direct bridge peer (probe container claiming the service hostname) getting
301, with its own bridge IP as the original socket peer of the rejected
request in the Gunicorn access line (the 301 is issued before the safe
request log middleware completes) and no spoofed value in any captured
log; the layered body-size contract (3 MiB form, above the application's
2.5 MiB cap → early application 400 without the body being read; 11 MiB
multipart → edge 413; 11 MiB **chunked** multipart → empty-form 200 (unread, not a rejection); 11 MiB unread
body → 200, honestly labeled bounded-not-rejected; a 640 KiB multipart
without CSRF → early 403; a 640 KiB above-floor multipart completing); the
shipped `read_body_idle 30s 1024` pair cutting stalled and below-floor
trickling bodies (the cut surfaces to the client as Caddy's 499) while the
pool stays responsive during the cut; a sender above the minimum rate
is also cut by the total body deadline (declared 60s-to-3s test substitution);
slow-header, oversized-header (431), and idle-connection bounds; private
docs staying 404; malformed-request 400 without raw echo; Gunicorn safe
logger categories; direct host→app 301; and a dead-DB instance (liveness
200, readiness a safe 503, production 500 with no error or credential
leakage through the identical TLS proxy contract).
The wrapper additionally asserts that the captured output never carries the
synthetic database password (sentinel set via
`SLAIF033B_BOUNDARY_DB_PASSWORD`) and that no owned container/volume/image
residue remains; dedicated tests prove that a foreign container or volume
holding an expected owned name is refused and left untouched, that a
creation race (foreign claim of the app name after the run's pre-creation
check) is left untouched by the failed create, and that an injected
mid-run failure (the Caddy session leader SIGKILLed while its child
survives) leaves no owned container, volume, image, or process-session
residue and does not kill a foreign session. Test-only dials exist for
these injections (`SLAIF033B_BOUNDARY_PROJECT`, `SLAIF033B_BOUNDARY_CADDY`,
`SLAIF033B_BOUNDARY_DB_PASSWORD`, `SLAIF033B_BOUNDARY_SLOW_APP_UP_S`,
`SLAIF033B_BOUNDARY_FAULT`); an operator never sets them. In CI the test
job installs the pinned official Caddy v2.11.6 artifact (sha256-verified,
self-reported version asserted), so the required real-HTTPS evidence runs
at the implementation head rather than skipping. Focused suites for the
same boundary without the full rehearsal: `tests/test_proxy_gunicorn.py`
(real Gunicorn forwarding, parser, and safe-logger behavior) and
`tests/test_proxy_security.py` (middleware trust, headers, and log
privacy).

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
| Proxy/TLS trust boundary | test_proxy_gunicorn.py/test_proxy_security.py (real Gunicorn forwarding/spoofing, parser and log privacy); test_https_boundary.py plus deploy/rehearse_https_boundary.sh (owned real-HTTPS rehearsal, pinned Caddy v2.11.6, loopback-only, owned resources) |
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

Shared abuse controls: `tests/test_abuse_controls.py` exercises atomic real-PG
contention, bounded locked-row failure, expiry/cleanup and adapter behavior.
`tests/test_abuse_http.py` launches the production application with real
Gunicorn workers and the shipped TLS proxy. It proves worker-independent
allowances, forwarded-header spoof resistance, shared member/admin identity
limits, valid logins, multiple-token account budgets and safe DB failure.
Fixtures use owned ports, short-lived per-client certificates and explicit
synthetic environments; no production data or global trust-store changes.

## Public entry, administration admission, browser identity (task guidance)

Focused task suites for the public entry, administration admission and
browser identity work:

```bash
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test \
  tests/test_product_entry.py tests/test_assets_admin.py \
  tests/test_abuse_controls.py tests/test_abuse_http.py tests/test_web_human_mvp.py
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test \
  --browser chromium tests/browser/test_product_entry_browser.py
```

Run these only from an owned disposable source copy against an explicit
owned PostgreSQL17 project (unique owned test database per run, product-test
child envs with `OAP_ROLE` cleared and explicit `PYTHONPATH`/settings/DB
URLs); never from the valuable working checkout. The browser suite captures
privacy-safe 1440/390 screenshots for visual review; round chronology and
results belong in the immutable OAP reports, not here.

## Form guidance (SAR-044) (task guidance)

Focused suites for the rendered form/choice guidance work:

```bash
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test \
  tests/test_form_guidance.py
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test \
  --browser chromium tests/browser/test_form_guidance_browser.py
```

Same owned-disposable rules as above: never run product tests from the
valuable checkout; unique owned test database per run. The server suite
asserts rendered help bound to each control's own `aria-describedby`
(including both rendered password-choice radios bound to the first choice's
help id, kept on the invalid-POST re-render), human scope labels,
humanized policy units (including non-round minutes and the
fresh-install default policy rendered through the real initializer, minimum
1 minute), daylight-saving occurrence semantics (ambiguous
Automatic rejected, explicit occurrences, nonexistent spring-forward
times), admin password-change enable/disable behavior on GET and
invalid-POST pages, the rendered permission wording pinned against the real
authorization (staff without model permissions reach the management area;
administration model operations keep model-permission enforcement and
protected models), and the live routing of the staff asset REST endpoints
versus the unrouted legacy `assets/views.py` HTML views; the browser suite
checks visible, nearby help at 1440 and 390 — bound where the control
carries `aria-describedby`, and after the admin widgets initialize for the
JS-generated select-filter list boxes (both from/to boxes of every
permission/group selector) and both rendered password-choice radios, with
the invalid password POST keeping the rendered, bound help — including every
admin surface (login, user add/change,
password change, group add, asset add/change, tag add) — with full-page
captures for long admin forms, keyboard access and overflow checks, and
privacy-safe screenshots (never the one-time token page, no
credential/verifier/token/CSRF/cookie/HAR/trace material). The full control
inventory and coverage map, including the legacy unrouted-controls
classification, live in `docs/ux/form-guidance-inventory.md`.

## Branding (SAR-045) (task guidance)

Focused suites for the optional operator appearance-override work
(`docs/branding.md`):

```bash
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test \
  tests/test_branding.py
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test \
  --browser chromium tests/browser/test_branding_browser.py
```

Same owned-disposable rules as above: never run product tests from the
valuable checkout; unique owned test database per run; child envs with
`OAP_ROLE` cleared and explicit `PYTHONPATH`/settings/DB URLs.

- `tests/test_branding.py` asserts the fixed-slot mechanism end to end:
  disabled/missing/empty directories, real response bytes/MIME/headers,
  CSS/image/SVG content and size negatives, wrong-magic and ambiguity,
  symlink/special-file/traversal refusals, per-slot fallback independence,
  safe refresh (mtime) semantics, and preserved auth/error behavior.
  Its final test is the owned Docker qualification: a tracked-file
  snapshot build, rendered overlay topology against BOTH base Compose
  files, and the same built image run in production topology (private
  PG17, UID 10001, read-only rootfs) first default and then with the
  read-only branding mount, including a write refusal and an
  in-container invalid-asset fallback; unique owned project, synthetic
  configuration and exact owned cleanup. It skips honestly only when the
  docker/git prerequisites are absent.
- `tests/browser/test_branding_browser.py` qualifies the default identity
  and one institutional override fixture at 1440/390 for landing, member
  login, admin login, member dashboard + form, staff page and admin
  index: actual asset requests, selected imagery, computed CSS tokens,
  stylesheet order (override after built-in/admin styles), the compact
  logo switch at narrow widths, the safe invalid-override fallback,
  labels/keyboard/no overflow, CSRF and no framework branding. Screenshots
  are privacy-safe and land in the ignored `test-results/` directory.
