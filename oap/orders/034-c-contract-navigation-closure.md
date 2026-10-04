<!-- OAP-META
{
  "id": "034-c",
  "round": "c",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "f8430fa14e0f53339f7c1e1427fe52a3fa56ba7e",
  "issue_number": 67,
  "branch": "codex/67-oap-034-a-shared-abuse-controls",
  "pr_mode": "AMEND",
  "previous_round": "034-b",
  "pr_number": 68,
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
    "oap/reports/034-a-shared-abuse-controls.md",
    "tests/test_api_schema.py (DB fixtures only; preserve assertions)",
    "tests/test_api_tokens.py (DB fixture on API-root test only)",
    "tests/test_proxy_security.py (DB fixture on anonymous API adapter test only)",
    "tests/test_proxy_gunicorn.py (owned migrated DB for existing body control only)",
    "oap/orders/034-b-baseline-fixture-closure.md",
    "oap/reports/034-b-baseline-fixture-closure.md",
    "tests/browser/test_human_mvp_browser.py (navigation wait only)",
    "oap/orders/034-c-contract-navigation-closure.md",
    "oap/reports/034-c-contract-navigation-closure.md",
    "oap/reports/034-b-baseline-fixture-closure.md"
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

# 034-c — Contract and navigation review closure

H: selected shared abuse controls and human direct execution. A: SAR-040 and
preserved API/token contract. E: exact034-b implementation914f0630bdc6ff63f3c8fcf30bbf8dfdc98b6b7a all five CI jobs SUCCESS/full787 passed; local786 passed/1 browser empty-page navigation failure, unchanged focused retry1 passed. Final source review finds create schema200 contradicts actual201. C: D0/DHA_NONE.

Same objective/branch/PR68, retain all034-a/b criteria. Only:
1. Declare201 for reservation-create success, keep429/503; pin generated schema
   to the actual response. No HTTP/domain/idempotency behavior change.
2. Wait for token-list heading after clicking Back before reading its content.
   Preserve all one-time secret/revoke/privacy assertions; no sleeps or retries
   masking application failures.
3. Focused schema/browser first; full required suite at final implementation
   head after these relevant changes, all five exact implementation/report-head
   checks. Short immutable report states failures honestly. Stopped external
   coding agent remains stopped; direct execution is human-authorized.

Strongest objection: repairing tests can hide behavior changes. Preserve real
HTTP assertions and only synchronize on rendered destination. No other feature,
source, dependency, authority, data, deployment or governance machinery change.

## Deferred human adjudication
- Decision: NONE
