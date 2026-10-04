<!-- OAP-META
{
  "id": "031-a",
  "round": "a",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "696b87965920817f1a6b36589562a4af68e75497",
  "issue_number": 61,
  "branch": "codex/61-oap-031-a-gunicorn-idle-connections",
  "pr_mode": "CREATE_OR_RESUME",
  "previous_round": null,
  "pr_number": null,
  "allowed_paths": [
    "Dockerfile (Gunicorn default command only)",
    "compose.yaml (app Gunicorn command only)",
    "compose.production.example.yaml (app Gunicorn command only)",
    "tests/test_gunicorn_responsiveness.py (new durable real-server regression)",
    "tests/test_operational_hardening.py (only existing assertions that pin changed Gunicorn configuration, if necessary)",
    "docs/deployment.md (worker/thread rationale and regression procedure only)",
    "INSTALL.md (Gunicorn concurrency paragraph only)",
    "TESTING.md (Gunicorn regression command/evidence only)",
    "oap/orders/031-a-gunicorn-idle-connections.md",
    "oap/active",
    "oap/reports/031-a-gunicorn-idle-connections.md"
  ],
  "forbidden_resources": [
    "all other application/domain/auth/policy/UI/dependency/migration/inventory/workflow/canonical governance edits",
    "foreign/user dirty or ignored files, existing deployment files, live services or their images/containers/volumes",
    "actual public exposure, host LAN/DNS/TLS/firewall changes, real secrets/private/production data/lab/Neumann probes",
    "merge or auto-merge, force-push/rebase/reset/clean/stash, authentication copying"
  ],
  "requirements": [
    "SAR-022",
    "SAR-024",
    "SAR-025",
    "SAR-031",
    "SAR-032",
    "SAR-033",
    "SAR-035",
    "SAR-038"
  ],
  "decision_class": "D0",
  "target_gate": "M-INTERNET-UX-PILOT development; real exposure remains human D2",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "8483a070026f382bb9b698e9346f3cb33f7dea44f8190b231431585986ebb17d",
    "PLAN.md": "d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06"
  }
}
-->

# 031-a — Reproduce and fix Gunicorn idle-connection starvation

## Goal / provenance

H: current attributable human instruction2026-10-04, selected M-INTERNET-UX-PILOT, requirement8 highest priority, plus request to submit simple bounded coding work immediately to establish live usability. A: S-06/S-12/S-15/S-16/S-19 and SAR IDs above. E: live main696b87965920817f1a6b36589562a4af68e75497, green CI37138528962/OAP37138529032, no open PR before issue61, clean canonical checkout; git branches/worktrees/stash/unpublished refs/ignored filenames/dangling runtime-commit subjects inspected, no foreign threaded fix found locally. No current target product container found in structural local Docker inspection. Current production command sync3 workers; local/image sync2. I: old ICA is historical for old target, not new Internet qualification. C: reproducible runtime/config regression is D0, not CRITICAL.

The human report says another agent fixed LAN timeout with threaded workers. Do not conclude that fix never existed: the bounded local search found none; a deployment on another host was neither probed nor modified. Preserve any foreign change discovered later and report its identity. No reset/clean/stash/overwrites. This first task qualifies/fixes the runtime boundary; Internet abuse controls, default policy, landing/admin/UI/help/theming and fresh ICA are selected next work, not silently waived or claimed complete here.

## Ordered reads

Compact coding read set, exact order, relevant Docker/Compose/rehearsal commands, TESTING.md/runtime safety, relevant existing operational tests and login/health source paths. Consult current official https://gunicorn.org/design/ (already independently fetched by strategy: sync one request per worker/no keepalive, threaded worker pool supports keepalive; buffering proxy remains required). No full strategy/history read.

## Scope and numbered acceptance

1. FIRST independently reproduce the reported failure BEFORE editing tracked configuration. In a disposable source copy with synthetic settings/static assets and a real Gunicorn/Django WSGI server, run old supported sync3-worker configuration. Warm /health/live and /login/ successfully, open at least6 simultaneous TCP idle clients (and a partial-header slow-client variant where needed to prove worker occupation), hold them while separately requesting both endpoints with bounded short timeouts. Record the old failure, close blockers and confirm recovery. No mocked worker or toy replacement application. No existing DB or service needed for anonymous live/login GET; if a DB is needed use owned isolated PG17, never the foreign host5432. Capture safe status/timing evidence, not credentials/cookies/CSRF/full HTML.
2. Only after that negative control, use gthread in all three supported defaults (Dockerfile CMD, localCompose command, productionCompose command). Proposed deliberate baseline:3 workers,8 threads per worker,keepalive5s, preserving the normal30s worker timeout. Rationale:6 slow clients can occupy one worker's thread pool;8 reserves capacity for the health/login requests even under uneven acceptance, total24 request slots with existing3-worker production isolation and bounded DB-connection demand. Verify against actual Gunicorn23 behavior; if this does not pass, diagnose/report rather than blindly raising counts or changing app code. Document scope: this is a responsiveness baseline, not a generic load guarantee or direct-Internet-Gunicorn authorization. Keep binds exactly unchanged: local/production host loopback, DB privateproduction. No new dependencies or infrastructure.
3. Durable tests in new tests/test_gunicorn_responsiveness.py launch REAL installed Gunicorn and actual Django routes, with finite setup/request/cleanup limits and owned subprocess/socket cleanup. Read/assert the effective supported commands so reverting any default to sync is caught; test6 held idle and6 partial-header clients (where stable) and both endpoints return expected200 promptly under configured gthread. Include old sync negative control whose observed timeout is expected by the test, proving regression sensitivity (do not merely monkeypatch a config string). Ensure connections remain held during probes and shutdown cleans up children even after failure. Use unique loopback ports and ephemeral static/config resources, no precious .env/deploy paths, no global signal/container cleanup.
4. Tests run in ordinary existing CI test job automatically; preserve all4 CI jobs plusoap-harness. Run new regression locally with real Gunicorn in a disposable checkout, suitable existing runtime/config tests, lock/lint/format/mypy/diff checks, full current-head standard CI. For thread concurrency preservation rely on actual existing PG17 concurrency/rollback/browser/restore suites in fullCI, not mock DB claims. Build/productionCompose checks validate unchanged UID10001 and exposure topology. If existing tests pin commands, minimally update only their command assertions, never weaken safety gates. No migration or application-domain edit.
5. Docs add a concise worker/thread/keepalive rationale and troubleshooting note, new regression invocation, and retain mandatory proxy/privateDB boundary. Do not remove current unsupported-public warning before later controls are implemented/qualified. README stays product-first and untouched. No old objective/ICA chronology in operator prose.
6. Same issue61/one branch/PR with Closes #61. Observe all5 implementation-head checks SUCCESS before COMPLETE; pending/skipped/cancelled/missing is not pass. No unrelated fix if outside scope. Standard sequence: implementation incl exact order/active -> push/PR -> actualCI -> capture full implementationSHA -> immutable report-only commit firstparentimplementation, publicationSELF, report-headCI unobserved at authoring -> push/remote verification -> responseOK -> EXIT. Publication actions still pending at report authoring must not be described as already successful. Coding never merges.

## Negative paths / strongest objection

A test that only opens sockets without proving old starvation can falsely pass; require real old-sync timeout plus warm/recovery controls. Increasing concurrency can increase DB connections and race pressure; bound to24 slots, retain PostgreSQL final constraints/shared services and run existing real race/rollback suite. Threading does not defeat arbitrary slow-client floods: proxy buffering/read-timeout/rate controls remain a separate selected security objective. Public exposure remains forbidden. A new actual discrepancy routes to strategy; do not silently fix below an unreached boundary.

## Documentation / reporting / recovery

Name exact commands/configs/counts/status and actual measured timings. Report foreign-fix search limits, negative-control results, proposed/final parameters, supported-config identity, real-server test evidence, privacy/cleanup, CI at implementation vs unknown report-head, and limitations. No claims for later requirements or new milestone readiness. Do not sum overlapping suites. A failed in-scope case requires bounded diagnosis; out-of-scope defects get truthful PARTIAL/BLOCKED report. Preserve sameID/branch/PR on interruption, old reports immutable, no force push/reset/stash/clean. Expected report oap/reports/031-a-gunicorn-idle-connections.md. Response FIFO /home/ubuntu/codex-supervision/slaif-asset-reservation/response.fifo; wrapper already consumed control, never wait twice. Existing wrapper uses qualified qwen-neumann profile; no runtime/auth/provider change.

## Deferred human adjudication
- Decision: NONE
