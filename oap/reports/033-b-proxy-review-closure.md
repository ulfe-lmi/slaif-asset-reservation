<!-- OAP-META
{
 "kind": "report",
 "id": "033-b",
 "order_path": "oap/orders/033-b-proxy-review-closure.md",
 "order_sha256": "bfefb75538d21c7657940879c92b1d8c07f5ddeca91370acf2592c29145587c7",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 65,
 "pr_number": 66,
 "branch": "codex/65-oap-033-a-proxy-boundary-hardening",
 "implementation_head": "5eb6205c77f2c91c4c52b77e58651ca634fdfa83",
 "base_sha": "79a1d192aeba2b0a422945aa6a07ed0b0f19e98d",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "5eb6205c77f2c91c4c52b77e58651ca634fdfa83",
  "runs": [
   {
    "run_id": 37224278307,
    "workflow": "CI",
    "jobs": {
     "quality": "success",
     "test": "success",
     "security": "success",
     "container": "success"
    }
   },
   {
    "run_id": 37224278283,
    "workflow": "oap",
    "jobs": {
     "oap-harness": "success"
    }
   }
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 033-b — Proxy review closure

Implementation head SHA: 5eb6205c77f2c91c4c52b77e58651ca634fdfa83
Report publication commit: SELF

Result: COMPLETE for the bounded proxy/privacy/ownership objective.
The attributable human stopped the external coding agent after its unpublished
work and directed STRATEGIC to finish directly. The same branch, PR, active ID
and immutable order were preserved. This is direct implementation and review,
not an independent closure audit. No merge or deployment occurred before this
report. The final milestone still requires shared abuse controls, bootstrap
policy, UX/branding and a fresh independent audit.

## Acceptance

| # | Evidence and outcome |
|---|---|
| 1 | Actual HTTPS one-time token response retains no-referrer, no-store/private and no-cache. Real Caddy generic upstream/default tests detect the old unconditional replacement; Server/Via removed. |
| 2 | Tracked-file snapshots exclude ignored data. Child environments are allowlisted. Containers/networks carry per-run nonce labels; explicit volumes are verified before mounting. Cleanup uses IDs and volume creation identity. Real foreign-container, foreign-volume and creation-race tests preserve the foreign objects. |
| 3 | Owned process groups are terminated even after leader death; injected-failure tests audit remaining processes/resources and preserve a foreign session. Captured diagnostics do not print credentials or full secret-bearing output. |
| 4 | Actual host Caddy TLS -> loopback-published non-root/read-only production app -> private PG17. Gateway/loopback peers explicit, real port-bearing CSRF origin, secure login/cookies, normalized client-IP proof and spoofed/untrusted/underscore cases. |
| 5 | Proxy derives from shipped example; adaptations are narrowly asserted. Shipped total read deadline60s, idle30s/min-rate1024 bytes/s, header/write/idle/upstream/buffer/cap settings. Above-rate total deadline uses an explicit60s-to-3s substitution. Oversized, unknown-length, early-CSRF, stalled/trickle/header/idle paths exercised without calling unread200 a rejection. |
| 6 | Consumed forwarding stripped in both branches; original peer retained. Scoped IPs, host wildcards/malformed labels, invalid origins/ports and unsafe HSTS combinations rejected. Uppercase HTTP origins cannot bypass HTTPS. Real500 through TLS, parser/access logging, unknown routes and proxy502 canaries remain private; global proxy error-log request object removed. |
| 7 | All five exact-head checks SUCCESS. Full CI:765 passed, no skips,400.32s; real PG concurrency/browser/restore, eight responsiveness cases, HTTPS and ownership paths included. Pinned official Caddy checksum and version token verified in existing test job. |
| 8 | INSTALL/deployment/security/testing/example/ADR reconciled to actual behavior. Old033-a report remains immutable; its unsupported COMPLETE interpretation on token header precedence, exact Docker trust path and ownership is superseded by this evidence. |

## Verification and earlier failures

- Final commands in CI: locked install, ruff check/format, mypy, diff check,
  migrate/check/makemigrations, bootstrap import, operational checks, schema
  validation, pytest, pip-audit, both Compose renders, image build/UID/static
  checks and stdlib OAP harness. Runs37224278307 /37224278283, exact head above.
- Focused local work: settings/proxy138 passed; real Gunicorn7 passed;
  rehearsal ownership16 passed; proxy header/error-log regression passed;
  later settings99 passed and error-boundary retry2 passed. Owned PG17 and
  source copies only; foreign host5432 and valuable env files untouched.
- Local full run at f789406:754 passed/2 failed in583.42s. Both failures
  were the same synthetic error probe: URL-safe secret could contain the
  token delimiter and fail parsing before DB access. Canonical hex fixed
  it. That failed run is not called a pass for the final revision.
- Earlier CI setup compared Caddy's complete version/hash string to the
  version alone; comparison now uses its version token, retaining SHA256
  pinning. UTC CI exposed timestamp abbreviation parsing; numeric-offset
  parsing now works independently of local timezone. Earlier setup errors
  from a deliberately disconnected URL were rerun against owned PG17.
- No known vulnerabilities: local and exact-head CI pip-audit. No application
  domain, migration, dependency, inventory or permissions change in this
  objective. Runtime changes are confined to ordered proxy/settings/logging
  and Gunicorn boundary arguments; pool remains3x8/keepalive5/timeout30.

## Limits and strongest objection

A proxy peer IP authenticates a trusted host boundary, not an individual
process: gateway trust also trusts host-local callers. Operators must control
that host. The read cap applies to bodies actually consumed; WSGI can ignore
unknown-length payloads, whose200 is not whole-body rejection. Total deadlines,
buffering and responsiveness remain enforced. These are documented limits,
not evidence of unrestricted Internet/production maturity. Shared login/API
limits and the remaining selected milestone work are not implemented by this
PR. Real exposure, DNS/TLS/firewall, private data and final milestone judgment
remain human D2. Decision: NONE; no CRITICAL admission or disposition.
