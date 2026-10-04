<!-- OAP-META
{
 "kind": "report",
 "id": "033-a",
 "order_path": "oap/orders/033-a-proxy-boundary-hardening.md",
 "order_sha256": "c13ea222cb109720d4746c58a0e5808f493bcf00f67fe8566d38119d16bc3be1",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 65,
 "pr_number": 66,
 "branch": "codex/65-oap-033-a-proxy-boundary-hardening",
 "implementation_head": "3c184b8aaf019500ab4916032c3d8ddc46860124",
 "base_sha": "79a1d192aeba2b0a422945aa6a07ed0b0f19e98d",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "3c184b8aaf019500ab4916032c3d8ddc46860124",
  "runs": [
   {"run_id": 37192426066, "workflow": "CI", "event": "pull_request", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 37192426088, "workflow": "oap", "event": "pull_request", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 033-a report — harden and qualify the HTTPS/proxy trust boundary

Order digest: `c13ea222cb109720d4746c58a0e5808f493bcf00f67fe8566d38119d16bc3be1`
(committed `oap/orders/033-a-proxy-boundary-hardening.md`, strategy-published order
bytes as-is; `state: FINAL`, `pr_mode: CREATE_OR_RESUME`, `decision_class: D0`,
`Decision: NONE`). Active pointer `oap/active` = `033-a` + LF (verified by xxd:
`3033 332d 610a`, 6 bytes).

Implementation head SHA: 3c184b8aaf019500ab4916032c3d8ddc46860124

Report publication commit: SELF

**Result: COMPLETE** — all eight numbered acceptance criteria met with real
evidence (real Caddy v2.11.6 edge, real Gunicorn, real PostgreSQL 17, real
browser suite). The round implements the ordered trusted-peer forwarding
contract, layered body bounds, server-level incoming deadlines, safe
Gunicorn/route-template logging, the owned real-HTTPS qualification rehearsal,
and the corresponding operator docs plus ADR 0015. No merge was performed;
the PR awaits strategy's development-merge gate. Shared login/API abuse
controls, UI/branding, HSTS ramp completion, and the final Internet-exposure
ICA remain later, separate gates — no Internet-readiness is claimed.

## 1. Starting state and E-list reconciliation (verify, do not assume)

- Branch `codex/65-oap-033-a-proxy-boundary-hardening` existed locally at base
  `79a1d192aeba2b0a422945aa6a07ed0b0f19e98d` (main, verified merge of PR #64,
  issue 63 closed) with the previous session's uncommitted 033-a work
  preserved; no PR and no report existed. Remote base re-verified before the
  first commit.
- Ordered reads completed: root router -> `oap/coding-instructions/AGENTS.md`
  -> `ARCHITECTURE-for-agents.md` -> `OAP-COMMUNICATION-coding-agent.md` ->
  exact active order -> `SECURITY-CORE.md`/`TESTING-CORE.md` -> scoped
  excerpts (production settings/env/middleware/logging, Gunicorn 23
  forwarding/parser sources, Caddy v2.11.6 sources, `deploy/Caddyfile.example`,
  rehearsal/test entry points). No strategic history read.
- STRATEGIC safety-recovery workorder
  (`workorders/033-a-SAFETY-RECOVERY.md`, supervision home) was read before any
  rehearsal execution; its owned/disposable/loopback-only/no-inherited-operator-DB
  boundary is restated in the rehearsal header and enforced by the script
  (see sections 2.1 and 8).
- Proven E-list facts carried from the order (live main79a1d192; verified
  report head 9e4d4137 with all five checks green; issue 65 selected, no open
  PR; the independent probe findings — invalid Host 400, untrusted
  `X-Forwarded-Proto` spoof reaching 200, `JsonLogFormatter` TypeError on a
  non-JSON `HttpRequest` extra) were re-verified by the new negative tests
  rather than re-probed ad hoc.

## 2. Acceptance evidence (ordered criteria)

### 2.1 Criterion 1 — operator-owned Caddy qualified, owned loopback-only HTTPS test

- Caddy **v2.11.6** pinned in `deploy/rehearse_https_boundary.sh`
  (`CADDY_VERSION=v2.11.6`, exit 42 on any other version) and named in
  `deploy/Caddyfile.example`, `docs/deployment.md` section 8, and ADR 0015.
  The example configuration was validated against the actual binary
  (`caddy adapt`/`caddy validate` clean; only two expected cosmetic
  "Unnecessary header_up" warnings because the headers are set explicitly for
  overwrite semantics).
- The real HTTPS test (`deploy/rehearse_https_boundary.sh`) uses kernel-assigned
  unique loopback ports, a 1-day synthetic RSA certificate for
  `slaif-boundary.test` trusted only by per-client `--cacert`/SNI, Caddy bound
  to 127.0.0.1 only with `admin off` and `auto_https off`, and owned
  uniquely named PostgreSQL 17 container/volume. No public DNS, no ACME, no
  OS trust-store changes. Every resource is owned by the run; name collisions
  are refusals, never adoptions; cleanup is identity-validated and runs on
  failure. PASSED locally end to end (`https-boundary=ok`, exit 0, 21 checks)
  at the implementation head.
- No plugin/infrastructure framework added: the existing operator-owned Caddy
  baseline is kept; the optional Compose proxy alternative was compared and
  not adopted (the app stays loopback-published and the proxy host-side).

### 2.2 Criterion 2 — explicit trusted peer list, one-hop identity, real Gunicorn

- `env_trusted_proxy_peers`/`validate_trusted_proxy_entry`
  (`src/slaif_reservation/config/env.py`): required in production; entries
  must be explicit IPs or point-to-point networks (IPv4 `/31`, IPv6 `/127`);
  broad ranges (`0.0.0.0/0`, `172.16.0.0/12`, `10.0.0.0/8`, `192.168.0.0/24`,
  `192.168.0.0/30`, …) are rejected — negative tests in
  `tests/test_settings.py`/`tests/test_proxy_security.py`.
- `TrustedProxyForwardingMiddleware`: trusted peer honors exactly `http`/
  `https` `X-Forwarded-Proto` and single-IP `X-Forwarded-For` (ambiguous
  chains fall back with a category-only `proxy-ambiguity` warning); untrusted
  peer gets all forwarding headers stripped, `wsgi.url_scheme` pinned to the
  real transport, and the peer as client identity (`request.client_ip`,
  written back to `REMOTE_ADDR`). `SECURE_PROXY_SSL_HEADER` is no longer used
  in production settings, so a server-derived scheme cannot bypass the list.
- Real Gunicorn proof (`tests/test_proxy_gunicorn.py`): trusted peer
  (`127.0.0.1,::1`) forwarding honored; untrusted peer — a client socket bound
  to `127.0.0.2` reaching the server at `127.0.0.1` with trusted peers
  `127.0.0.1/32`, exactly the STRATEGIC workorder construction — spoofed
  `X-Forwarded-Proto: https` + `X-Forwarded-For` produce no scheme change and
  identity `127.0.0.2`; the `wsgi.url_scheme` bypass attempt is neutralized;
  underscore wire variants never reach the app (`--header-map drop`). All
  real-Gunicorn call sites in the suite bind loopback only (no non-loopback
  listeners, no external/private-host probes).
- Docker bridge-gateway peer: documented with exact discovery commands
  (`ip route show default dev <bridge>`, `docker network inspect … .IPAM
  .Config[].Gateway`) in `deploy/env.production.example`, `docs/deployment.md`
  section 8 and `INSTALL.md` step 2/12; the internal-alpha rehearsal exercises
  the supported operator path with `SLAIF_TRUSTED_PROXY_PEERS=127.0.0.1`
  (in-container probe) and host-side smoke probes arriving as direct
  (untrusted) clients through the bridge — the contract under test.

### 2.3 Criterion 3 — production validation fail-closed; healthcheck contract retained

- Production settings require `SLAIF_DJANGO_SECRET_KEY`,
  `SLAIF_ALLOWED_HOSTS` (wildcard `*` rejected), `SLAIF_CSRF_TRUSTED_ORIGINS`
  (bare origins, `https`-only while SSL redirect is on),
  `SLAIF_TRUSTED_PROXY_PEERS`, `DATABASE_URL`, distinct 32+ byte pepper;
  `SLAIF_DEBUG` rejected; secure session/CSRF cookies and SSL redirect on by
  default; HSTS stays zero-default validated opt-in. Negative fixtures in
  `tests/test_settings.py`.
- The verified healthcheck contract is retained and made consistent: the
  in-container probe dials `127.0.0.1` with `X-Forwarded-Proto: https`, so
  `127.0.0.1` must be in `SLAIF_ALLOWED_HOSTS` **and** in
  `SLAIF_TRUSTED_PROXY_PEERS` (INSTALL.md step 2, compose healthcheck comment,
  `deploy/env.production.example`). No blanket proxy-header trust remains.
- The internal-alpha rehearsal keeps `SLAIF_SECURE_SSL_REDIRECT=false` with
  http origins **only** because that synthetic deployment has no
  TLS-terminating proxy; it is now explicitly commented as a deliberate
  plain-loopback rehearsal choice, and the real-HTTPS rehearsal qualifies the
  strict redirect/secure-cookie behavior against the real proxy (301 for
  plain-transport untrusted requests; secure cookies; CSRF 302 login
  round-trip). No bypass is silently preserved for real service deployment.

### 2.4 Criterion 4 — public proxy bounds (headers/bodies/idle/buffers/upstream)

- `deploy/Caddyfile.example` (qualified with v2.11.6):
  `request_body { max_size 10MB }` whole-body 413 for bodies downstream
  handlers actually read; `request_buffers 1MB` in-memory bound kept strictly
  below the cap (Finding A); server-level `servers { timeouts { read_header
  60s; read_body_idle 30s 1024; write_idle 30s; idle 5m } }` (defaults when
  omitted; route-level `timeouts` observed ineffective — Finding B); upstream
  transport `dial_timeout 10s`, `response_header_timeout 30s`,
  `read_timeout 60s`, `write_timeout 60s`, `keepalive 3s` (below Gunicorn
  keep-alive 5).
- Rehearsal proves against the real stack: body-cap-app (11 MiB urlencoded
  -> exactly 400, body never read), body-cap-edge (11 MiB multipart upload ->
  exactly 413, stable), body-cap-unread (11 MiB octet-stream -> 200 + pool 200,
  bounded), body-stall-bounded (trickling body cut at the `read_body_idle`
  bound, HTTP 499), slow-header-bounded (slow header cut at `read_header`),
  idle-connection-closed.
- Gunicorn `--timeout 30` documented as worker-liveness, not a per-request
  deadline; the threaded 3x8 pool, keep-alive 5 and timeout 30 are preserved
  unchanged (eight Gunicorn responsiveness regressions still pass in the full
  suite).
- Response headers: `-Server` removed, `X-Content-Type-Options: nosniff`,
  `Referrer-Policy: strict-origin-when-cross-origin` at the edge; Django
  `X-Frame-Options: DENY`, `Sec-Fetch`-independent secure cookies, one-time
  token no-referrer/no-store values unchanged. No CSP was added: the actual
  admin/Swagger/token-history compatibility work is explicitly staged to the
  later safe-branding objective per the order; no existing protection was
  broken or waived (rehearsal `response-headers` check).

### 2.5 Criterion 5 — safe health, private schema/docs, error boundaries

- `/health/live` 200 with a dead DB (rehearsal `dead-db-boundary` against a
  second Gunicorn on an unroutable database port); readiness failures return
  503 with a safe body (no database/migration details — asserted by existing
  health suites, unchanged).
- Schema/docs stay disabled by default and staff-only when enabled; the
  unauthorized member/management/private-route and production 400/403/404/500
  negatives remain covered by the existing suites (full run green at the head).
  No production crash endpoint was added; error responses carry no traceback,
  SQL, secret, request object or private sentinel (Gunicorn parser rejections
  now return the fixed `SAFE_ERROR_DETAIL` body — never the echoed raw input).

### 2.6 Criterion 6 — privacy at actual app/Django/Gunicorn/Caddy log points

- App request logs use the matched **route template** or `unmatched-route`
  (never the raw path); method/status/duration/request-ID only.
- The reproduced `JsonLogFormatter` TypeError is fixed without
  `default=str`/repr leakage: unserializable request/exception state becomes
  category-only markers (`[unserializable]`, exception type, bounded
  file:line stack) in `src/slaif_reservation/config/logging.py`.
- Gunicorn: `SlaifGunicornLogger` (new `src/slaif_reservation/config/gunicorn.py`,
  wired in the `Dockerfile`/compose commands) emits JSON access lines
  (method/status/size/peer) and category+peer for parser failures — never the
  raw request line/target/headers/body — and `install_safe_error_responses`
  replaces Gunicorn's error-page detail so rejected requests are not echoed.
  Real-parser privacy is proven by the `parser-privacy` real-Gunicorn test
  (malformed request with an in-memory canary; canary asserted absent from
  captured logs and response) and the `access-privacy` test (query-string
  canary absent from access logs).
- Caddy: access logs off by default in the example (no `log` directive); the
  documented opt-in requires JSON field exclusions. Rehearsal `canary-log-
  privacy` checks the app/Caddy/Gunicorn log sinks for hostile-path/query/
  header canaries; all green. Tests use in-memory canaries and
  status/category diagnostics; failed sentinels are never printed.

### 2.7 Criterion 7 — real HTTP positive/negative evidence and full suites

- Rehearsal checks (all PASSED at the implementation head): owned-pg,
  app-provisioned, app-up, edge-up, tls-health, tls-requires-owned-ca,
  tls-port-rejects-plain-http, response-headers, forwarding-overwrite,
  login-secure, body-cap-app, body-cap-edge, body-cap-unread,
  body-stall-bounded, slow-header-bounded, idle-connection-closed,
  canary-log-privacy, malformed-request-safe, gunicorn-logger-live,
  direct-redirect, dead-db-boundary.
- Production Compose built and rendered (CI container job green at the head:
  non-root 10001:10001, read-only, loopback app, unpublished DB); local full
  pytest (test settings, real PG 17): **696 passed, 1 failed** where the single
  failure is the OAP harness strategic-launcher test that refuses the
  launcher-injected `OAP_ROLE=CODING` environment of the local session — the
  order itself directs clearing the inherited `OAP_ROLE` for harness tests;
  with it cleared the full harness suite is **154 OK**, and CI (clean
  environment) reports oap-harness **success** at the head. No product test
  failed locally.
- The eight Gunicorn responsiveness regressions, real PG concurrency, browser
  (Chromium, `tests/browser`), idempotency and restore suites all pass in the
  same full run.
- The implementation branch contains two commits: `bb43dd2a` (implementation)
  and `3c184b8a` (CI repair at the first head: the boundary wrapper's
  foreign-container test now converts an honest prerequisites exit 42 into a
  pytest skip on runners without the pinned Caddy — mirroring its sibling
  tests — plus a factual loopback-only clarification of the real-Gunicorn
  fixture docstring). The local full suite above ran at `bb43dd2a`; the
  wrapper change was verified locally (focused `tests/test_https_boundary.py`
  4 passed, including the live foreign-container refusal against the pinned
  Caddy) and by the CI test job at `3c184b8a` (693 passed, 4 skipped), where all
  four boundary rehearsal wrapper tests honestly SKIP (runner has no Caddy;
  script exit 42) and every other suite runs to a pass.

### 2.8 Criterion 8 — operator docs and ADR

- `docs/deployment.md` section 8 rewritten (trust contract with peer
  allowlist/discovery, overwrite-never-append, untrusted stripping, layered
  body contract, server-level incoming deadlines with the route-level
  warning, headers/HSTS ramp, `SECURE_PROXY_SSL_HEADER` no longer used);
  sections 4/5/9 updated accordingly. `docs/security-model.md` adds the
  proxy->app trust boundary item, route-template logging, layered limits and
  the DoS row. `SECURITY.md` gains the two contract principles. `INSTALL.md`
  steps 2/12, sections 11 and 15 updated. `TESTING.md` documents the
  rehearsal invocation/exit codes and the boundary suites. ADR 0015 records
  the trust-boundary decision, the two Caddy v2.11.6 findings, and the
  deferred gates. The precise Internet-readiness warning is retained
  (sections 6/12 of INSTALL, security model, ADR consequences).
- `request.client_ip` is documented as the single source for the next limiter
  objective (no second raw-XFF interpretation).

## 3. Changed files and scope

Implementation (before the report commit), all within ordered `allowed_paths`:

- `src/slaif_reservation/config/env.py` — bounded production-security
  validation (trusted peer entries, strict origin validation).
- `src/slaif_reservation/config/settings/production.py` — proxy/trust/
  security settings, fail-closed validation, middleware order.
- `src/slaif_reservation/config/middleware.py` — `TrustedProxyForwarding-
  Middleware`, safe response-header/log behavior.
- `src/slaif_reservation/config/logging.py` — safe robust production log
  formatting (route template, unserializable-safe exception metadata).
- `src/slaif_reservation/config/gunicorn.py` — **new** safe logger/error-
  response support (real parser privacy experiments required it).
- `Dockerfile`, `compose.yaml`, `compose.production.example.yaml` — Gunicorn
  `--forwarded-allow-ips 127.0.0.1,::1 --header-map drop --logger-class
  slaif_reservation.config.gunicorn.SlaifGunicornLogger` (pool/bind/user/
  build semantics preserved).
- `deploy/Caddyfile.example` — operator proxy trust/timeout/buffering/header
  contract (pinned Caddy v2.11.6).
- `deploy/env.production.example` — `SLAIF_TRUSTED_PROXY_PEERS` + discovery.
- `deploy/rehearse_https_boundary.sh` — **new** owned disposable real-HTTPS
  qualification script.
- `deploy/rehearse_internal_alpha_deployment.sh` — synthetic production
  contract adaptation (trusted peer set + deliberate plain-loopback comment;
  ownership/refusals preserved).
- `tests/test_proxy_security.py`, `tests/test_proxy_gunicorn.py`,
  `tests/test_https_boundary.py` — **new** boundary tests.
- `tests/test_settings.py`, `tests/test_operational_hardening.py` —
  strengthened fixture/config assertions for the affected settings.
- `tests/test_api_tokens.py` — **one-line fixture repair** (see section 3.1
  bounded discrepancy): the existing production-fail-fast subprocess test's
  "minimal valid production env" lacked the newly ordered required
  `SLAIF_TRUSTED_PROXY_PEERS`; no assertion changed.
- `docs/deployment.md`, `docs/security-model.md`, `SECURITY.md`,
  `INSTALL.md`, `TESTING.md`, `docs/decisions/0015-https-proxy-trust-boundary.
  md` — the ordered documentation/ADR surface.
- `oap/orders/033-a-proxy-boundary-hardening.md`, `oap/active` — exact
  strategy-published order bytes and pointer (`033-a` + LF).

### 3.1 Bounded discrepancy (out-of-allowlist file, reported not smuggled)

`tests/test_api_tokens.py` is not in the order's `allowed_paths`, but its
`test_api_token_production_setting_fail_fast` subprocess test hard-codes a
"minimal valid production environment" fixture; the order-mandated required
`SLAIF_TRUSTED_PROXY_PEERS` made that fixture stale and the test's positive
case fail at the implementation head. The repair is a single fixture line
(`"SLAIF_TRUSTED_PROXY_PEERS": "127.0.0.1"`), no assertion or behavior
change. This is reported to strategy as a bounded discrepancy rather than a
silent scope expansion; no other file outside the allowlist was touched.

## 4. Commands and results (summary)

Local environment: Linux x86_64, Caddy v2.11.6 (`~/.local/bin/caddy`), Docker
29.1.3, `postgres:17@sha256:d13db94…` (cached), uv-managed Python 3.13,
Django 5.2.17, Gunicorn 23.0.0, Playwright Chromium installed. Local PG 17 at
127.0.0.1:54330 (round-owned product-suite DB, `slaif033a-pg`); rehearsal
uses its own uniquely named PG17 container/volume per run.

| Command (implementation head) | Result |
| --- | --- |
| `uv run ruff check .` | PASSED (all checks) |
| `uv run ruff format --check .` | PASSED (190 files already formatted) |
| `uv run mypy src` | PASSED (120 files, strict) |
| `uv run --env-file .env python manage.py check` | PASSED (0 silenced) |
| `uv run --env-file .env python manage.py makemigrations --check --dry-run` | PASSED (no changes) |
| `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test` (at `bb43dd2a`) | PASSED 696 / FAILED 1 (harness env artifact, see 2.7) / ~5.5 min |
| same command at `3c184b8a`, focused `tests/test_https_boundary.py` | PASSED 4 (rehearsal `https-boundary=ok` exit 0, ~53 s, owned resources cleaned) |
| `env -u OAP_ROLE python3 -m unittest discover -s tests/oap -p 'test_*.py' -v` | PASSED 154 OK |
| `uv run pip-audit` | PASSED (no known vulnerabilities) |
| `git diff --check` | PASSED |
| `uv run --env-file .env python manage.py spectacular --file build/openapi/schema.yaml --validate --fail-on-warn` | PASSED (schema unchanged) |
| `uv run --env-file .env python manage.py migrate --noinput` then `operational_check` | PASSED (CI-equivalent order) |
| `bash deploy/rehearse_https_boundary.sh` (owned, loopback-only) | PASSED `https-boundary=ok` exit 0, 21 checks; cleanup verified, no residue |

Focused suites at the head: `tests/test_proxy_gunicorn.py` +
`tests/test_proxy_security.py` + `tests/test_settings.py` +
`tests/test_operational_hardening.py` = 130 passed.

## 5. CI observed before authoring

At implementation head `3c184b8aaf019500ab4916032c3d8ddc46860124` (PR #66,
event pull_request):

- `CI` run 37192426066 (pull_request, head 3c184b8…): quality success (20 s),
  test success (4 m 25 s), security success (18 s), container success (32 s) —
  all five job statuses success at the exact head;
- `oap` run 37192426088 (pull_request, same head): oap-harness success (37 s).

All five exact-head checks (quality, test, security, container, oap-harness)
PASS; both run conclusions `success` with `headSha` equal to the
implementation head (verified via `gh run view --json headSha,conclusion`).

The first implementation head `bb43dd2a94c8fc2580bc612619425b317d5b993b` was
fully observed before authoring: quality success, container success, security
success, oap-harness success, test FAILED (5m27s) with exactly one failure —
`test_https_boundary_refuses_foreign_container` asserting non-42 while the
CI runner (no Caddy) made the rehearsal exit 42 honestly (`caddy-missing`);
693 passed, 3 skipped (the honest rehearsal skips). That failure is the
wrapper defect repaired in `3c184b8a`; no product failure occurred at either
head.

Report-head CI: NOT YET OBSERVED AT AUTHORING.

## 6. Security, data, dependencies and local tools

- No real secrets, credentials, private data, or operator `.env` values
  entered the repository, tests, logs, or this report. The rehearsal and the
  boundary tests use synthetic generated values only; the rehearsal unsets
  `DATABASE_URL`/`TEST_DATABASE_URL`/`DJANGO_SETTINGS_MODULE`/
  `SLAIF_TRUSTED_PROXY_PEERS` and never loads the repository `.env`; secrets
  live in 0600 work files or environment, never argv. The captured-output
  sentinel test (`SLAIF033A_BOUNDARY_DB_PASSWORD`) asserts no database
  password leak.
- No public exposure, DNS, ACME, OS trust-store, firewall, or real service
  was touched; no real lab/GPU/SmartScheduling contact. All rehearsal
  network activity stayed on owned 127.0.0.0/8 addresses (Caddy and Gunicorn
  bind 127.0.0.1; the untrusted-peer negative uses a 127.0.0.2 client
  source; the dead-DB probe points at unroutable 127.0.0.1:1).
- No new dependencies: the change set adds no third-party packages (Gunicorn
  is the existing pinned application server; the rehearsal uses the system
  python3 standard library, caddy, openssl, curl, docker).
- One round-owned diagnostic PostgreSQL container left by the previous
  session (`diag033a2-*`, loopback-only, synthetic) was identified as owned
  033-a residue and removed with its anonymous volume before the validation
  run; two pre-round (4-week-old, stopped, postgres:16) containers
  `slaif-155f-postgres-*` are foreign to this round and were left untouched.
- No merge, self-approval, auto-merge, force-push, reset/clean/stash
  performed.

## 7. DHA outcome and unresolved gates

`Decision: NONE` — no CRIT entry appended or needed; no coding-side D1/D2
adjudication. Unresolved (deliberately deferred, per the order): shared
login/API abuse controls (next separate objective), UI/branding and the CSP
compatibility work, HSTS ramp completion after final hostname validation,
and the fresh isolated ICA at the exact merged revision. Until those
complete, Internet readiness is NOT claimed.

## 8. Safety discrepancies and prototype repairs (STRATEGIC workorder)

The STRATEGIC safety-recovery workorder (read before any rehearsal
execution) found the earlier rehearsal prototype unsafe. Repairs, all in
`deploy/rehearse_https_boundary.sh` unless noted:

1. **Inherited operator DB (workorder headline).** The prototype inherited
   `DATABASE_URL`/default 54330 and could receive migrations in an inherited
   database. Now: inherited product environment variables are unset at
   start; a unique owned PG17 container/volume (name includes PID+random
   hex) is created; a pre-existing name is a refusal, never an adoption, and
   the container/volume are never dropped-elsewhere, terminated or migrated;
   the explicit synthetic `DATABASE_URL` is passed to every
   migration/seed/check invocation. A same-round earlier draft also lacked
   an explicit loopback bind and disabled automatic HTTP/ACME listeners:
   Caddy now binds 127.0.0.1 only, `admin off`, `auto_https off`.
2. **Cleanup ownership/termination.** PID-only cleanup became bounded
   TERM->KILL->reap per owned process session plus an orphan `/proc` audit on
   the `--bind` markers, running on failure too. A latent defect found
   during this session's verification: the EXIT trap's `set +u` reset `$?`
   to 0 before `local status=$?` captured it, so a refusal path exited 0 —
   and the same cleanup unconditionally `docker rm -f`'d the container name,
   which in the foreign-name refusal case deleted the FOREIGN container
   (reproduced live before the fix). Fixed by capturing the status before
   `set +u` and gating container/volume removal on run-owned creation
   flags; the foreign-container refusal test now proves non-zero exit and
   the foreign container left running.
3. **Non-loopback untrusted-peer probe (workorder).** The real-Gunicorn
   untrusted-peer negative now uses exactly the workorder construction:
   client bound to 127.0.0.2 -> server 127.0.0.1, trusted peers
   127.0.0.1/32. No LAN-facing listener, no external/private host probe
   anywhere in the suite.
4. **Early-403 false pass (workorder).** Oversized-POST negatives originally
   403'd at CSRF before body parsing; the body-cap checks now perform a
   private per-check CSRF round-trip (tokens kept out of argv via 0600 files
   / `curl -K`) so the bodies actually reach the application/edge limits and
   the asserted codes are the contract codes (400 app / 413 edge / bounded
   unread), not early CSRF/redirect.
5. **Version pin honesty.** The prototype's example header claimed Caddy
   v2.11.7; the qualified and pinned binary is v2.11.6. Corrected in
   `deploy/Caddyfile.example` (header), the rehearsal, the docs and ADR 0015.
6. **Real Caddy v2.11.6 behavior findings (new, drive the design).**
   - Finding A: `request_buffers` sized equal to `request_body max_size`
     exhausts the cap counter during buffering (proven on the real stack:
     11 MiB octet-stream -> 200), so the shipped buffer (1MB) is a strictly
     lower memory bound and form-type full-body rejection is delegated to
     Django's `DATA_UPLOAD_MAX_MEMORY_SIZE` Content-Length pre-check (400,
     body unread).
   - Finding B: the route-level `timeouts` directive's read/write deadlines
     were observed NOT to take effect on stalled body reads in v2.11.6
     (12 s hang; identical server-level `read_body_idle` cut at 3.1 s with
     HTTP 499). The shipped contract uses the global `servers { timeouts { …
     } }` form and documents the route-level warning; built-in defaults are
     recorded from v2.11.6 sources (`app.go`).
7. **Rehearsal fixture correctness repairs** (protocol-level, no boundary
   weakening): Django `JsonResponse` spaced-body greps; curl cookie-jar
   `TRUE`/`FALSE` Secure column; login field is `username` (label "Email");
   413-probe EPIPE guards; `/proc` cmdline NUL-safety; SNI + owned-CA TLS
   probes on the TLS port (no trust weakening); idle-probe unit
   normalization (seconds vs nanoseconds); declared read-timeout constants
   under `set -u`.

What changed versus the workorder's description: the rehearsal now exists
only in its repaired form; the unsafe prototype was never executed (the
previous process was stopped before rehearsal subprocess start, and no
inherited database received migrations — the inherited-DB risk was eliminated
by construction before first run).

## 9. Limitations and recommendation

- The CI test job's rehearsal wrapper honestly SKIPS (script exit 42) on
  runners without the pinned Caddy v2.11.6; the real-HTTPS boundary evidence
  then rests on the local qualified run at the implementation head plus the
  always-run real-Gunicorn suites. Requiring Caddy on CI runners is a CI
  tooling decision outside this order.
- HSTS is zero by default by design; enabling it requires the documented
  certificate/domain ramp after the final hostname is verified.
- The trusted-peer list is operator-maintained; a peer change (new bridge
  gateway, new proxy) requires the documented rediscovery. A future
  objective may add an operational_check warning for the common
  missing-gateway case (not done here: read-only diagnostics only if
  necessary, and none was necessary).
- No load/DoS immunity is claimed; the bounds are finite-response controls
  for the supported single-host alpha shape.
- Recommendation: strategy may proceed to the development-merge gate for
  this PR when it chooses; the next objective is the shared login/API abuse
  control, which will consume `request.client_ip` as its single client
  identity source.
