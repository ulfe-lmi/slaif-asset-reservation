<!-- OAP-META
{
  "id": "029-a",
  "round": "a",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "state": "FINAL",
  "base_sha": "f406c612f52f64a50f0a145b27a7f580838c7287",
  "issue_number": 57,
  "branch": "codex/57-oap-029-a-product-documentation",
  "pr_mode": "CREATE_OR_RESUME",
  "previous_round": null,
  "pr_number": null,
  "allowed_paths": [
    "README.md",
    "QUICKSTART.md",
    "INSTALL.md",
    "CONTRIBUTING.md",
    "docs/README.md",
    "docs/oap-workflow.md (status paragraph and closing-keyword/post-merge issue lifecycle sentences only)",
    "oap/orders/029-a-product-documentation.md",
    "oap/active",
    "oap/reports/029-a-product-documentation.md"
  ],
  "forbidden_resources": [
    "application/source/migrations/tests/dependencies/lockfile/Dockerfile/Compose/settings/workflow/inventory changes",
    "canonical PLAN/ARCHITECTURE/CRITICAL and immutable prior audit/order/report/history changes",
    "real deployment/secrets/private data/SmartScheduling/lab/Neumann/DNS/TLS/firewall/public exposure",
    "other issues, unrelated branches, merge/auto-merge/protection changes",
    "auth copying or raw credential/user data in output"
  ],
  "decision_class": "D0",
  "requirements": [
    "SAR-002",
    "SAR-016",
    "SAR-022",
    "SAR-023",
    "SAR-024",
    "SAR-025",
    "SAR-027",
    "SAR-031",
    "SAR-032",
    "SAR-033",
    "SAR-036",
    "SAR-037",
    "SAR-038"
  ],
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "8483a070026f382bb9b698e9346f3cb33f7dea44f8190b231431585986ebb17d",
    "PLAN.md": "d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06"
  }
}
-->

# 029-a — Product-first documentation and repository hygiene

## Goal

Make the repository explain and run the existing asset-reservation product for researchers, operators, developers and agent/API clients. One bounded documentation objective; no feature or runtime change. FINAL after strategic reconciliation on 2026-10-03.

## Provenance

- H: attributable current in-session human instruction 2026-10-03, HUMAN OBJECTIVE, REQUIRED DELIVERABLES 1–6, DOCUMENTATION TRUTH RULES, VERIFICATION REQUIREMENTS and DEPLOYMENT-GATE / ICA CONSEQUENCE. Human explicitly selects and authorizes the normal coding/review/development-merge loop for this cleanup; all D2 boundaries retained.
- A: PLAN P-01/P-03/P-04; ARCHITECTURE A-01/A-07/A-08/A-10 and SAR IDs in metadata; S-12/S-16/S-19/S-22/S-24.
- E: live private main f406c612f52f64a50f0a145b27a7f580838c7287, parent a9c3133d3da36c34bd66ff4dba264d0b10bae9e0; clean main, absent active pointer, no open PR before this objective; CI 35664329877 successful, 4 jobs. The nine supplied stale issues are already closed/completed with factual comments on 2026-10-03; do not add duplicate comments. Current README leads with OAP chronology; INSTALL has foreground app startup in its quickstart; CONTRIBUTING still claims no application exists. Root QUICKSTART absent.
- I: existing ICA report docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-a9c3133.md is exact-revision evidence, not marketing or automatic coverage of edited deployment instructions. Strategy owns post-merge freshness assessment under docs/audit/ICA-PROTOCOL.md; coding does not audit or declare milestone closure.
- C: CRITICAL has no live entries; this is D0 editorial/verification work within explicit human scope, no consequential provisional product choice.

## Ordered read set

Read the standard compact coding set, then the five target documents (QUICKSTART is new), TESTING.md, relevant deployment/security/human/API/runbooks and implementation/configuration needed to verify claims. Inspect current docs in ulfe-lmi/slaif-local-coding: README.md, QUICKSTART.md, INSTALL.md, docs/README.md, CONTRIBUTING.md (reference main observed f3793af9e5f05bdfba19ef800eeaf57177d0ed2b; retrieve through gh). Copy information architecture and presentation only, never its model server/Gateway/registry/release-artifact assumptions. Verified SLAIF logo URL https://www.slaif.si/assets/slaif-logo.svg returns SVG HTTP 200; optional branding may use it. Source facts must win over old prose.

## Scope

1. README becomes a concise product landing page. Order: product purpose/value; prominent Get started links to QUICKSTART and INSTALL; how it works (small diagram welcome); compact human/agent/staff capabilities; supported runtime; task documentation; concise important limits; developers; license. Optional honest CI/Python/license badges; verify actual Apache-2.0 license and locked stack. No readiness/release certification badges. New reader finds product/start/install before governance. OAP only near bottom specialist pointer. Preserve substantive historical evidence in existing history, never rewrite immutable records.
2. New QUICKSTART is the shortest real Docker LOCAL EVALUATION path (roughly 5–10 minutes with prerequisites/cache/network caveat). Explicit prerequisites incl. Docker/Compose, Linux amd64, Git/private repo access, required available ports. Clone actual repository; use a distinct evaluation Compose project consistently to avoid normal project collision; committed development compose is loopback-only, development settings/secrets, DB 5432 and app 8000. Start detached so following commands execute; deliberate migrations; optional bootstrap import with actual syntax; interactive createsuperuser; login, health/live and health/ready; explain policies must be configured before booking and sanitized inventory is not verified hardware. No fake seed policy or account. Teardown defaults data-preserving; place VERY visible destructive warning immediately before optional down -v. Do not promise pilot readiness on an empty evaluation DB. Explain conflicts without stopping foreign services. No product/Compose edit to accommodate host conflicts.
3. INSTALL is full controlled internal-alpha operator guide: supported single amd64 Linux host, Docker build from reviewed revision (no registry), proxy -> 127.0.0.1 app -> private PG17; non-root/read-only runtime; prerequisites/security gates; source; protected real environment/DB secret file (matching password, correct permissions, no printed secrets); build/tag identity; quiet safe Compose validation (avoid printing secrets from config); DB healthy; deliberate migrations/operational_check; optional verified asset import; administrator; app; policies; Caddy/HTTPS; health/readiness/pilot readiness at appropriate prepared-data stage; persistence; backup/off-host/restore; routine lifecycle; upgrades; compatible app rollback vs DB restore; uninstall/data warning; troubleshooting; developer pointer; limitations. Preserve operational depth without development/history narrative. Cross-check every command/path/env/URL. Production healthcheck uses 127.0.0.1 and X-Forwarded-Proto=https: check ALLOWED_HOSTS implications, do not weaken settings or modify config. Do not claim PG client tools are in app image (they are not); Compose-native backup/restore vs host wrappers must stay clear. Document privileged shared PG migration/runtime role as existing operational limitation. Rehearsal is disposable synthetic proof, not a real deployment; opt-in deployment-rehearsal.yml exists separately from four standard jobs.
4. docs/README becomes task-oriented linked navigation: Start here; Users/API clients; Operators; Developers; Governance/history last. Links use actual files/anchors. Historical STATUS/handoff/bootstrap stay labeled history. Canonical architecture is root ARCHITECTURE.md; docs/architecture.md is compatibility pointer. API contract describes implemented API (do not call it merely intended).
5. CONTRIBUTING becomes concise actual developer path: Python3.13/uv/locked deps/local PG17; explicit .env handling; tests/lint/type/schema pointers and commands; disposable test copy warning; privacy/security; scoped PRs and evidence; agent workflow pointer. No governance textbook; fix stale pre-adoption/pre-implementation claims. PRs should use Closes #<issue> when they fully satisfy that objective, preserve incomplete issues. Existing PR template already says Closes #; reinforce use and strategic post-merge verification with a minimal sentence in docs/oap-workflow.md. Also replace only that file's stale inactive-candidate status paragraph with accurate adopted operation status; do not expand/change OAP machinery or authority.

## Non-goals and truth constraints

No runtime/config/test/dependency/inventory/architecture/plan/audit edits. Do not silently fix source defects. Report exact discrepancy to strategy and continue independent documentation work; a runtime repair would require a separate strategic decision/order.

Current limits must remain clear without a giant README ledger: trusted internal pilot only; not unrestricted public Internet; broad authenticated-human reservable-asset access, no project/group membership auth; no app login/API rate limiting; shared privileged PG role; scheduled/off-host backup is operator-owned; no OIDC/password-reset/email; notifications/workload execution/gateway/scheduler/monitoring are outside current core; real/private legacy migration is separate. No private exports committed. Assets list/detail API is staff-session-only: do not advertise bearer asset discovery. Service accounts cannot human-login. Reservations are entitlements, not enforcement on physical machines.

## Numbered acceptance

1. All five product/developer entry docs meet the scope above, with actual supported commands, clear boundaries and professional concise tone.
2. Raw/rendered first ~100 README lines explain product/capabilities/start/install before OAP or history. No normal README/QUICKSTART/INSTALL narrative contains WO ranges, objective ranges, old SHAs, audit counts, PR chronology, conversion/handoff prose. Search and report any justified exception.
3. Execute QUICKSTART on an owned disposable checkout/resources, against real PG17 and HTTP. Confirm migrations, optional import syntax/dry-run/apply, createsuperuser interactive path or explicit equivalent documented as test adaptation, administrator login, both health endpoints, data-preserving stop/down and destructive teardown semantics. Record exact commands and adaptations, not only a prose review. This host already has a foreign service at 127.0.0.1:5432; NEVER stop it. Use isolated network or temporary uncommitted test-only port override if needed, and disclose it. Do not alter checked-in compose. Check uniqueness before resources; cleanup only exact owned project/volume/image. No secrets in logs.
4. Cross-check every INSTALL command against source/help; production Compose renders, env/Caddy files exist, actual port topology/health settings/operational and backup restore commands match. Execute full existing production-shaped rehearsal in a disposable clean copy with unique project/port/image; inspect script safety first. Do not run destructive operational tests in the valuable checkout. Real TLS/exposure/backup on live data remain NOT RUN. Identify any changed normative deployment instruction explicitly for strategy's freshness assessment.
5. All changed Markdown links (including anchors and external branding where added) validated; no dangling paths. Check inbound links to changed headings in current docs and preserve useful anchors if necessary rather than expanding scope. First-glance and ledger regressions checked.
6. Product/runtime/dependency/workflow/test/inventory bytes identical to base; exact allowed-path diff and history preservation. Run git diff --check and appropriate standard checks. Required CI at exact implementation head: quality/test/security/container plus oap-harness; all must succeed before COMPLETE report. If a pre-existing failure occurs, diagnose first boundary, do not alter forbidden files or waive failures; tell strategy. No ceremonial new tests for prose.
7. One issue #57 / one PR, body includes Closes #57 and actual scope/evidence/limitations. Report identifies changed paths, all verification results including failures/adaptations, strongest unresolved limitation and explicit zero runtime-source changes. Separate implementation CI from report CI not yet observed.

## Verification / Negative paths

Use actual source at base for claim map, local disposables for documentation commands, remote CI for full standard regression. Inspect readonly CLI --help where executing real operational changes is forbidden. Check no collision adoption, no real env overwrite, no destructive down -v against foreign projects, no secret-bearing config/stdout, fail-closed deployment errors preserved, missing policy still fails closed, no fake full-path pass when a step is blocked.

## Documentation and reporting

Evidence belongs in the immutable OAP report, not first-glance product prose. Do not append a new audit report or claim ICA closure. Strategy will assess post-merge exact-head freshness. Document operator-facing limitations without repetitive defensive/self-referential language. Avoid copied reference-product content.

Use C-11/C-12 exact sequence: implementation commit/push incl. order/active -> actual PR -> required implementation-head CI -> capture literal full implementation head -> immutable report-only commit with that head as first parent and Report publication commit: SELF -> push and verify remote -> response OK -> exit. No further mutation after report publication. Report path oap/reports/029-a-product-documentation.md.

## Recovery

Verify base main and remote before first edit. Reuse same branch/PR on interruption, preserve all foreign changes, no reset/clean/stash/force push. Do not replay a published report. Notify strategy promptly if runtime verification exposes a defect or mandatory checks fail outside scope.

## Deferred human adjudication
- Decision: NONE
