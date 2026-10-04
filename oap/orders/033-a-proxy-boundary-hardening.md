<!-- OAP-META
{
  "id": "033-a",
  "round": "a",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "79a1d192aeba2b0a422945aa6a07ed0b0f19e98d",
  "issue_number": 65,
  "branch": "codex/65-oap-033-a-proxy-boundary-hardening",
  "pr_mode": "CREATE_OR_RESUME",
  "previous_round": null,
  "pr_number": null,
  "allowed_paths": [
    "src/slaif_reservation/config/env.py (bounded production-security validation only)",
    "src/slaif_reservation/config/settings/*.py (proxy/TLS/header/log settings and middleware order only)",
    "src/slaif_reservation/config/middleware.py (trusted forwarding, safe response headers/log fields only)",
    "src/slaif_reservation/config/logging.py (safe robust production log formatting only)",
    "src/slaif_reservation/config/gunicorn.py (new safe logger/config support only if actual parser privacy experiment requires)",
    "src/slaif_reservation/config/urls.py (private schema/docs authority tightening only; no production crash endpoint)",
    "src/slaif_reservation/config/views.py (only existing health/error safety if an actual failing boundary requires it)",
    "src/slaif_reservation/config/operational.py (read-only proxy-setting diagnostics only if necessary)",
    "Dockerfile (supported Gunicorn forward/header/log arguments only; preserve pool/bind/user/build semantics)",
    "compose.yaml (app Gunicorn forward/header/log arguments only)",
    "compose.production.example.yaml (app forward/header/log arguments, health/config only; preserve network/binds/DB)",
    "deploy/Caddyfile.example (operator proxy trust/timeout/buffering/header contract)",
    "deploy/env.production.example (proxy/security operator configuration)",
    "deploy/rehearse_internal_alpha_deployment.sh (synthetic production contract adaptation only; preserve ownership/refusals)",
    "deploy/rehearse_https_boundary.sh (new owned disposable real HTTPS qualification script if needed)",
    "deploy/https-boundary.override.yaml (qualification-only private/loopback fixture if needed)",
    "src/slaif_reservation/web/templates/web/token_created.html (only minimal security-required inline-JS externalization if CSP requires; preserve secret/history contract)",
    "src/slaif_reservation/web/static/web/token_history.js (only equivalent history-scrubbing security externalization if necessary)",
    "tests/test_proxy_security.py (new meaningful production/proxy/log negative tests)",
    "tests/test_proxy_gunicorn.py (new actual Gunicorn boundary tests)",
    "tests/test_https_boundary.py (new owned HTTPS qualification/ownership tests)",
    "tests/test_settings.py (valid fixture/config and strengthened negative assertions only)",
    "tests/test_operational_hardening.py (affected safety/config/log/rehearsal assertions only)",
    "tests/test_health.py (actual unchanged safe health contract)",
    "tests/test_gunicorn_responsiveness.py (only command parser/pins if extra safe flags require, never weaken oldsync/positive/cleanup)",
    ".github/workflows/ci.yml (only affected existing production container/health assertion; preserve all four jobs/no new deployment)",
    "docs/deployment.md (qualified operator proxy/TLS/privacy contract and procedures)",
    "docs/security-model.md (actual controls and precise remaining qualification limits)",
    "SECURITY.md (corresponding current security contract only)",
    "INSTALL.md (corresponding operator proxy/security setup and troubleshooting only)",
    "TESTING.md (owned real HTTPS/proxy/log regression invocation/evidence only)",
    "docs/decisions/0015-https-proxy-trust-boundary.md (new concise trust-boundary ADR)",
    "oap/orders/033-a-proxy-boundary-hardening.md",
    "oap/active",
    "oap/reports/033-a-proxy-boundary-hardening.md",
    "tests/browser/test_human_mvp_browser.py (only existing token history/secret/header assertions affected by security changes)"
  ],
  "forbidden_resources": [
    "all other domain/account/token authorization/policy/inventory/UI/theming/migration/dependency/architecture/governance machinery changes",
    "valuable existing .env/deploy secrets, foreign work/containers/volumes/images/ports or user data",
    "actual public exposure, host DNS/TLS/ACME/firewall/OS roottrust/real secrets/private production data/lab probes",
    "merge/auto-merge, force-push/rebase/reset/clean/stash, private authentication copying"
  ],
  "requirements": [
    "SAR-011",
    "SAR-013",
    "SAR-015",
    "SAR-016",
    "SAR-017",
    "SAR-022",
    "SAR-023",
    "SAR-024",
    "SAR-025",
    "SAR-026",
    "SAR-027",
    "SAR-031",
    "SAR-032",
    "SAR-035",
    "SAR-038",
    "SAR-039",
    "SAR-047"
  ],
  "decision_class": "D0",
  "target_gate": "M-INTERNET-UX-PILOT development; real exposure remains human D2",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "06dd0f50e778b9843e2a709caa0ae1f0c97f48baee726f4e3a1397cc6a198d8c",
    "PLAN.md": "b19219e2d727af5a9554e011ba45a786f1bb61f25c001011fc18006cae665d08"
  }
}
-->

# 033-a — Harden and qualify the HTTPS/proxy trust boundary

## Goal and provenance
H: selected human requirement 1 makes Internet reachability a security objective. A: SAR-039, SAR-023–026, SAR-031–032 and A-15. E: live main79a1d192aeba2b0a422945aa6a07ed0b0f19e98d is verified merge of PR64, issue63 closed. Its exact reporthead9e4d41374675077b0d0a848abdbe5c3e0abf5366 passed all five checks; fullA15/SAR039-047 and faithful compact projection accepted, previousPR62 delivered thread baseline. Current merged-main CI may be running, no future result claimed. New issue65 selected; no corresponding open PR yet. Independent production-Django-client probes with synthetic in-memory secrets and a dead DB showed: invalid Host correctly returns 400 (CommonMiddleware validates it); untrusted REMOTE_ADDR 198.51.100.25 plus spoofed X-Forwarded-Proto:https returns 200 instead of SSL redirect; DisallowedHost logging includes a non-JSON HttpRequest extra, causing JsonLogFormatter TypeError and a raw Python logging diagnostic dump. The first attempt lacked PYTHONPATH and reached no product boundary; an unpublished Host-200 hypothesis is withdrawn. Do not add an unnecessary Host-validation fix. I: old internal-pilot ICA cannot qualify the new target. C: D0 implementation of selected controls, DHA NONE.

## Scope and non-goals
Only production proxy/TLS/header/error/log trust. Shared login/API abuse control is the next separate objective; do not yet claim Internet readiness. Allowed families: config settings/env/middleware/logging/operational checks; a safe Gunicorn logger/config if real parser-output experiments require it; production Compose/Caddy/env examples and minimal corresponding rehearsal changes; focused security/settings/proxy/log tests; owned disposable HTTPS qualification fixture/script; deployment/security/INSTALL sections and one trust-boundary ADR. Preserve the 3x8 threaded pool, keep-alive5/timeout30, UID10001, binds/private DB, fail-closed secrets and disabled/private schema/docs. No domain/account/token permission/policy/UI/theme/dependency changes except minimal security-required JS externalization or existing assertion adjustments; report an out-of-scope discrepancy rather than expanding. No valuable .env, foreign resources, real host/DNS/ACME/OS-root-trust/firewall/secrets/data/exposure, reset/clean/stash/force-push or merge.

## Numbered acceptance
1. Compare existing operator-owned Caddy with an optional Compose proxy. Prefer the existing operator-owned baseline: no plugin/infrastructure framework unless actual evidence justifies it. Verify current primary Caddy/Gunicorn/Django documentation and actual qualified versions. Validate the real Caddy configuration. A local HTTPS test must use unique loopback ports, synthetic short-lived certificate and explicit per-client/browser trust, without public DNS/ACME or OS trust-store changes. Own every file/container/volume/image/process; cleanup even on failure and refuse foreign resource adoption.
2. Implement explicit validated trusted proxy peer CIDRs/IPs and one-hop normalized client identity. Only that peer may supply TLS/client-IP forwarding; public Caddy overwrites X-Forwarded-Proto and X-Forwarded-For from actual scheme/remote address. Ignore/reject arbitrary untrusted Forwarded/XFF/XFP/XFH, ambiguous chains and underscore/hyphen variants. Do not allow a server-derived wsgi.url_scheme to bypass middleware trust: test REAL Gunicorn, not only RequestFactory. Avoid broad private-network/0.0.0.0/0 trust. Account for host Caddy -> published Docker loopback traffic having a bridge-gateway peer; document exact safe discovery/allowlist and prove the supported operator path. Local/test semantics and DB-independent liveness remain explicit.
3. Production validation rejects unsafe hosts/origins/proxy/security settings and DEBUG, retains distinct nonplaceholder secrets, secure session/CSRF cookies and HTTPS redirect. Reject wildcard/insecure trust for the supported target. HSTS remains validated deliberate opt-in with safe zero default and a documented certificate/domain ramp, not fictional live qualification. Existing INSTALL explicitly requires approved service Host plus127.0.0.1 for the healthcheck; retain that verified contract or deliberately improve the probe's Host, never weaken SSL/trust to pass health. Rehearsal currently sets SSL redirect false: adapt it safely if strict production enforcement changes, and do not silently preserve a bypass for real service deployment.
4. Public proxy bounds header/body read, idle time, body size/buffering and upstream waits. Align finite body cap and request buffer: Caddy request_buffers only reads UP TO its limit, so a partial buffer is not full-body protection. Threads alone do not close stalled header reads; Gunicorn timeout30 is not a per-thread request deadline. Check actual slow/oversized client behavior, normal health/login and private app/DB topology. Response headers resist sniffing/framing/unsafe referrers and avoid server identity; preserve stricter one-time-token no-referrer/no-store/private values. A CSP must be compatible with actual admin/Swagger/token-history behavior, or explicitly stage its needed implementation in the later safe-branding objective; do not break or waive existing protections.
5. Public health exposes only safe ok/unavailable; readiness failures do not dump database/migration details. Docs/schema stay disabled by default and active authorized staff-only when enabled, no accidental anonymous schema. Test unauthorized member/management/private routes and production400/403/404/500 with test-only injected failures (never add a production crash endpoint). No traceback, SQL, secret, request object or private sentinel is browser-visible. Service-account/inactive boundaries must match current authority, not broaden it.
6. Qualify privacy at ACTUAL app, Django error, Gunicorn parser and Caddy log entry points. Never retain raw query, hostile path, credential/cookie/header/password/token/body/private free text. App logs use safe route templates or an unmatched marker, method/status/duration/correlation and safe error category/stack metadata, not arbitrary message/exception locals. Fix the reproduced JsonLogFormatter object-serialization failure without default=str/repr leakage or unbounded recursion. Inspect malformed-header/parser logs below middleware; add the smallest safe Gunicorn logger/config if necessary. Proxy access logs must be off or precisely redacted. Tests use in-memory canaries and safe Boolean/category diagnostics, never print failed sentinels.
7. Real HTTP positive/negative evidence: TLS/cookies/CSRF/redirect/headers; trusted vs untrusted peer forwarding; direct and proxied spoofing including underscore names; allowed/invalid Host+Origin; anonymous privacy/schema; DB-down liveness/readiness; errors and captured logs. Build and render production Compose; verify actual non-root/read-only image, loopback app and non-host-published DB. Preserve and run the eight Gunicorn responsiveness regressions plus existing real PG concurrency/browser/idempotency/restore suites. All five exact implementation checks must succeed. No fake test boundary or unexecuted check counts as a pass.
8. Update precise operator configuration/proxy/TLS/forwarding/privacy troubleshooting and the ADR. Keep normal docs product-first, no OAP ledger and no production claim. Retain a precise Internet-readiness warning until shared abuse controls and final qualification/ICA are completed. New canonical client identity is the SINGLE source for the next limiter, not another raw-XFF interpretation.

## Strongest objection and recovery
Proxy trust can be bypassed by pre-middleware server scheme handling or a mistaken Docker peer allowlist, and rejected requests may leak below Django middleware. Real Gunicorn/proxy/spoof/log tests, explicit one-hop operator assumptions and owned resource checks resolve the selected boundary. Ordinary controls do not claim DDoS immunity. Report materially new/out-of-scope findings to strategy; do not smuggle UI/domain fixes. Normal same-objective order/active/implementation-check/report-only literal SHA first-parent/SELF/remote verification/notify/exit sequence; no rewriting old reports or coding merge. Actual issue/PR/base identities are supplied only at activation.


## Ordered reads, publication and evidence
Read the compact coding law/projection/protocol, this exact order, current production settings/env/logging/middleware, actual Gunicorn23 forwarding/parser sources, Caddy example and safe rehearsal/test entry points. Consult only relevant primary docs. No strategic history read. Newly discovered files needed outside the explicit allowlist require a bounded discrepancy report to STRATEGIC rather than silent scope expansion; similarly named existing tests may be used but do not invent their existence.

Use a disposable source checkout WITH Git metadata for ignore-boundary fixtures, synthetic environment only (do not load a valuable checkout's .env), clear inherited OAP_ROLE for harness tests, owned PG17/ports/images/project resources. Capture statuses/counts/categories only, no raw cookies/CSRF/token/password/canaries or resolved environment in reports/tool output. Required final five implementation-head checks SUCCESS before COMPLETE; pending/missing/skipped/cancelled is not success. New fixture/server tests must preserve finite owned cleanup and real-boundary sensitivity. No extra mirror tests for prose.

Issue65/one branch/PR, Closes #65. Normal immutable publication: implementation incl exact order/active -> push/PR -> actual exact CI -> capture literal full implementation SHA -> immutable report-only commit first parent implementation, publication SELF, report-head CI unknown at authoring -> push/actual remote verification -> response/exit. Report exact trust/header/log decisions, alternatives/rationale/strongest objection, real negative and positive evidence, any not-run/skipped/blocked states, changed paths, preservation/dependency/privacy/ownership facts and precise remaining shared-abuse/UX/fresh-ICA gates. Expected report oap/reports/033-a-proxy-boundary-hardening.md. No coding merge or automatic deployment. Dedicated qualified profile unchanged.

## Deferred human adjudication
- Decision: NONE
