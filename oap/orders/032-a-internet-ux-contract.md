<!-- OAP-META
{
  "id": "032-a",
  "round": "a",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "3abe17d026d7ebfe402426afd89e30cdc6924f61",
  "issue_number": 63,
  "branch": "codex/63-oap-032-a-internet-ux-contract",
  "pr_mode": "CREATE_OR_RESUME",
  "previous_round": null,
  "pr_number": null,
  "allowed_paths": [
    "ARCHITECTURE.md (selected target contract, appended stable requirements, historical observation labels only)",
    "PLAN.md (current selected milestone and historical epoch labels only)",
    "ARCHITECTURE-for-agents.md (faithful current full-source projection/hash)",
    "docs/governance/INTERNET-UX-PROJECTION-REVIEW.md (new semantic coverage and measured context record)",
    "docs/audit/ICA-PROTOCOL.md (derive current canonical requirement scope; retain full fresh audit protocol)",
    "docs/audit/ICA-REQUIREMENT-MATRIX-TEMPLATE.md (historical initial seed label/current-scope pointer only, preserve existing rows)",
    "oap/orders/032-a-internet-ux-contract.md",
    "oap/active",
    "oap/reports/032-a-internet-ux-contract.md"
  ],
  "forbidden_resources": [
    "all product/source/runtime/config/test/dependency/migration/inventory changes",
    "all immutable historical reports/orders/bootstrap archives/digests/maps/manifests and installed role-law files",
    "real production/lab/private data/secrets/DNS/TLS/firewall/public exposure",
    "foreign/ignored files, valuable deployment resources, reset/clean/stash/forcepush, merge or auto-merge"
  ],
  "requirements": [
    "SAR-001",
    "SAR-002",
    "SAR-003",
    "SAR-004",
    "SAR-005",
    "SAR-006",
    "SAR-007",
    "SAR-008",
    "SAR-009",
    "SAR-010",
    "SAR-011",
    "SAR-012",
    "SAR-013",
    "SAR-014",
    "SAR-015",
    "SAR-016",
    "SAR-017",
    "SAR-018",
    "SAR-019",
    "SAR-020",
    "SAR-021",
    "SAR-022",
    "SAR-023",
    "SAR-024",
    "SAR-025",
    "SAR-026",
    "SAR-027",
    "SAR-028",
    "SAR-029",
    "SAR-030",
    "SAR-031",
    "SAR-032",
    "SAR-033",
    "SAR-034",
    "SAR-035",
    "SAR-036",
    "SAR-037",
    "SAR-038",
    "SAR-039",
    "SAR-040",
    "SAR-041",
    "SAR-042",
    "SAR-043",
    "SAR-044",
    "SAR-045",
    "SAR-046",
    "SAR-047"
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

# 032-a — Record selected Internet/UX contract and executor projection

## Goal / provenance
H: attributable human2026-10-04 explicitly selects all eight Internet/UX requirements and authorizes bounded development, disposable qualification, strategic merge, fresh ICA; real deployment remains D2. A: S-05/S-12/S-20/S-23 and SAR-001..038 preserved. E: live main3abe17d026d7ebfe402426afd89e30cdc6924f61 is verified merge of PR62, issue61 closed, reporthead065cf891c2cf353114928eba6c4e2bdf7612d361 allfivechecks SUCCESS, root independent eightGunicorn regressions passed48.56s. Currentmerged-main CI may still be running; no main CI success claimed atactivation. Issue63 newly selected, no corresponding openPR yet. I: existing internal/trusted-pilot ICA is historical for its target. C: capture selected meaning, not new D1 risk acceptance; DHA NONE.

## Scope
Canonical architecture/PLAN and compact architecture projection only, a small current projection coverage record, ICA protocol/matrix reference maintenance if it assumes exactly38 rows. No app/runtime/test/dependency/migration/governance machinery/law/archived snapshot changes. Do not copy or rewrite historical audit reports, initial matrices, bootstrap maps/manifests/digests. No blanket expected-hash updates to make checks green. The full canonical contract below is authored by strategy; coder applies it first, THEN compiles executor projection, mapping every must/condition/exclusion/evidence facet. No private parallel canonical plan/architecture.

## Canonical architecture changes ordered
1. Root header must distinguish original conversion observations (2026-09 baseline) from current selected target (2026-10-04). Preserve archived accepted sources. Existing A01..A14 and SAR001..038 stable, no weakening or silent replacement. Historical UNPROVEN rows and baseline observations must be identified as point-in-time, not current audit results. Source constraints current DRF3.17; lock authoritative. Old no-policy-seed assertion becomes historical baseline observation with pointer to SAR041 target. Old nonexistent-restore-drill/baseline-diagnostic proof-gap claims labeled historical, current evidence belongs exact reports/tests/audits; do not invent fresh results. Architecture can state chosen gthread baseline as observed only because predecessor merge verified. Do not claim controls below implemented.
2. Add A-15 Selected Internet/UX target, with exact substantive contract:

M-INTERNET-UX-PILOT is selected human product meaning as of2026-10-04. SLAIF Asset Reservation must support an Internet-reachable authenticated service through a normal HTTPS endpoint, and a friendly SLAIF browser experience. Accounts remain administrator-created; no anonymous self-registration or private inventory/reservation disclosure. Public landing is the only selected new anonymous product surface. Broad authenticated-human reservation access under current policies remains an explicit authorization limitation; projects/groups/memberships remain deferred. Internet reachability does not imply anonymous access or unrestricted production maturity. All prior reservation/domain/auth/privacy/CSRF/idempotency/audit/protected-admin/PostgreSQL/recovery guarantees continue to apply.

The qualified target topology is public HTTPS reverse proxy/TLS termination -> loopback/private non-root Gunicorn -> private PostgreSQL17, on Linux amd64/x86_64. Gunicorn and PostgreSQL must not be directly published to the Internet. Operator-owned Caddy or equivalent remains the simple baseline unless bounded investigation selects a simpler safe optional proxy configuration. Trust only explicitly configured proxy peers; reject/ignore attacker-supplied forwarding outside that boundary, define client IP and TLS-header normalization precisely. Allowed hosts and CSRF trusted origins are explicit; production debug off, secure session/CSRF cookies and SSL redirect enforced. HSTS remains a documented deliberate opt-in strategy (no fictional live certificate/domain qualification). Production errors and response headers must avoid framework traceback/secret leakage. API docs/schema remain disabled by default and staff-only when enabled. Health must expose only safe liveness/readiness state. Logs exclude raw credentials, private payload/free text and sensitive query material. Fail-closed secrets and private DB/network persist. Administration is protected by the same HTTPS/authentication/abuse assumptions; any extra operator IP restrictions must be configurable and documented rather than assuming a trusted LAN.

Abuse protection must bound remote authentication attempts on ordinary AND administration login and bound unauthenticated/invalid-bearer and authenticated API traffic without arbitrarily tiny limits for legitimate agents. Limits must coordinate across Gunicorn workers/processes; per-process in-memory multiplication is insufficient. Choose and document reasonable configurable rates, trusted-client identity, expiry/cleanup and failure behavior. No permanent attacker-triggered account lockout. Preserve stable machine-readable API errors, owner privacy, CSRF and idempotency. Multi-process and negative-path HTTP tests must prove effective controls; proxy read/idle/body bounds remain necessary because threads do not prevent arbitrary slow-client floods.

A supported fresh initialization path automatically creates an effective active global fallback reservation policy named default: asset NULL, booking horizon7days measured by reservation START, maximum duration2880minutes/48hours/2days, no restricted operating-hour window, minimum lead0, cancellation cutoff0, purpose optional. Required unspecified fields use simple explicit minimally surprising defaults consistent with existing constraints; strategy sets actual values in the initialization objective after semantic inspection. Upcoming/concurrent limits must be visible and documented. Initialization must be idempotent and atomic, fresh assets reservable subject to policy, existing operator policies (including deliberate inactive configuration) preserved, upgrades predictable, no duplicate active-global policy or silent overwrite. It may use a migration, safe initializer or bootstrap path; requiring manual policy creation in normal fresh install is disallowed. Tests prove fresh initialization, repetition, configured-upgrade preservation and real booking.

Anonymous / is a polished public landing with product identity, concise purpose, obvious Login AND Administration actions, appropriate locally packaged SLAIF branding, no asset/user/reservation data. Administration action enters administration login. Authenticated members can reach dashboard, staff management and permitted administrators administration without redirect loops. Member/admin login excludes invalid/inactive/service-account identities under current authority rules. Product browser titles, headings, breadcrumbs, admin login/index/header, footer and errors use SLAIF Asset Reservation or SLAIF-branded Administration, never Django/default framework branding. Customize administration identity structurally, not CSS hiding. Technical docs/imports/dependency names may say Django. Protected/read-only admin models remain protected and explain their service-backed mutation route.

Audit every member, staff and admin editable field plus non-obvious choices and raw filters. Useful labels and nearby rendered help explain units/effects, horizon START semantics, lead/cutoff, global/specific resolution, optional purpose, DST occurrence-only relevance, token scopes in human language, destructive/high-impact actions and protected admin editing. Help is accessible through labels/aria-describedby or equivalent form associations. Do not clutter obvious fields or weaken validation. Humanize policy duration display without changing storage units and retain machine scope values/permissions.

Default appearance follows CURRENT SLAIF references slaif.si/doc.slaif.si/edu.slaif.si/trainings, inspected with Playwright screenshots. Build coherent typography/color/spacing/nav/cards/buttons/forms/tables/status/footer using CSS tokens, local official assets where organizationally appropriate and licensed. Do not hotlink runtime-critical assets or copy unrelated site HTML/framework. Operator appearance customization needs no source fork or application image rebuild: bounded read-only branding directory/configuration, primary/compact logo where useful, favicon/browser identity where practical, selected images and CSS loaded AFTER defaults. Self-contained defaults and safe fallback; no server-side template execution, remote JS mechanism, arbitrary file exposure or unsafe mount adoption. Define MIME/path/symlink/size/failure boundaries and document them. Default and custom fixture must be Playwright tested.

Gunicorn uses a deliberate threaded pool consistently in image/local/production/rehearsal where relevant. Preserve foreign fix if found; otherwise independently reproduce old sync starvation BEFORE changing configuration. Real-server tests hold at least six idle/slow clients while /health/live and user login respond within bounded time; old sync negative control must fail or equivalent mechanism prove original sensitivity. Owned child/socket cleanup even on failure, unique resources, no foreign service. Worker/thread/keepalive rationale and bounded capacity documented, mandatory buffering/time-limited HTTPS proxy retained.

Qualification uses real unit/integration, PostgreSQL concurrency/rollback, browser authentication/CSRF/privacy, Gunicorn six-client negative/positive regression, disposable Internet-shaped HTTPS proxy, shared login/API abuse controls, production-settings negatives, container/config/health, fresh+upgrade policy initialization, default/custom branding. Real Playwright development capture/view/iterate is mandatory, not merely200 or testpass. Representative meaningful fixtures cover anonymous landing/login/admin login; member dashboard/assets/detail/availability/create/reservation list+detail/profile/token list+create; management dashboard/policy list+detail+form/blackout list+detail+form/reservations/audit list+detail+export controls; administration index/user list+change/asset list+change/relevant models. Review approximately1440,1024,768,390 widths, desktop/mobile default/custom. Durable semantic assertions cover overflow, primary actions/navigation/focus/labels/associated help/responsive tables/forms, no framework visible text, no anonymous private leak. No brittle pixel snapshots unless stability proven. Privacy-safe screenshots exclude one-time secrets/password verifiers/cookies/CSRF/raw traces/private data. Strategy actually visually inspects screenshots and orders iterations when poor; attractive is not established by CI alone.

Product-first README/QUICKSTART/INSTALL/docs index and security/deployment/theming docs reconcile behavior, keep OAP history out of product narrative. Standard five exact-head checks quality/test/security/container/oap-harness plus links/pip audit apply. Final fresh isolated ICA begins with human scope, full current architecture/digest and exact current merged immutable revision; maps ALL applicable SAR001..047 source/runtime/negative evidence. Old internal-pilot ICA cannot qualify this changed target. Findings require bounded corrections then repeat architecture-to-current-main audit, not only closed-findings review. Human owns milestone acceptance/release/real Internet exposure, DNS/TLS/firewall/identity/secrets/private data; development and disposable qualification authorize none of those real actions. Development evidence may support presenting one exact revision to D2, never authorize deploying it.

## Append stable requirement rows (same existing Source/Inspect/Evidence/classification format)
SAR-039 Internet HTTPS/proxy boundary: enforce complete A15 topology/trust/TLS/config/error/headers/log/privacy/docs/health/DB/secrets contract. Source human requirement1/current A15. Inspect config/settings/middleware, deployment/Compose/proxy, docs. Evidence real disposable HTTPS proxy, spoofed forwarded peers/headers, negative hosts/origins/cookies/settings/errors, private topology and leak canaries. Initially UNPROVEN for new milestone.
SAR-040 Shared authentication and API abuse control: enforce A15 cross-process member+admin login and API bounds, sane configurable rates, trusted client identity, safe failure/expiry/cleanup and no permanent account-lockout. Source human requirement1 security paragraph. Inspect actual limiter storage/middleware/auth/adapters and deployment. Evidence real multi-process attacks, invalid/valid bearer scopes, retry behavior, worker-count scaling, database-failure negatives, legitimate requests. Initially UNPROVEN.
SAR-041 Default fresh-install policy: enforce A15 defaultglobal values, required-field clear defaults, fresh/repeated/configured-upgrade behavior, atomicity/unique activeglobal, actual reservation succeeds. Source human requirement2. Inspect initialization/migrations/services/supported operator paths. Evidence fresh+upgrade DBs, repetition/races/rollback, policy UI units and booking. Initially UNPROVEN.
SAR-042 Public product entry: enforce A15 anonymous landing identity/Login/Administration no private leakage, admin login route and sensible role navigation/no loops. Source human requirement3. Inspect URLs/web templates/auth. Evidence anonymous/member/staff/admin/inactive/service-account real browser routes/CTAs and leak tests. Initially UNPROVEN.
SAR-043 Browser product identity: enforce A15 no visible Django/framework branding across all user/admin/error/title/footer/breadcrumb surfaces, proper structural custom admin and protected-model explanations. Source human requirement4/administration experience. Inspect actual AdminSite/templates/errors. Evidence browser inner_text/title/accessible labels no-framework assertions, not source-import blacklist or CSS hiding; permission matrix unchanged. Initially UNPROVEN.
SAR-044 Explained accessible forms: enforce A15 systematic member/management/admin/filter fields, human token scopes, units/policy/DST/high-impact/help associations, validation preserved. Source human requirement5/defaultpolicyUX. Inspect forms/admin/raw templates. Evidence complete field inventory+coverage, meaningful visible help/labels/aria, negative validation and protected mutations. Initially UNPROVEN.
SAR-045 Safe operator appearance overrides: enforce A15 self-contained default read-only Docker/no-rebuild logo/compact/favicon/images+CSS-after-default safe customization with no code/template/remote-JS/file escape. Source human requirement6/theming acceptance. Inspect actual handler/settings/mounts/template assets/docs. Evidence custom fixture Playwright, missing/invalid/path/symlink/MIME/mount/failure negatives. Initially UNPROVEN.
SAR-046 SLAIF design and visual qualification: enforce A15 current reference inspection, coherent accessible responsive system, all role/surface viewport/default/custom screenshot view/iterate and semantic regressions. Source human requirement7/Playwright primary acceptance/visual quality bar. Inspect CSS/tokens/templates/assets/browser evidence. Evidence actually reviewed privacy-safe screenshots1440/1024/768/390, default/custom, contrast/focus/layout/help/navigation/no overflow and visual iteration notes. Initially UNPROVEN.
SAR-047 Threaded Gunicorn responsiveness: enforce A15 preserve/reproduce fix, consistent deliberate pool and six held idle/partial actual health/login bounded responses with old sync sensitivity and cleanup/proxy rationale. Source human requirement8. Inspect image/Compose/rehearsal and real Gunicorn tests. Evidence exact config, negative oldsync and positive threaded sockets, held-open and failure cleanup, existing DB concurrency. Initially UNPROVEN (predecessor evidence indexed but not self-certified ICA).

## PLAN changes
Label original conversion/baseline sections historical at header, preserve chronology/evidence. Add current selected milestone contract/priorities derived A15 with exact all-eight human meaning and newIDs; remove current implication workflow-only/request-internal-only or Internet unselected. Preserve deferred OIDC/projects/notifications/execution/scheduler/real cutover and realD2 gates. Table bounded sequence runtime -> architecture -> proxy -> sharedabuse -> defaultpolicy -> landing/admin -> help -> themes -> finalqualification+freshICA; futureorders remain DRAFT UNTIL STRATEGIC RECONCILIATION, no invented PR/SHA. Currenttarget selected, notcomplete. Distinguish oldproof gaps/results from current evidence.

## Projection/coverage acceptance
Only after fullARCH applied, compile ARCHITECTURE-for-agents to all47 stable requirements preserving original38strength and new faceted contract, currentfullsource SHA256 identity, no historic currentstack/workflow-only claim. Write small current governance/projection-review document mapping A15 obligations -> IDs -> compact clauses, list strategy-only decisions explicitly, actual byte measurements transitive mandatory readset <=50000, projection<=20000, exact tokens UNMEASURED unless qualifiedtokenizer. Preserve archived generation1mapping/digests. Semantic comparison deliberate, not ICA. No hidden mandatory read full architecture/PLAN/history. If mismatch affects scope, stop report rather than blindhashrewrite. CurrentICA protocol derive IDs dynamically/canonicalcurrentindex rather than hardcoded38 for newrequests; old audits/templateshistorical remain preserved. No new framework/harness/test platform.

## Verification/reporting/recovery
Diff allowlist proof no runtime/app/test/dependency/migration/archived/governance-law changes; source/projection facet comparison and measured bytes, links, existing lint/format/typecheck and standard exact-head fiveCIchecks. Immutable normal implementation/reportonly sequence. Strongest objection: a new target paragraph could silently imply controls implemented or erase original guarantees; keep intent vs evidence distinct, preserve38IDs and sourcehistorical labels and require fresh all47ICA. Decision D0, DHA NONE, no deployment or milestonecomplete claim.


## Publication, exact evidence and continuation
Issue63/one branch/PR; Closes #63. Ordered code/config bytes are unchanged (only files explicitlyallowed above); do not invent application implementation for the new contract. Fullsource authored here by strategy; apply to root first before compilingcompact, source hashes computed AFTER those authorized changes. Run existing locked lint/format/type/diff and standard five exactimplementation-head checks SUCCESS before COMPLETE; CI runtime tests guard preservation but not implementation of newtarget. No meaningless new tests for prose. Normalimmutable report-only firstparent actualimplementationSHA/SELF, reportchecks unknown atauthoring, pushremoteverify/notifyexit. Report exact source/projection digests, measuredbytes, semanticmapping limitations, allchangedpaths, zero runtimebytechange and newrequirements UNPROVEN until freshICA. Previousorders/reports frozen; no Codingmerge. Expectedreport oap/reports/032-a-internet-ux-contract.md. Wrapper consumedcontrolonce, qualifiedcodingprofileunchanged. On gap/out-of-scopefailure boundedtruthful reporttostrategy ratherthan broaden.

## Deferred human adjudication
- Decision: NONE
