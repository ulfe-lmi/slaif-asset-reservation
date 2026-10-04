<!-- OAP-META
{
  "id": "034-b",
  "round": "b",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "f8430fa14e0f53339f7c1e1427fe52a3fa56ba7e",
  "issue_number": 67,
  "branch": "codex/67-oap-034-a-shared-abuse-controls",
  "pr_mode": "AMEND",
  "previous_round": "034-a",
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

# 034-b — Close baseline fixture integration gaps

H: selected shared abuse protection and current human direct-execution instruction. A: SAR-040 and preserved auth/body/privacy/idempotency. E: actual PR68/head5fdd9fa8c2b120be10a2dc85af5056c15db2667a report verified3checks/realremote, firstparent2d09a862d0d0b8d763e289292a1f5d841d4c45b6. Full owned run and CI:781passed/6failed; no merge accepted. C: D0/DHA_NONE.

Same objective/branch/PR. Retain all034-a controls and criteria. This correction
admits only necessary existing test fixtures; no production bypass, per-process
limiter, weaker assertion or unrelated feature.

1. Add explicit real DB fixtures to the four previously DB-free API adapter
   tests. Preserve API root/schema/absent-token-route/401 assertions.
2. Existing production body-limit regression must use an owned migrated test
   database now that login has shared counters. Retain real Gunicorn, valid
   CSRF small200/large400 controls, liveness and cleanup. Never use foreign5432
   or silently replace its body-limit proof with an early503/403.
3. Collect production static manifests in an owned test directory before real
   HTTPS admin login. Keep genuine successful member/admin login, shared
   quotas, worker/source spoof and account/token coverage. Test-only paths
   or instrumentation do not ship a production diagnostic endpoint.
4. Run focused failing cases first; full required suite at final implementation
   head after relevant corrections, all five exact-head checks and normal
   immutable report-head CI. No repeated unchanged full runs. Short report
   separates actual commands/head/failures/limits.

Strongest objection: fixture repairs can conceal enforcement failures. Preserve
original assertions and real PG/HTTP/proxy boundaries, with production controls
never disabled. No actual exposure, secrets/private data/DNS/TLS/firewall,
reset/clean/stash/forcepush or new dependency/governance machinery. Current
human directs STRATEGIC to execute directly; stopped coder stays stopped.

## Deferred human adjudication
- Decision: NONE
