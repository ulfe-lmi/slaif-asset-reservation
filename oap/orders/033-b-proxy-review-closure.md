<!-- OAP-META
{
  "id": "033-b",
  "round": "b",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "79a1d192aeba2b0a422945aa6a07ed0b0f19e98d",
  "issue_number": 65,
  "branch": "codex/65-oap-033-a-proxy-boundary-hardening",
  "pr_mode": "AMEND",
  "previous_round": "033-a",
  "pr_number": 66,
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
    "oap/active",
    "tests/browser/test_human_mvp_browser.py (only existing token history/secret/header assertions affected by security changes)",
    "tests/test_api_tokens.py (only positive production fixture required-peer line already reported)",
    "oap/orders/033-b-proxy-review-closure.md",
    "oap/reports/033-b-proxy-review-closure.md"
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

# 033-b — Close exact-head proxy/privacy/ownership review gaps

## Goal and provenance
H: selected human Internet-security requirement and preserved token secrecy/owned disposable qualification. A: A-15/SAR-015/023–026/031/032/039/047 and 033-a criteria1/2/4/6/7. E: actual report1c0f06c86afa8d7629cf5777230c5e784a0e6e36, implementation firstparent3c184b8aaf019500ab4916032c3d8ddc46860124, PR66 identity and report-only verified; all five exact report checks SUCCESS. Full source/diff/rehearsal/tests reviewed. Independent real Caddy2.11.6 probe with the shipped response-header block and an owned loopback backend sending no-referrer showed edge strict-origin-when-cross-origin instead; no-store/private stayed intact and Server absent. No DB, secret, real host or external exposure involved. This contradicts preserved SAR-015 at the proxy boundary. Remaining actual source gaps below need correction. C: D0, no new human product decision or CRITICAL.

## Scope/non-goals
SAME issue65/PR66/branch. Retain all 033-a implementation improvements, threaded3x8/keepalive5/timeout30, private app/DB and immutable order/report. Allowed families remain preceding metadata; corrections only in proxy/header/middleware/config/log/rehearsal/tests/docs and minimum existing CI setup. No shared limiter (034), policy seed, UI design, domain/account/token permissions, dependencies/schema/architecture/governance machinery changes. No real operator env/DB/DNS/ACME/TLS/firewall/roottrust/public exposure, foreign resources, reset/clean/stash/forcepush or coding merge.

## Numbered acceptance
1. Preserve stricter UPSTREAM Referrer-Policy and Cache-Control (especially one-time token no-referrer/no-store/private) through real Caddy. Use appropriate default-only/deferred header semantics, not unconditional replacement. Add actual HTTPS end-to-end assertion on the REAL one-time-token response with secret extracted only in memory and never logged/artifacted; also generic header precedence negative controls. Keep Server removal/nosniff/framing intact. Do not merely assert unchanged Django view headers while proxy weakens them. This is a reproduced in-scope product defect.
2. Repair rehearsal source/resource ownership. Never cp-a the valuable checkout wholesale (ignored.env/secrets/auth/private exports/role data are copied even if not loaded). Snapshot tracked files plus explicit authorized candidate untracked files, with owned temporary Git metadata if needed for ignore fixtures; prove sentinel ignored/private files are absent. Use an explicit minimal synthetic environment for EACH child; do not inherit other SLAIF settings/PG* credentials/client config. Every production/migration/seed/check uses ONLY own DB. Refuse collisions before creation; creation-attempt flags are not proof that only this run can create names. Capture actual container ID and owned labels, create/identify the volume explicitly, and delete only matching owned identity. If another actor creates a name after the initial check, a failed create must leave that foreign resource untouched. No blanket DROP, terminate-other-DB or name-only deletion. Add foreign container AND volume refusal/creation-race/partial-create/failure-cleanup tests with owned stand-ins; untouched sentinel proves guard, not just nonzero exit.
3. Bounded process sessions must be cleaned even if the leader exits first: current kill_session returns on dead leader, skipping surviving children. Track exact owned process-group/session identity, terminate/reap all owned children and audit app/dead-app/Caddy, not only primary Gunicorn bind. Test leader-death and injected failure without leaking test processes or killing foreign/reused identities. Capture secrets/cookies/CSRF only privately; assertions/diagnostic stdout must not print sentinels, raw stderr/full environment or secret-bearing argv. Fix HTTP-test cleanup/log-drain bounds where necessary, do not refactor unrelated fixtures.
4. Qualify the ACTUAL supported operator path: real TLS Caddy host -> Docker loopback-published non-root production application -> private PG17, explicitly discover/configure the actual bridge-gateway /32 peer. The previous native Gunicorn+containerPG rehearsal and direct untrusted bridge smoke do not prove a TRUSTED host proxy through the Docker gateway. Reuse production Compose/image in an owned copy/project with synthetic env/secret files, unique image/ports/volumes and same safety guards. Test real TLS login/cookies/CSRF using the legitimate origin INCLUDING fixture port (not manual portless Origin that masks browser behavior), health/readiness, private docs, error/log/header behavior and trusted/untrusted spoofed XFP/XFF/Forwarded/underscore/hyphen/multiple variants. Validate normalized CLIENT IP itself (test-only probe or later-compatible safe instrumentation), not only HTTP200; no production diagnostic endpoint exposing identities. No real DNS/host changes.
5. Derive qualification proxy configuration from the SHIPPED example, rather than independently reconstructing similar handlers or silently changing required safeguards. Any harness-only certificate/address/admin/ACME/listen/short-deadline substitution must be explicit, narrowly checked against actual adapted shipped config and reported honestly. Actual shipped read_header/body/read-idle/min-rate/write/idle/buffer/cap/upstream settings need evidence. Keep mandatory proxy request buffering/finite body handling defensible: a 1MB buffer is only partial for 10MB admitted bodies. Investigate simple alternatives to avoid holding backend threads for hours of above-min-rate trickling; select finite TOTAL request/body bounds in addition to idle bounds, prove slow/trickle and oversized/unknown-length/early-CSRF cases without accepting a different easier contract. Do not label an ignored oversized request200 as a whole-body rejection. The previous layered observations are retained as experiments, not quietly erased; implement/prove the final supported boundary and document precise limits. No plugin/platform expansion.
6. Enforce the declared forwarding trust contract fully. Strip unused forwarding headers for trusted as well as untrusted peers; preserve original peer separately from canonical client identity for diagnostic/trust checks. Actual one-hop XFF/proto accepts only validated canonical values; malformed/ambiguous client values cannot select another bucket, and trusted underscore/hyphen variants must be rejected/stripped at the public/server boundary before normalization. Validate configured hosts/origins/ports and HSTS combinations according to the supported explicit HTTPS contract: wildcard/malformed/credential/fragment/insecure origin errors must fail safely without echoing raw values. Any retained plain-only rehearsal exception must be explicit outside the supported Internet deployment shape, never a hidden production bypass. No unnecessary Host middleware fix below existing CommonMiddleware validation. Check safe log message/method/exception handling at every actual sink, including corrected authorization-regex escaping, generic malformed methods/headers and unknown error paths.
7. Run meaningful focused real-server/ownership/HTTPS negatives and positives, existing eight responsiveness regressions/full PG concurrency/browser/idempotency/restore/security/build/Compose checks. Required real HTTPS evidence must ACTUALLY run at the final implementation head; no required qualification follows from four CI tests skipped for missing Caddy. Authorize a minimal pinned/verified official Caddy setup in the EXISTING CI test job if that is the cleanest durable path (preserve all four job names +oap-harness, no deployment side effect); otherwise prove complete exact-head owned local execution and honest CI skip limits. No repeated overlapping full tests without a reason. The previous out-of-list tests/test_api_tokens.py ONE positive fixture-peer line is explicitly admitted here; no assertion change or broader file scope. All five exact implementation checks SUCCESS before COMPLETE.
8. Reconcile operator INSTALL/deployment/security/ADR/testing documentation with the final implemented and exercised path/limits; keep product-first wording, precise pending shared-abuse/UX/branding/fresh-ICA gates, no public readiness/production claim. Keep old033-a report immutable, explicitly supersede any unsupported COMPLETE criterion interpretation in the new report. Name actual commands, versions, configs, statuses/failed/skipped/notrun cases, ownership cleanup, prior experiments vs current controls, strongest objection and the source boundaries proved. No audit result as marketing.

## Strongest reason not to merge
Green CI/source presence did not cover token-header precedence through Caddy or the exact Docker proxy-peer path, and cleanup-by-name/copying ignored files leave a valuable-resource boundary weak. Real end-to-end privacy and identity/ownership negative tests must resolve those concrete gaps before development acceptance. This is a correction within the selected target, not a request to reapprove it. No D1/D2 action is authorized.

## Publication/recovery
Same33 objective/PR66, previous33-a frozen. Normal implementation/order/active push -> exact five checks -> literal full implementation head -> immutable report-only firstparent implementation/SELF/report CI unobserved at authoring -> push/actualremoteverify -> notify/exit. Expected report oap/reports/033-b-proxy-review-closure.md. Restore standard qualified long-lived coding launcher at this quiescent checkpoint; previous one-shot recovery wrapper exited after33-a. Dedicated qwen-neumann profile/home/provider remain unchanged. Do not replay accepted031/032 or drop remaining034–039 and fresh architecture-to-current-main all47 ICA.

## Deferred human adjudication
- Decision: NONE
