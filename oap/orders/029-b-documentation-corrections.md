<!-- OAP-META
{
  "id": "029-b",
  "round": "b",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "state": "FINAL",
  "base_sha": "f406c612f52f64a50f0a145b27a7f580838c7287",
  "issue_number": 57,
  "branch": "codex/57-oap-029-a-product-documentation",
  "pr_mode": "AMEND",
  "previous_round": "029-a",
  "pr_number": 58,
  "allowed_paths": [
    "README.md",
    "QUICKSTART.md",
    "INSTALL.md",
    "CONTRIBUTING.md",
    "docs/README.md",
    "docs/oap-workflow.md (issue lifecycle sentence only)",
    "oap/orders/029-b-documentation-corrections.md",
    "oap/active",
    "oap/reports/029-b-documentation-corrections.md"
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

# 029-b — Correct documentation usability, secret handling and operator navigation

FINAL. Same objective/issue #57/PR #58, same branch. No new product objective.

## Goal and strategic review

At actual implementation b2998a9bae1424f411c1cbfc6c4cc4f59a642e28 / published report 2b2dc31b638f39b6bbab90f288f775e3fdb37d9b, strategy rejects 029-a acceptance claims 1 and 4 as incomplete. The source/diff inspection finds copy/paste placeholders, unsafe password literals, misleading quiet-config claim, missing operator sections and incomplete navigation. Review is independent of the security-CI blocker. Report-only parent/remote/PR identity passed verify_report 3/3. All runtime/source/test/config/dependency/history bytes remain base-identical. 029-a's report remains immutable; b corrects prose and supersedes incorrect interpretations explicitly.

## Provenance and boundaries

- H: current human documentation-productization instruction 2026-10-03, deliverables1–5, tone, truth, verification, no hidden product change, end-to-end coding/review loop. Same authorized objective.
- A: S-05/S-06/S-12/S-15/S-16/S-19/S-21; SAR-022/023/024/025/027/031/032/033/036/037/038; 029-a numbered acceptance1/4/5/6/7.
- E: actual reviewed PR58 bytes at b2998a9 and report2b2dc31; plain compose config prints resolved application environment; accounts/models.py USERNAME_FIELD=email; current source/config/CLI and verified links. Exact implementation CI37130103563: quality/test/container PASS, securityFAIL; OAP37130103499 PASS. Remote failed log confirms only urllib3 2.7.0 PYSEC-2026-4175/4176/4177 fix2.8.0. Read-only uv tree confirms dev-only chain via requests/pip-audit/pytest-playwright; dependencies unchanged. Human scope exception for separate security PR is PENDING, NOT authorized by this order.
- I: no new ICA finding or milestone claim; strategy owns eventual freshness assessment. Prior ICA remains bound to a9c3133.
- C: D0 correction of known documentation defects under explicit scope; DHA NONE, no CRIT admission conditions.

## Ordered reads

Compact normal coding set; exact 029-a report; six changed documents; only source/help excerpts needed for corrections below. Do not reload all historical/source books or rerun unchanged large local suites. Existing execution evidence may be reused with exact identity/adaptations; current-head remote CI remains mandatory before acceptance. No dependency/security waiver.

## Base and recovery

Remote main remains f406c612f52f64a50f0a145b27a7f580838c7287. Resume the existing branch codex/57-oap-029-a-product-documentation and actual PR58 at report head2b2dc31b638f39b6bbab90f288f775e3fdb37d9b. No force push/rebase/report edit/reset/clean/stash. If changed unexpectedly, report discrepancy and reconcile. Keep old order/report bytes unchanged. The exact new order and active029-b pointer are strategy-owned bytes to commit with implementation. Standard final report-only sequence applies.

## Non-goals

No src/tests/deploy/Compose/Dockerfile/dependency/workflow/inventory/canonical governance/history changes, no unrelated PR, no merge, no D2. Security remediation is not allowed here. All disposable runtime verification must use a disposable checkout and unique project/port/IMAGE; inspect collisions and never overwrite a shared image tag or existing env/secret. Keep synthetic credentials out of outputs and erase only exact owned temporary files/resources.

Goal: finish the authorized documentation productization on issue57/PR58. No dependencies/runtime changes. Correct source-verified usability/security errors and missing requested operator sections. Current security CI is blocked by unchanged dev urllib32.7.0 (3 advisories); do NOT upgrade, suppress, waive, or present all-green. Human scope decision pending separately.

## Scope and numbered acceptance (same six docs only)

1. Every clone command must use actual https://github.com/ulfe-lmi/slaif-asset-reservation.git. QUICKSTART and CONTRIBUTING must run as written; no <private-repo-url>. INSTALL reviewed revision is operator-selected: use an explicit shell read prompt and verify full commit rather than a redirection-prone <reviewed-commit-sha> literal in executable commands.
2. Remove both insecure/broken inline-password CLI alternatives from QUICKSTART/INSTALL. Keep interactive createsuperuser, accurate email/password prompts. No default username/admin claim. Noninteractive verification is an honestly described TEST adaptation using secret environment input, never an invented literal password or output. Add curl prerequisite and use curl -fsS for health200. Remove agent-like sentences about inventing accounts/fake seed data/correct expected behavior; simply say staff creates an active policy in /manage/ before booking, optional sanitized assets are not hardware verification.
3. Fix claims that static project name can NEVER collide/touch another stack. Explicitly require unused project name and check existing project/volume before first run; if present select another name consistently, do not adopt/delete it. Keep obvious destructive warning for down -v, default teardown preserving data. QUICKSTART should be concise (~120–150 lines if feasible), not defensive prose.
4. INSTALL: compose config --quiet is the safe no-output validation command. Current config (without --quiet) prints resolved env secrets and is NOT quiet. Require umask077 and mode0600 for deploy/env.production BEFORE real values are written. Preserve existing-file/no-overwrite guidance and secret-dir0700/passwordfile0600. Generate no real secret in this test. Keep exact current hostname+127.0.0.1 requirement; correct label public hostname to approved service hostname for internal pilot. Actual independent strategy HTTP smoke at source-identical production settings: omitted127 ->400; added127+forwardedhttps->200; added127withoutheader->301. No security weakening.
5. INSTALL: replace sections3(local evaluation) and4(development) with short pointers to QUICKSTART/CONTRIBUTING, retaining headings/section numbers for inbound references. Remove explicit banned boilerplate No other requirements are invented..., Every command below corresponds... . Add a compact linked contents/navigation list near top. Preserve section5 step numbering and section6/12 pointers used by current runbooks/request; do not change immutable history. Make operator guide clear rather than another full quickstart copy.
6. INSTALL: add actual task-oriented Uninstall/data retention and Troubleshooting sections, and practical application rollback commands to existing section9. No unrequested runtime settings. Existing rollback semantics: previous image must be compatible with current DB; retag recorded previous commit image to internal-alpha then compose up -d app, verify health/operational_check; incompatible DB requires approved backup restore, not Git revert/migrate guess. Stop/start/status commands must consistently use production compose file. Uninstall default down(no-v) retains named volume; optional destructive command plainly warned and limited to operator-owned project after retention decision. Troubleshooting covers ports, bad secret/mismatched DB password (changing POSTGRES_PASSWORD_FILE does not change password in existing PG volume), DisallowedHost/unhealthy probe, readiness503/migrations, proxy/CSRF, policy missing, backup tool location. Verify each fact via source/current tools.
7. INSTALL backup/restore: preserve correct PG-container native tool commands, protected backup storage/off-host responsibility, default wrapper dry-run and absent-client-tools-in-app limitation. Stop app before restore; do not restart after failed restore; document --exit-on-error if using native pg_restore and validate its actual PG17 help. Add safe destination-permissions/prerequisite wording; never print real secrets/fullconfig. Do not execute production restore; isolated checks only. Negative API expected401 check must not use curl -f then silently hide its failure or claim discarded body was inspected. Use clear status-only expected401, or capture synthetic body explicitly in verification.
8. README add direct ARCHITECTURE.md link in documentation table, OpenAPI information pointer (staff-only/disabled by default production correctly stated), and ensure no unrelated reference-product assumptions. Prefer plain cancellable/releasable instead of reducible jargon. Keep first100lines product/start beforeOAP.
9. docs index Start here includes canonical architecture; Users includes token/auth docs actual anchors; Operators directly links security model, backup/restore, readiness/preparation runbooks and migration runbook (private cutover remains separate). Move initial-conversion READINESS.md from normal operator path to labeled governance baseline. Governance includes AGENTS, PLAN, compact architecture and CRITICAL. Current canonical docs remain unchanged.
10. CONTRIBUTING: intro for human developer (architecture/security/testing and scoped issue); AGENTS/OAP instructions belong agent section. Add prerequisites/link to TESTING for required test tooling, don't replicate operator path. Keep developer commands accurate and normalbranchPR expectations.
11. Minimal docs/oap-workflow wording: objective PR uses Closes #issue only when satisfied; after merge strategy verifies closure, and reconciles a satisfied still-open issue with factual merged-PR closeout. No new machinery.

## Verification and negative paths

Relative links AND actual heading anchors; inbound numbered references; first100README/ledger sweep; gitdiffcheck; protected product/config/test/dependency/history bytes same. Verify amended commands safely in disposable context. Reuse 029-a realPG17 quickstart/rehearsal evidence only for unchanged behavior with exact adaptations; do not rerun unchanged expensive suites just for prose. Current standard remote CI still required; record actual results and BLOCKED security while unchanged. Do not label failed full local suite passed with failure. Prior local full suite was FAILED(610pass/1fail), clean-env harness154PASS separately; no sum. User/strategy approval does not waive CI.

## Documentation and reporting

PR body: concise finalproblem/result and verification/limitation, Closes#57, actualsourceheads and reportreference. Supersede incorrect 029-a PR assertion advisories postdate earliergreenCI: upstream publication is Sep15, which predates Sep21. What we observed is currentpip-auditfail vs historicalgreen, without proving why historicaldata differed. Immutable 029-a report remains unchanged; b report explicitly corrects interpretations as needed. Coding nevermerges; report-only finalcommit then exit.


Use structured CI data or `gh pr checks 58 --watch --interval 20`, not the prior broken line-count shell poll (the comma-joined one-line output made TOT=1 forever). Wait in a bounded shell, no model polling. Run IDs/head/status must be actual; never call FAILED passed-with-failure. If security still fails, publish a truthful PARTIAL/BLOCKED report after all checks finish, with exact implementation/report identities, then exit; no repeated attempt to fix forbidden dependencies. Response FIFO is /home/ubuntu/codex-supervision/slaif-asset-reservation/response.fifo; strategy already runs the receiver. A published report is frozen even if notification is lost.

## Deferred human adjudication
- Decision: NONE
