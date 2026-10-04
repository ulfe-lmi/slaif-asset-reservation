# ADR 0015: HTTPS/proxy trust boundary (trusted peer, body bounds, safe logs)

**Status:** accepted
**Date:** 2026-10-04

## Context

Internet reachability is a security objective, but live probing of the
pre-change production stack showed the proxy trust boundary was implicit:
an untrusted remote address spoofing `X-Forwarded-Proto: https` could
change application behavior, and rejected requests below Django
middleware (Gunicorn parser failures) could echo or log raw input. The
deployment shape (operator-owned Caddy in front of a loopback-only
Gunicorn/Django container) already existed; this decision fixes how trust,
request bounds, and log privacy are expressed at that boundary, qualified
against the actual pinned toolchain.

## Decision

1. **One-hop trusted-peer forwarding.** The application honors
   `X-Forwarded-Proto` and single-value `X-Forwarded-For` only from the
   peers in `SLAIF_TRUSTED_PROXY_PEERS` (required in production; entries
   must be explicit IPs or point-to-point networks — `/31` IPv4, `/127`
   IPv6 — so a broad range can never become an impersonation lane). Every
   other peer is a direct client: all forwarding headers are stripped,
   `wsgi.url_scheme` is pinned to the real transport, and the peer address
   is the client identity (`request.client_ip`, the single source for any
   future limiter). The proxy must overwrite, never append, both headers
   from the actual connection; the example pins Caddy **v2.11.6** with
   `header_up X-Forwarded-Proto {scheme}` / `header_up X-Forwarded-For
   {remote_host}`. A server-derived `wsgi.url_scheme` can no longer bypass
   the trust list; Gunicorn additionally runs
   `--forwarded-allow-ips 127.0.0.1,::1 --header-map drop` so underscore
   wire-header variants never reach the application. `SECURE_PROXY_SSL_HEADER`
   is no longer used in production settings.
2. **Layered body-size contract.** `request_buffers 1MB` (memory bound
   only, kept strictly below the cap) + `request_body { max_size 10MB }`
   (413 for bodies a downstream handler actually reads, e.g. multipart
   uploads) + Django `DATA_UPLOAD_MAX_MEMORY_SIZE` 2.5 MiB (400, checked
   before the form body is read); bodies the application never reads are
   bounded by the buffer and ignored. A buffer sized like the cap cannot
   protect: Caddy's buffer reads up to its limit and exhausts the cap
   counter while filling (Finding A below).
3. **Server-level incoming deadlines.** Caddy global `servers { timeouts
   { … } }` (read_header, read_body_idle with min rate, write_idle, idle)
   bounds slow/stalled clients; Gunicorn `--timeout 30` remains a
   worker-liveness timeout, not a per-request deadline (Finding B below).
4. **Safe logs and error responses below Django.** `SlaifGunicornLogger`
   (wired by `--logger-class`) replaces Gunicorn's formatters with JSON
   access/error records (method/status/size; category plus peer for
   parser failures) and its raw error pages with a fixed detail, so
   malformed requests are never echoed back or retained raw. Application
   request logs use the matched route template (or `unmatched-route`),
   never the raw path; unserializable request/exception state is replaced
   by category-only markers. Proxy access logs stay off unless configured
   with field exclusions.
5. **Qualified, owned evidence.** `deploy/rehearse_https_boundary.sh`
   builds an owned, disposable, loopback-only real TLS edge (fresh source
   copy, uniquely named PG17 container/volume, kernel-assigned ports,
   1-day synthetic certificate trusted only by the test clients) and
   exercises the boundary end to end; no public DNS/ACME, no OS
   trust-store changes, no inherited configuration, foreign resources
   refused rather than adopted.

## Findings driving the design (Caddy v2.11.6, verified empirically)

- **Finding A — buffer/cap alignment.** With `request_buffers` equal to
  `request_body max_size`, the buffered read consumes the cap during
  buffering, so an oversized body a downstream handler never reads (e.g.
  `application/octet-stream` to a form endpoint) passed as 200. The
  buffer is therefore a strictly-lower memory bound, and full-body
  rejection for form types is delegated to the application's
  Content-Length pre-check.
- **Finding B — route-level `timeouts` ineffective.** A route-level
  `timeouts { read_timeout … }` did not cut a stalled request-body read in
  v2.11.6, while the identical server-level `read_body_idle` deadline did
  (HTTP 499 at the bound). The supported contract uses the server-level
  form; revisit if a future Caddy release fixes the route form.

## Revision 2 (OAP 033-b) — corrected defects, retained findings

The 033-a round's independent real-Caddy probe exposed that the shipped
response-header block **replaced** the one-time token page's
`Referrer-Policy: no-referrer` with the edge default (an unconditional
`set` semantics), contradicting the preserved token-secrecy contract at
the proxy boundary. Findings A and B above remain valid history; the
decisions they drove are unchanged. This revision records the corrected
contract, qualified again end to end against Caddy v2.11.6:

1. **Deferred edge header defaults.** The edge `Referrer-Policy` default
   uses Caddy's `?` (apply-only-when-absent) semantics, so stricter
   per-view policies - in particular the token page's `no-referrer` and
   `no-store, private` - survive the proxy unchanged (asserted against
   the REAL token response, secret handled in memory only). Caddy's
   default `Via: 1.0 Caddy` hop header is removed (`-Via`); `Server`
   removal and nosniff are retained. (The 033-a report's interpretation
   of criterion 1 as COMPLETE on header preservation is superseded by
   this correction; the 033-a report itself is immutable.)
2. **Total forwarding stripping in BOTH branches.** A trusted peer's
   request also carries every forwarding header (`Forwarded`,
   `X-Forwarded-Host/-Port/-Prefix`, scheme variants, `X-Real-IP`)
   consumed once and stripped - previously only the untrusted branch
   stripped - and the original socket peer is preserved as
   `request.remote_peer`, separately from the normalized
   `request.client_ip` (the safe request-log `client` field and the
   intended limiter source).
3. **Total and idle body bounds.** `read_body 60s` bounds total request
   consumption, including an above-rate sender. `read_body_idle 30s 1024`
   bounds stalls and enforces a 1,024-byte/second average minimum. The
   previous draft misinterpreted the minimum-rate unit; its transfer-time
   calculations do not describe the implemented contract. The rehearsal
   exercises the shipped idle/rate values and an explicitly shortened
   total deadline. Oversized request headers receive 431.
4. **Qualified actual operator path.** The rehearsal now exercises the
   supported shape end to end: host TLS Caddy (pinned, loopback-only,
   admin/ACME off) -> Docker loopback-published non-root production
   image -> private PG17, with the bridge gateway explicitly discovered
   and configured as the `/32` trusted peer (one of the two possible
   original peers behind the published port, depending on host NAT mode
   - loopback or bridge gateway; both are trusted), the CSRF origin
   including the
   fixture port, and the configuration DERIVED from the shipped example
   with narrow, asserted substitutions.
5. **Fail-closed configuration.** `ALLOWED_HOSTS` entries must be bare
   explicit hostnames/IP literals (scheme, port, userinfo
   and malformed entries fail closed without echoing the raw value), and
   out-of-contract HSTS combinations (non-zero max-age without the SSL
   redirect; subdomain/preload with zero max-age) are rejected at
   settings load.

## Consequences

- Operators must allowlist the exact proxy peer they see (loopback for a
  host-side proxy; the Docker bridge gateway for a proxy on the app
  network) — documented with discovery commands; the in-container
  healthcheck keeps its `127.0.0.1` contract via the same list.
- HSTS stays a validated, explicit opt-in (zero default) with a
  certificate/domain ramp; response headers add
  `Referrer-Policy: strict-origin-when-cross-origin`, nosniff, and no
  `Server` identity.
- Shared login/API abuse controls, UI/branding, HSTS ramp completion, and
  the final Internet-exposure ICA remain separate, later gates; this
  decision does not claim Internet readiness.
