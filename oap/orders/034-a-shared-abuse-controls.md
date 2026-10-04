<!-- OAP-META
{
  "id": "034-a",
  "round": "a",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "f8430fa14e0f53339f7c1e1427fe52a3fa56ba7e",
  "issue_number": 67,
  "branch": "codex/67-oap-034-a-shared-abuse-controls",
  "pr_mode": "CREATE_OR_RESUME",
  "previous_round": null,
  "pr_number": null,
  "allowed_paths": [
    "src/slaif_reservation/api/models.py",
    "src/slaif_reservation/api/migrations/0002_abusebucket.py",
    "src/slaif_reservation/config/abuse.py",
    "src/slaif_reservation/config/settings/base.py",
    "src/slaif_reservation/config/settings/production.py",
    "src/slaif_reservation/config/settings/test.py (only explicit test isolation if needed; production controls never disabled)",
    "src/slaif_reservation/config/env.py (rate and bounded database waits only)",
    "src/slaif_reservation/api/authentication.py",
    "src/slaif_reservation/api/problem.py",
    "src/slaif_reservation/api/reservation_views.py (429/503 schema only)",
    "src/slaif_reservation/api/management/commands/purge_expired_abuse_buckets.py",
    "src/slaif_reservation/config/operational.py (cleanup registration only)",
    "tests/test_abuse_controls.py",
    "tests/test_abuse_http.py",
    "tests/test_settings.py (rate configuration negatives)",
    "deploy/env.production.example",
    "deploy/rehearse_https_boundary.sh (DB-failure503 and legitimate quota fixture adaptation only)",
    "docs/security-model.md",
    "docs/deployment.md",
    "docs/api-contract.md",
    "docs/decisions/0016-shared-abuse-controls.md",
    "SECURITY.md",
    "INSTALL.md",
    "TESTING.md",
    "oap/active",
    "oap/orders/034-a-shared-abuse-controls.md",
    "oap/reports/034-a-shared-abuse-controls.md"
  ],
  "forbidden_resources": [
    "all other feature/UI/theme/policy/inventory/dependency/governance machinery changes",
    "real production/lab/private exports/secrets/DNS/TLS/firewall/public exposure",
    "foreign resources/reset/clean/stash/forcepush/auth copying"
  ],
  "requirements": [
    "SAR-011",
    "SAR-012",
    "SAR-013",
    "SAR-014",
    "SAR-015",
    "SAR-016",
    "SAR-017",
    "SAR-018",
    "SAR-025",
    "SAR-026",
    "SAR-031",
    "SAR-032",
    "SAR-039",
    "SAR-040"
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

# 034-a — Shared login and API abuse controls

## Goal and provenance
H: human requirement1 mandates member/admin login and API abuse resistance
across workers; the current human additionally directs STRATEGIC to implement
directly after stopping CODING. A: A-15/SAR-040 with preserved auth/privacy/CSRF/
idempotency. E: accepted PR66, merged f8430fa, exact report8a762a1 all5 checks
SUCCESS and real proxy/client identity established. I: fresh full47-row ICA
remains later. C: D0 implementation of selected protection, DHA NONE.

## Scope and design
One purpose: shared abuse budgets. PostgreSQL atomic counters in the existing
API app, generic config middleware/core, authentication integration and one
forward migration. No Redis/cache/plugin/dependency or broader permissions.
Defaults: common member/admin login IP30/300s, normalized identity10/300s;
API pre-auth IP1200/60s, authenticated owner600/60s and token300/60s. Positive
bounded configurable rates; no permanent account lockout or disable switch
in production. Fixed-window boundary bursts documented. Keys use scoped HMAC,
not raw IP/email/token values; identity comes only from the established
canonical client, never another forwarded-header interpretation.

## Numbered acceptance
1. Member/admin login POST share IP/identity quotas, including equivalent case
   and route switches. Count attempts uniformly; preserve CSRF, role rules,
   generic failures and normal successful login. No account-state mutation.
2. Every /api/v1 request is bounded before costly authentication, including
   invalid/missing bearer; valid bearer operations also share owner/token
   budgets. Multiple tokens cannot multiply the owner allowance. Preserve
   scopes, owner404, idempotent replay and reservation/audit guarantees.
3. Atomic SQL enforces the declared quota across processes and threads, with
   saturated counts, fixed expiry and bounded connection/statement/lock waits.
   HTTP429 has Retry-After/no-store/correlation and stable API problem details;
   DB failure returns safe bounded503. Liveness remains DB-free.
4. Indexed expiry, bounded opportunistic cleanup and an operator command
   defaulting dry-run/explicit apply remove only expired rows. No failure
   audit flood, raw keys/credentials or account-existence oracle.
5. Focused real PG contention and real multi-worker HTTP/proxy tests prove
   member/admin limits, worker scaling, forwarded spoof rejection, valid/
   invalid bearer, multi-token owner budget, expiry/recovery, cleanup and
   failure behavior. Legitimate traffic and existing domain paths continue.
6. Document actual budgets/NAT tradeoffs, configuration/failure/cleanup and
   perimeter/DDoS limits. No Internet-readiness claim before the remaining
   selected milestone and independent audit.

## Verification and reporting
Focused tests while implementing; full required suite at final implementation
head and repeat only after relevant changes/failures. All five exact-head CI
checks required, including normal report-head CI. Owned PG17/source copies
only, no valuable env files or foreign5432. Short evidence report maps the six
criteria, exact commands/results/failures/skips and limits. Normal literal
implementation head, immutable report-only first parent/SELF, actual remote
verification. Root implements under current explicit human exception; do not
restart the stopped external coder or pretend self-review is independent ICA.

## Strongest reason not to merge
Counters can add DB contention and temporarily impede shared-NAT users. Bound
work/waits, expire predictably, use configurable generous defaults and prove
real concurrency/failure/legitimate paths. These controls are not distributed
DDoS immunity or deployment authorization.

## Deferred human adjudication
- Decision: NONE
