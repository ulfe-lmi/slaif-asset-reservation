<!-- OAP-META
{
  "id": "040-a",
  "round": "a",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "fb135dbc4a91a6fc983f49a6785d75c4277029c2",
  "issue_number": 79,
  "branch": "codex/79-oap-040-a-deployment-contract",
  "pr_mode": "CREATE_OR_RESUME",
  "previous_round": null,
  "pr_number": null,
  "allowed_paths": [
    "README.md",
    "QUICKSTART.md",
    "INSTALL.md",
    "docs/README.md",
    "docs/deployment.md",
    "docs/security-model.md",
    "SECURITY.md",
    "docs/human-ui.md",
    "docs/branding.md",
    "docs/runbooks/ (only current contract contradictions)",
    "docs/audit/ (qualification/freshness/request drafts; no immutable report rewrite)",
    "ARCHITECTURE.md (only demonstrated normative inconsistency)",
    "ARCHITECTURE-for-agents.md (only required faithful recomposition)",
    "docs/bootstrap/ (only current projection coverage record, never historical snapshots)",
    "oap/active",
    "oap/orders/040-a-deployment-contract.md",
    "oap/reports/040-a-deployment-contract.md"
  ],
  "forbidden_resources": [
    "Application/backend/domain/schema/migrations/dependencies/runtime/configuration/inventory changes",
    "Real exposure/deployment/DNS/TLS/firewalls/production/private data/secrets/lab/Neumann resources",
    "OAP machinery/canonical law/stable requirement weakening or immutable history rewrites",
    "Valuable-source product tests, unknown cleanup/reset/clean/stash/forcepush/auth copying"
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
  "target_gate": "M-INTERNET-UX-PILOT combined qualification; real exposure stays human D2",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f8a8df265d4dd452969d4bee874045c8f8a8261f9c87c96ba4c049a7dddf320d",
    "PLAN.md": "b19219e2d727af5a9554e011ba45a786f1bb61f25c001011fc18006cae665d08"
  }
}
-->

# 040-a — operator contract and integrated qualification

One purpose: reconcile product/operator documentation with the implemented
Internet-reachable authenticated pilot, and substantiate the combined deployment
contract at the final head before fresh independent audit.

H: human requirements 1–8 and documentation/testing/ICA paragraphs; human direct
ROOT implementation override. A: A-15, all SAR-001–047 preserved. E: PR78 merged at fb135dbc4a91a6fc983f49a6785d75c4277029c2;
issue77 closed, zero open PRs/issues before creating issue79. Final implementation
01159efce5d91302e99a99a21509c440d0989048 / report8f773c49179e23e7dc5c71e11a2f4c2b6aa4a618
all5 checks SUCCESS (CI37344926250/OAP37344926002 and
CI37346880102/OAP37346880012); full964passes. Exact base/branch reconciled live. I: old internal-pilot ICA is historical only. C: D0,
DHA_NONE, real exposure remains human D2.

## Bounded scope

README.md, QUICKSTART.md, INSTALL.md, docs/README.md, docs/deployment.md,
docs/security-model.md, SECURITY.md, docs/human-ui.md, docs/branding.md,
operator runbooks only where their current instructions contradict the selected
contract, and a concise integrated qualification/freshness record under docs/audit.
Canonical architecture/projection only if an actual normative inconsistency is
demonstrated; no stable requirement removal, weakening or self-certified status.
No product/backend/schema/dependency/runtime/configuration changes, inventories,
real hosts/DNS/TLS/firewalls/data/secrets or OAP machinery expansion.

## Acceptance

1. README stays product-first. Describe supported authenticated HTTPS proxy
   topology, current shared login/API budgets, default policy, landing/Admin
   access, field guidance and optional read-only branding. Remove superseded
   claims that throttling is absent or only trusted-LAN deployment is supported.
   State broad authenticated human access, privileged runtime DB role, operator
   backup/monitoring/maintenance duties and absent institutional identity/reset/
   email/execution integration honestly. No production certification or work ledger.
2. Quickstart remains local evaluation, Docker loopback only, administrator-created
   accounts, deliberate migrations followed by initialize_default_policy, optional
   sanitized inventory, health and explicit destructive-volume warning.
   Installation is the full authenticated pilot operator contract: production
   secrets, private DB/app, HTTPS and explicit proxy peers/forwarding normalization,
   hosts/origins/secure cookies/SSL/HSTS opt-in, shared configurable budgets and
   safe failure, docs disabled/staff-only, privacy-safe health/logs, worker/thread
   capacity plus proxy bounds, branding, backup/off-host responsibilities,
   deliberate upgrades/rollback, maintenance and troubleshooting.
3. Reconcile security and deployment references with actual source; distinguish
   implemented controls from deferred project authorization/DB role separation/
   institutional identity and operational responsibilities. Keep immutable
   historical reports/orders/snapshots untouched. Task-oriented docs index links
   the design/theming material; no chronological development narrative for users.
4. Cross-check every changed normative command/variable/file/port/header/constraint
   against implementation. Use existing owned production-shaped and real-HTTPS
   rehearsals; exercise the supported fresh local evaluation path with disposable
   resource ownership and safe port override where host ports are occupied.
   No real data/proxy/public listener/cert issuance. Verify rendered production
   Compose topology and read-only branding overlay, health/readiness/default
   policy/admin initialization, migrations and backup/restore semantics.
5. Full standard five CI checks at literal final implementation head and report
   head. Index actual real PostgreSQL concurrency/rollback, browser auth/CSRF/
   owner privacy, six-held-client old-sync/positive threaded Gunicorn regression,
   HTTPS spoof/error/log/headers/private-docs negatives, shared multi-process
   login/API abuse tests, fail-closed settings, fresh/upgrade/default policy,
   branding safety/same-image/container tests, pip-audit and visual matrix evidence.
   Do not repeat unchanged full tests locally when exact final CI supplies them;
   focused diagnostics for discrepancies, honest skips/failures/unrun evidence.
6. Changed links and first README screen reviewed; no stale ledger/public target
   contradictions in normal docs. Assess full architecture vs current source;
   retain exact architecture digest if A-15 already matches accepted behavior,
   otherwise update full canonical source and recompose projection faithfully.
   Prepare an initial ALL47 UNPROVEN audit request/matrix dynamically from the
   canonical index after merge, using actual immutable revision, human scope and
   full architecture first. Fresh independent auditor is separate; do not declare
   closure from strategy or reuse old-target ICA as qualification.

Strongest reason against the change: changing deployment prose could imply real
exposure permission or claim unsupported controls. Pin every normative statement
to current enforcing code and disposable evidence, preserve limitations, require
fresh independent architecture-to-current-main audit, and keep human D2 explicit.

## Resources and execution

ROOT direct implementation; coding clients remain stopped under human override.
Every product operation runs owned disposable source with explicit owned PostgreSQL
URLs/settings/PYTHONPATH and minimal child environment with role cleared. Existing
PG17 receipt033b-owned-test-db.json exact ID/nonce must validate before use; never
source/eval/print its environment. Rehearsals own synthetic configs, random ports,
local-only certificates and nonce-labelled Docker resources with exact cleanup.
Do not damage foreign PG16, deployments, env files or project volumes. No real
account/inventory/export/credentials. No immutable future SHA/PR invented.

## Publication and review

Same-objective PR uses Closes #79. Only after all final implementation checks pass,
commit only immutable report with literal full implementation SHA first parent
and publication SELF; verify actual remote/report/PR identity. Report-head CI
remains mandatory. Strongest objection and limitations recorded; conditional
protected development merge only. Fresh independent audit is a separate role
and cannot be substituted by ROOT review.

## Deferred human adjudication
- Decision: NONE
