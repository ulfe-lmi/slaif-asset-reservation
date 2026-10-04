# Deployment and Operations

**Status:** CI-green, production-shaped internal-alpha candidate; a real deployment has not yet
been evidenced

## 1. Target

A maintained Linux server hosts the reservation application outside individual compute machines. It is reachable over HTTPS by authorized humans and agents. The initial workload is small enough for one web service and one PostgreSQL instance.

## 2. Service layout

```text
reverse proxy (Caddy or Nginx)
  -> Django/Gunicorn application
  -> PostgreSQL 17 on a private network

systemd timer or cron
  -> idempotent Django management commands
```

Do not run PostgreSQL on a public interface. Do not colocate production secrets in the repository or image.

## 3. Development environment

Work Order 0001 provides a repeatable development path using:

- Python 3.13 managed by `uv`;
- committed `uv.lock`;
- PostgreSQL 17 through Docker Compose;
- synthetic test data only;
- documented commands for migrations, checks, tests, OpenAPI validation, and container smoke.

No developer should need SmartScheduling credentials or production data.

The committed Compose file is development-only. It publishes PostgreSQL and the application on
`127.0.0.1` only, while keeping app-to-database communication on the internal Compose network.

The complete development installation procedure (database, locked dependencies, env file,
migrations, bootstrap import, runserver, superuser, health checks) is owned by `INSTALL.md`,
sections 3 and 4. The standard verification command set for changes is in `TESTING.md`.

Migrations are a deliberate command. They are not hidden inside the application worker startup.

Work Order 0003 adds PostgreSQL-specific reservation migrations. The migration chain installs the
`btree_gist` extension with `BtreeGistExtension()` and creates the
`reservation_no_overlap_per_asset` exclusion constraint. The deployment/migration role must be
allowed to create this extension, or an operator must preinstall it in the target database before
running migrations.

Work Order 0007 adds maintenance-blackout tables and audit action constraints. No background cleanup
or notification scheduler is introduced; blackout creation/deactivation is synchronous through the
staff management UI.

Work Order 0008 adds example-only production deployment artifacts:

- `compose.production.example.yaml`;
- `deploy/env.production.example`;
- `deploy/Caddyfile.example`;
- operator runbooks under `docs/runbooks/`.

These files describe the supported first internal-alpha shape but are not a real deployment. The
development Compose file remains unchanged and loopback-only.

Work Order 0011 adds the disposable internal-alpha rehearsal entry point
`deploy/rehearse_internal_alpha_deployment.sh`. The script creates temporary ignored
`deploy/env.production` and `deploy/secrets/postgres_password` files with synthetic values,
validates `compose.production.example.yaml`, builds the runtime image, applies migrations to
disposable PostgreSQL, runs bootstrap/import and operational checks, starts the app, verifies
health/login/management/API smoke paths, validates OpenAPI, then removes the temporary
env/secret files and Compose volume. It is local rehearsal evidence only, not a production
deployment. Its full behavior, modes (`--config-only`, `--status`, `--cleanup-owned`), and
evidence boundaries are documented in `INSTALL.md`, section 6.

Work Order 0004 adds local browser workflow tests. Development and CI install Chromium with:

```bash
uv run playwright install --with-deps chromium
```

The installed browser/runtime packages are development/test tooling only and are not production
application dependencies.

## 4. Configuration

Implemented variables:

- `DJANGO_SETTINGS_MODULE`;
- `DATABASE_URL`;
- `TEST_DATABASE_URL`;
- `SLAIF_DJANGO_SECRET_KEY`;
- `SLAIF_DEBUG`;
- `SLAIF_ALLOWED_HOSTS`;
- `SLAIF_CSRF_TRUSTED_ORIGINS`;
- `SLAIF_TRUSTED_PROXY_PEERS`;
- `SLAIF_ENABLE_API_DOCS`;
- `SLAIF_PUBLIC_API_DOCS`;
- `SLAIF_SECURE_SSL_REDIRECT`;
- `SLAIF_SECURE_HSTS_SECONDS`;
- `SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS`;
- `SLAIF_SECURE_HSTS_PRELOAD`.
- `SLAIF_API_TOKEN_PEPPER`;
- `SLAIF_API_TOKEN_MAX_LIFETIME_DAYS`.

`SLAIF_SECURE_HSTS_SECONDS`, `SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS`, and
`SLAIF_SECURE_HSTS_PRELOAD` default to disabled in production settings. Enable them only after
the final HTTPS hostname, redirects, and subdomain ownership are verified. `SECURE_SSL_REDIRECT`
and secure session/CSRF cookies remain enabled by default in production settings.

`SLAIF_TRUSTED_PROXY_PEERS` is required in production settings. It is the explicit list of
reverse-proxy peer addresses (comma-separated) whose `X-Forwarded-Proto` and single-value
`X-Forwarded-For` the application honors; every other peer is treated as a direct client with
all forwarding headers stripped (see section 8). Each entry must be an explicit IP address or a
point-to-point network (IPv4 `/31`, IPv6 `/127`); broad ranges are rejected because they would
let any host in the range impersonate the proxy. For a host-side proxy the value is the loopback
peer (`127.0.0.1`); for a proxy in a Docker network the value is the network's gateway address
(see section 8 for discovery).

`SLAIF_ALLOWED_HOSTS` must list explicit hosts; the wildcard `*` is rejected in production
settings. `SLAIF_CSRF_TRUSTED_ORIGINS` must be non-empty and every entry must be a bare origin
(`scheme://host[:port]` without userinfo, path, query, or fragment); while
`SLAIF_SECURE_SSL_REDIRECT` is enabled every entry must be an `https` origin.

`SLAIF_API_TOKEN_PEPPER` is required in production. Generate and store it as a protected deployment
secret outside the repository and image. It must be at least 32 UTF-8 bytes, distinct from
`SLAIF_DJANGO_SECRET_KEY`, and not the documented development placeholder. Replacing this single
pepper invalidates all existing API tokens until a future key-ring/rotation design is accepted.

`SLAIF_API_TOKEN_MAX_LIFETIME_DAYS` defaults to 90 and must be from 1 through 365.

Deferred variables:

- canonical external URL, email relay, structured-log destination, OIDC, and backup destination.
- login throttling/rate-limit configuration, because public local-auth hardening is deferred.

`.env.example` is for host-side local commands run explicitly as `uv run --env-file .env ...`;
Django does not automatically load it. Its `DATABASE_URL` points at the loopback-published
development database. Compose supplies the application service with its own container-internal
`DATABASE_URL` that uses hostname `db`. Never provide a production `.env`.

For production-shaped configuration, copy `deploy/env.production.example` on the deployment host and
replace every placeholder from a protected secret store into an untracked `deploy/env.production`
file. Never commit `deploy/env.production`. The production Compose example can render with
`docker compose -f compose.production.example.yaml config` before that file exists, but the
application cannot start successfully without the required runtime environment. Production settings
reject placeholder or too-short `SLAIF_DJANGO_SECRET_KEY` values and reject documented
development/test/example API-token peppers, including whitespace-padded forms.

`compose.production.example.yaml` publishes the app on loopback only. By default it binds
`127.0.0.1:8000`; set `SLAIF_APP_HOST_PORT` when rendering or running the example to choose a
different host port. The rehearsal script sets this variable from `SLAIF_REHEARSAL_PORT` so the
smoke checks probe only the configured rehearsal port.

## 5. Containers

The scaffold image:

- uses the Python 3.13 slim image;
- run as a non-root user;
- install only locked production dependencies;
- collects Django admin and drf-spectacular-sidecar static assets during image build;
- includes only the sanitized `data/bootstrap` inventory files needed by `operational_check`;
- exclude tests, caches, `.git`, local secrets, and development data;
- does not bake secrets into the image;
- expose no development server;
- emit logs to stdout/stderr.

Database migrations run as a deliberate release step, not unpredictably in every worker startup.

Build and inspect the runtime user:

```bash
docker build --tag slaif-asset-reservation:local .
docker image inspect slaif-asset-reservation:local --format '{{.Config.User}}'
docker run --rm --entrypoint test slaif-asset-reservation:local -f /app/staticfiles/admin/css/base.css
docker run --rm --entrypoint test slaif-asset-reservation:local -f /app/staticfiles/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js
docker run --rm --entrypoint test slaif-asset-reservation:local -f /app/data/bootstrap/assets.yaml
docker run --rm --entrypoint test slaif-asset-reservation:local -f /app/data/bootstrap/assets.schema.json
```

The configured runtime user must be `10001:10001`.

### Production dependencies

- `Django`: web framework, authentication, admin, ORM, migrations, sessions, CSRF, and settings.
- `djangorestframework`: versioned API foundation for later agent endpoints.
- `drf-spectacular`: generated OpenAPI schema from implemented DRF views.
- `drf-spectacular-sidecar`: local Swagger UI CSS, JavaScript, and favicon assets so API
  documentation does not depend on an unpinned CDN resource.
- `jsonschema`: Draft 2020-12 validation for the sanitized bootstrap inventory schema.
- `psycopg[binary]`: PostgreSQL driver for Django and health/readiness checks.
- `PyYAML`: safe parsing for the sanitized bootstrap inventory import command.
- `gunicorn`: production WSGI process runner used by the container image.
- `whitenoise`: conservative static-file middleware for the monolith deployment shape.

Locked versions are recorded in `uv.lock`.

### Gunicorn worker pool

All three supported defaults (the `Dockerfile` `CMD`, the development
`compose.yaml` app command, and the production example
`compose.production.example.yaml` app command) run Gunicorn with the
`gthread` worker pool:

```text
gunicorn slaif_reservation.config.wsgi:application
  --bind 0.0.0.0:8000
  --workers 3
  --threads 8
  --keep-alive 5
  --timeout 30
  --forwarded-allow-ips 127.0.0.1,::1
  --header-map drop
  --logger-class slaif_reservation.config.gunicorn.SlaifGunicornLogger
```

- The legacy `sync` pool processes one request per worker, and a client
  that connects and sends nothing — or stalls part-way through the header
  block — blocks that worker in a socket read. Three such clients occupy
  all three workers, and new connections sit in the listen backlog until a
  blocker disconnects or the arbiter's worker timeout restarts a worker.
  That is the idle-connection starvation failure: new requests time out on
  the LAN while slow or idle clients merely hold connections.
- `gthread` accepts connections in a worker event loop and serves each
  request in a pool thread. Idle keep-alive connections wait in the event
  loop and are closed after the 5 s keep-alive; only a stalled header read
  occupies a thread. The baseline is 3 workers x 8 threads = 24 request
  slots: six slow clients can occupy one full worker's thread pool while
  the remaining workers and threads keep `/health/live` and ordinary page
  loads responsive, and the existing 3-worker process isolation is
  retained.
- `--timeout 30` keeps the standard arbiter worker timeout; the binds are
  unchanged (container-internal `0.0.0.0:8000`; the service is published
  on host loopback only). It is a worker-liveness timeout, not a
  per-request deadline: stalled client input is cut by the proxy's
  server-level read deadlines (section 8), not by this flag.
- `--forwarded-allow-ips 127.0.0.1,::1` restricts Gunicorn's own
  `X-Forwarded-Proto` scheme derivation to loopback peers; the
  application trust decision is made later by
  `TrustedProxyForwardingMiddleware` against
  `SLAIF_TRUSTED_PROXY_PEERS`, which is the authoritative boundary
  (section 8).
- `--header-map drop` discards wire headers containing underscores
  before they reach the WSGI environment, so hostile `X_Forwarded_*`
  variants cannot ride on underscore spellings.
- `--logger-class slaif_reservation.config.gunicorn.SlaifGunicornLogger`
  replaces Gunicorn's default error/access formatters with safe JSON
  recorders and its raw error pages with a fixed detail (section 9).
- This is a responsiveness baseline for the supported reverse-proxied
  shape, not a load guarantee and not authorization to expose Gunicorn
  directly to the internet. The application stays reachable exclusively
  through the HTTPS reverse proxy (section 8), which must buffer client
  bodies and enforce its own read/idle timeouts; a slow-client flood is a
  proxy abuse-control concern, not something worker sizing solves.

Troubleshooting: if new requests queue while the service otherwise looks
up, suspect clients holding connections without completing requests
(idle or partial-header clients). The regression below reproduces the
starvation with the old `sync` configuration and proves the shipped
`gthread` defaults stay responsive:

```bash
uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test \
  tests/test_gunicorn_responsiveness.py -v
```

The test launches the real installed Gunicorn with the real Django routes
on unique loopback ports (the anonymous `/health/live` and `/login/` GETs
need no database), pins the supported commands to the `gthread` baseline,
and shuts its children down even after failures.

## 6. Health endpoints

- `/health/live`: application process responds; no expensive dependencies.
- `/health/ready`: database reachable and migration state is current.

Health responses contain no secrets, build environment, database host, or dependency versions beyond an approved release identifier.

Local smoke:

```bash
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready
```

Deployment smoke command:

```bash
python manage.py operational_check
```

It verifies database connectivity, applied migrations, required static assets, critical settings,
sanitized bootstrap inventory validation, and idempotency cleanup command registration. It does not
require production secrets when run under local/test settings.

For a disposable production-shaped smoke run, use the rehearsal described in `INSTALL.md`,
section 6. The rehearsal uses production settings with synthetic local-only values and disables
SSL redirect because no real reverse proxy or TLS endpoint exists in this local check.

## 7. Database lifecycle

### Migrations

- run `migrate --plan` or equivalent review before production migration;
- back up before destructive/large migrations;
- use backward-compatible expand/contract patterns once zero-downtime matters;
- do not edit previously deployed migrations;
- record application release and migration state.

Policy initialization is a deliberate operator command, not a migration.
On the supported fresh path run
`python manage.py initialize_default_policy` immediately after `migrate`:
it atomically creates the active global fallback policy `default` only
when no policy rows exist, couples the `reservation_policy.created` audit
in the same transaction, and is safe to repeat. Any pre-existing policy
configuration — active or inactive, global or asset-specific — is
preserved with no writes and no audit, so upgrades never silently
initialize or broaden an installation.

### Backup

Work Order 0008 adds PostgreSQL-native wrappers:

```bash
python manage.py backup_database --output /backups/slaif-YYYYMMDD.dump
python manage.py backup_database --output /backups/slaif-YYYYMMDD.dump --apply
python manage.py restore_database --input /backups/slaif-YYYYMMDD.dump
python manage.py restore_database --input /backups/slaif-YYYYMMDD.dump --apply
```

The default mode validates only. Apply mode uses `pg_dump` or `pg_restore`, requires
`DATABASE_URL`, writes or reads an explicit path, and avoids printing database passwords. Retention,
encryption, off-host copy, restore-drill cadence, and failure alerts remain operator policy.

A backup without a restore test into an isolated database is not release evidence.

The internal-alpha pilot readiness runbook documents the backup/restore rehearsal gate:

```text
docs/runbooks/internal-alpha-pilot-readiness.md
```

The pilot preparation pack documents the operator checklist and placeholder-only participant
communication templates for a future controlled internal lab pilot:

```text
docs/runbooks/internal-alpha-pilot-preparation.md
```

## 8. Reverse proxy and TLS

- valid certificate and automatic renewal;
- HTTP to HTTPS redirect;
- request and upload limits;
- bounded incoming read/write/idle deadlines;
- security headers coordinated with Django;
- API access logs redacted according to the security model;
- optional network restriction for `/admin/`.

Caddy (pinned v2.11.6) is the documented first internal-alpha example in
`deploy/Caddyfile.example`; Nginx remains acceptable if already operated
institutionally. The proxy must terminate HTTPS and be the single trusted
peer of the private application; it must not expose the app on any address
other than the one the proxy uses to reach it (container-internal
`127.0.0.1:8000` or the published loopback port).

### Trust contract

The application honors TLS/client-identity forwarding only from the peers
listed in `SLAIF_TRUSTED_PROXY_PEERS` (see section 4 for the strict entry
validation). The supported topology is one operator-owned proxy in front of
a private Gunicorn:

- **Host-side proxy (loopback app port):** the proxy dials the app at
  `127.0.0.1`, so the app's trusted peer is `127.0.0.1` (and `::1` where
  the dial could use IPv6).
- **Proxy in a Docker network:** the app sees the proxy as the network's
  gateway address. Discover it with
  `ip route show default dev <bridge>` on the host, or
  `docker network inspect <network>` (`.IPAM.Config[].Gateway`) when using
  the compose network. Configure exactly that address.

From a **trusted peer**, the app honors `X-Forwarded-Proto` only when it is
exactly `http` or `https`, and `X-Forwarded-For` only as a single valid IP
(the one-hop value the supported proxy writes from the real client
address). The proxy must **overwrite** both headers from the actual
connection, never append: `deploy/Caddyfile.example` sets
`header_up X-Forwarded-Proto {scheme}` and
`header_up X-Forwarded-For {remote_host}` (Caddy JSON `set` semantics), so
client-supplied values — including spoofed proto headers and ambiguous
chains — are replaced before they reach the app.

In **both branches** every forwarding header is consumed at most once and
then removed from the WSGI environment — `Forwarded`,
`X-Forwarded-For/Host/Port/Prefix`, the `X-Forwarded-Protocol`/
`X-Forwarded-Ssl` scheme variants, and `X-Real-IP` — so no downstream code
can re-interpret raw forwarding values (including in the trusted branch,
where the supported proxy supplies nothing but the canonical pair and only
client-sent noise could remain). Underscore wire-header variants never
reach the application at all: Gunicorn runs `--header-map drop`, which
rejects them at the parser boundary before any normalization.

From an **untrusted peer** the middleware pins `wsgi.url_scheme` to the
real plain-HTTP transport and uses the peer address as the client
identity. A server-derived `https` scheme therefore cannot bypass the
trust list, and a spoofed `X-Forwarded-Proto: https` from a non-listed
peer changes nothing (the request is a 301 to HTTPS instead).

The original socket peer is preserved separately as
`request.remote_peer` (diagnostics and trust checks only); the normalized
one-hop client identity is `request.client_ip`, written back to
`REMOTE_ADDR` so downstream code sees a single canonical value, and it is
the source for the safe `client` field in application request logs (an IP
address, never a credential; there is no diagnostic endpoint that exposes
identities). It is the intended single source for the next limiter
objective.

Ambiguous forwarding from a trusted peer (a chain instead of a single IP,
or a non-`http(s)` proto) falls back to the safe value with a
category-only warning (`proxy-ambiguity`), never raw header content.

**Residual (documented, qualified):** with the app behind the published
loopback port, the Docker bridge gateway is itself a trusted peer, so a
process on the operator host that dials the published port directly is
behind that trusted peer and can present forwarding headers. The
supported contract accepts this residual: the app is non-root,
loopback-published only, and authentication is by credentials, never by
client address. A direct peer from the bridge network that is NOT the
gateway (container-to-container) is untrusted and is handled by the
stripping/redirect contract above (proved by the rehearsal's probe
container, which gets 301, its own bridge IP as the original socket peer
of the rejected request in the Gunicorn access line, and no spoofed value
in any captured log).

### Body-size contract (layered)

- **Edge buffer bound:** `request_buffers 1MB` caps the proxy's in-memory
  request-body buffer. It is a memory bound only, and it must stay strictly
  below the body cap: Caddy's buffer reads only up to its limit, so a
  buffer sized like the cap exhausts the cap's counter during buffering and
  the 413 can never fire while the buffer is filling. A partial buffer is
  not full-body protection.
- **Edge whole-body cap:** `request_body { max_size 10MB }` rejects with
  413 bodies that downstream handlers actually read once the read passes
  the cap (for example multipart file uploads, which the application
  reads fully before responding). In Caddy v2.11.6 `10MB` is the
  **decimal** value 10,000,000 bytes. The cap holds for
  `Transfer-Encoding: chunked` (unknown Content-Length) bodies as well.
- **Application cap (form content types):** urlencoded form bodies whose
  `Content-Length` exceeds Django's `DATA_UPLOAD_MAX_MEMORY_SIZE`
  (2.5 MiB) are rejected with 400 from the application **early** (before
  view logic, well under five seconds in the qualification rehearsal) -
  and the body is **never read**: Django's Content-Length pre-check means
  the edge's read-time cap above cannot fire on form bodies at all.
  (Oversized multipart *memory fields* hit the same application cap once
  read; oversized multipart *file fields* stream to disk and are governed
  by the edge cap instead.)
- **Unread bodies — bounded, NOT rejected:** bodies the application never
  reads (for example `application/octet-stream` to a form endpoint)
  cannot be measured at the edge and are ignored by the application: the
  response is 200 and the edge memory stays bounded by the buffer above.
  This is honestly labeled a bounded-unread outcome, **not** a whole-body
  rejection; the combined effect is bounded memory and responsiveness for
  every oversized-client shape.

### Incoming deadlines

Caddy's **server-level** deadlines are set with the global Caddyfile
option (verified working in v2.11.6; the built-in defaults apply when
omitted):

```caddyfile
{
    servers {
        timeouts {
            read_header 60s       # slow header reads
            read_body 60s         # total body-read deadline
            read_body_idle 30s 1024  # idle bound and minimum bytes/second
            write_idle 30s        # default 60s: stalled response writes
            idle 5m               # default 5m: keep-alive connection life
        }
    }
}
```

`read_body 60s` bounds the total time spent reading a request body, including
a client that continues sending above the minimum rate. `read_body_idle 30s
1024` additionally cuts stalled uploads and enforces an average minimum of
1,024 bytes per second; the second value is a rate, not bytes per timeout
window. Qualification exercises the shipped idle/rate pair and a declared
60s-to-3s total-deadline substitution against an above-rate sender. Healthy
requests remain responsive during and after the cut.

Gunicorn's `--timeout 30` checks worker liveness; it is not a request-read
deadline. Header size is separately bounded by Go's request-header limit;
the oversized-header regression receives 431. The shipped server-level
timeouts provide the incoming request boundary.

The upstream transport timeouts in the example (`dial_timeout`,
`response_header_timeout`, `read_timeout`, `write_timeout`, `keepalive`)
bound the proxy-to-app direction; `keepalive 3s` stays below the app's
Gunicorn `--keep-alive 5` so the proxy discards idle upstream connections
first.

The global JSON log filter removes the `request` object from proxy error
records. Disabling site access logs alone does not protect request headers
or query strings when an upstream connection fails; the regression also
exercises that 502 path with a private-URI canary.

Trusting a Docker bridge gateway also trusts processes on the application
host that can reach its loopback listener. The service host must be under
operator control, without untrusted local tenants. Peer-IP allowlisting
does not authenticate a particular proxy process.

### Headers and HSTS

The example sets `X-Content-Type-Options: nosniff` and removes the
`Server` and `Via` headers (Caddy adds `Via: 1.0 Caddy` to proxied
responses by default; the supported contract exposes no hop identity).
`Referrer-Policy` uses Caddy's **deferred default** (`?` modifier): the
edge policy `strict-origin-when-cross-origin` is applied **only when the
application response does not set its own**. This preserves stricter
per-view policies through the proxy — in particular the one-time token
display page, whose `Referrer-Policy: no-referrer` /
`Cache-Control: no-store, private` / `Pragma: no-cache` contract (SAR-015)
must survive the edge unchanged. An unconditional set here would replace
the application's value (a reproduced, verified defect in the pre-033-b
example); the precedence is asserted end to end on the real token
response in the qualification rehearsal. Django contributes
`X-Frame-Options: DENY` and secure cookies; with
`SLAIF_SECURE_SSL_REDIRECT` enabled the app answers 301 for
plain-transport requests that have not been normalized by a trusted
peer. HSTS remains disabled (`SLAIF_SECURE_HSTS_SECONDS` = 0) until the
final HTTPS hostname, redirects, and subdomain ownership are verified;
enable it only after that, and ramp `SLAIF_SECURE_HSTS_SECONDS`
gradually. Out-of-contract HSTS combinations fail closed at settings
load: a non-zero max-age requires `SLAIF_SECURE_SSL_REDIRECT` enabled,
and `SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS`/`SLAIF_SECURE_HSTS_PRELOAD`
require a non-zero max-age.

The production settings no longer use `SECURE_PROXY_SSL_HEADER`; the
trusted-peer middleware (above) is the only scheme-trust mechanism.
`SLAIF_ALLOWED_HOSTS` entries are validated fail-closed (explicit bare
hostnames, IPv4/IPv6 literals, or Django dotted subdomain wildcards only;
schemes, ports, userinfo, and malformed entries are rejected without
echoing the configured value).

## 9. Logging and monitoring


Minimum implemented application-side posture:

- production JSON logs to stdout/stderr with timestamp, level, logger, message, request path,
  method, status, duration, and request ID where available;
- defensive redaction of Authorization, bearer-token-shaped values, token secrets, verifiers,
  peppers, cookies, CSRF values, passwords, raw request bodies, reservation purposes, and
  cancellation reasons;
- safe route-template request logging: the request logger records the matched route template
  (or an `unmatched-route` marker) plus method/status/duration — never the raw request path,
  so hostile paths and query strings cannot be retained in logs;
- safe exception metadata: unserializable request objects and arbitrary exception locals are
  replaced by category-only markers (`[unserializable]`, exception type, bounded
  file:line stack), never `repr`/`str` of the object graph;
- safe Gunicorn logging: `SlaifGunicornLogger` (wired by
  `--logger-class slaif_reservation.config.gunicorn.SlaifGunicornLogger`) emits JSON with
  method/status/size for access lines and a category plus peer for parser failures — never the
  raw request line, target, headers, or body — and replaces Gunicorn's default error pages
  with a fixed detail so rejected requests are not echoed back to the client;
- proxy access logs off by default: a Caddy 2 site emits no access log unless a `log`
  directive is defined. If an access log is operationally required, configure the JSON logger
  with field exclusions (`request.uri`, `request.headers`, `resp_headers`) and keep it
  reviewed.

Remaining operator monitoring minimum:

- reverse-proxy logs with secrets/queries reviewed;
- health probe;
- service restart monitoring;
- PostgreSQL disk/connection/backup monitoring;
- alerts for sustained 5xx, failed readiness, backup failure, and disk pressure;
- reservation conflict metrics treated as product signal, not necessarily errors.

Prometheus/Grafana integration is optional until an operator requirement is confirmed.

## 10. Scheduled work

Use idempotent management commands for:

- cleanup of expired idempotency records:

  ```bash
  python manage.py purge_expired_idempotency_records
  python manage.py purge_expired_idempotency_records --apply
  ```

  The default mode is dry-run. Scheduling remains operator responsibility;
- notifications/reminders if approved;
- audit/consistency checks;
- export and backup verification helpers.

Every command supports dry-run where mutation risk exists and returns a non-zero exit status on failure. A queue system requires a later ADR.

## 11. Release process

1. approved PRs merged to protected `main`;
2. CI green on release commit;
3. version/tag and release notes;
4. image build from commit and provenance recorded;
5. database backup;
6. migration review and execution;
7. application deployment;
8. readiness and smoke tests;
9. rollback decision window;
10. release result recorded.

Codex may prepare changes and evidence. A human operator authorizes production deployment and release.

## 12. Rollback

Before beta, document:

- application image rollback;
- database compatibility window;
- when migration rollback is unsafe;
- restore-from-backup escalation;
- how to put the service into read-only/maintenance mode;
- how to communicate reservation uncertainty during an incident.

Do not promise automatic rollback until tested.

## 13. Production-readiness gates

Do not label the service production-ready until all are evidenced:

- accepted authentication method and administrator access path;
- TLS and secure settings verification;
- database conflict/concurrency tests;
- token lifecycle and redaction tests;
- backup and isolated restore drill;
- migration and rollback runbook;
- monitoring/alert path;
- privacy/retention decision;
- administrator and incident runbooks;
- migration/cutover plan from SmartScheduling;
- human security and release approval.

## 14. Remaining Production Gaps

The scaffold is intentionally not production-ready. Remaining gaps include:

- accepted production host, DNS, TLS, and reverse-proxy configuration;
- production secret-management integration and operator-managed secret rotation;
- administrator verification of imported asset hardware identity and capabilities;
- no real deployment performed and no live TLS/DNS/certificate issuance;
- no backup scheduler or restore drill against a production copy;
- no production monitoring stack or alert routing;
- no OIDC, email, password reset, or notifications;
- no real SmartScheduling export processed, production import performed, or cutover rehearsed;
- no execution gateway integration;
- reverse-proxy static-asset strategy for production if WhiteNoise is later replaced;
- no projects/resource restrictions or delegated resource-manager roles beyond active staff.

### Shared abuse budgets

The service requires migrated PostgreSQL counter storage for login and API
requests. [Default allowances and configuration](decisions/0016-shared-abuse-controls.md)
coordinate across Gunicorn workers. Review shared-NAT and agent throughput
before adjusting the `SLAIF_LOGIN_*` / `SLAIF_API_*_LIMIT` values in the production
example. A generic429 is temporary; its Retry-After states the remaining window.
503 on protected operations can indicate unavailable/unmigrated counter storage.
Liveness is still independent; check readiness, migrations and database health.

Inspect expired counters with `python manage.py purge_expired_abuse_buckets`.
Add `--apply --batch-size 1000` for bounded deletion. The service also performs
bounded opportunistic cleanup. No periodic operator job is installed.
