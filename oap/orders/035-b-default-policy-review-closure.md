<!-- OAP-META
{
  "id": "035-b",
  "round": "b",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "0a81b931a11e6598540c2a6071b1e99ee895499e",
  "issue_number": 69,
  "branch": "codex/69-oap-035-a-default-policy",
  "pr_mode": "AMEND",
  "allowed_paths": [
    "src/slaif_reservation/reservations/initialization.py",
    "src/slaif_reservation/reservations/management/__init__.py",
    "src/slaif_reservation/reservations/management/commands/__init__.py",
    "src/slaif_reservation/reservations/management/commands/initialize_default_policy.py",
    "src/slaif_reservation/config/operational.py (initializer registration only)",
    "tests/test_default_policy.py",
    "tests/test_operational_hardening.py (command registration only if necessary)",
    "QUICKSTART.md",
    "INSTALL.md",
    "docs/deployment.md (policy initialization only)",
    "docs/human-ui.md (default values only)",
    "TESTING.md (new evidence commands only)",
    "deploy/rehearse_internal_alpha_deployment.sh (initializer after migrations only)",
    "deploy/rehearse_https_boundary.sh (policy fixture adaptation only if necessary)",
    ".github/workflows/ci.yml (initializer after migrate only)",
    "ARCHITECTURE.md (exact A-15 amendment below only)",
    "ARCHITECTURE-for-agents.md (exact SAR-041 clause below and actual full-source digest only)",
    "docs/governance/DEFAULT-POLICY-PROJECTION-REVIEW.md",
    "oap/active",
    "oap/orders/035-a-default-policy.md",
    "oap/reports/035-a-default-policy.md",
    "oap/orders/035-b-default-policy-review-closure.md",
    "oap/reports/035-b-default-policy-review-closure.md"
  ],
  "forbidden_resources": [
    "application model/schema/dependency/inventory/old migration changes",
    "generic system-staff bypass, HTTP or startup initialization, other UI/theme/API/network features",
    "OAP machinery/immutable history changes",
    "real deployment/exposure/secrets/DNS/TLS/firewall/private production/lab/legacy data",
    "foreign resources/reset/clean/stash/forcepush/auth copying"
  ],
  "requirements": [
    "SAR-008",
    "SAR-009",
    "SAR-025",
    "SAR-031",
    "SAR-037",
    "SAR-041"
  ],
  "decision_class": "D0",
  "target_gate": "M-INTERNET-UX-PILOT development only; real exposure remains human D2",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "f8a8df265d4dd452969d4bee874045c8f8a8261f9c87c96ba4c049a7dddf320d",
    "PLAN.md": "b19219e2d727af5a9554e011ba45a786f1bb61f25c001011fc18006cae665d08"
  },
  "previous_round": "035-a",
  "pr_number": 70
}
-->

# 035-b — Default-policy review closure

H: human requirement2 and latest instruction to use CODING. A: A-15/SAR-041
and preserved008/009/025/037. E: actualPR70 implementationa4c577722a6a5960bb73e2a01d78f178bcc8a295/report124bff04d5c37daaaf96d426d5aa4cb9e62b3034 verified3PASS realremote/firstparent/report-only; final implementation all5 checks SUCCESS/fullCI803passed388.52s. Full source/projection match exact ordered amendment; unchanged other bytes;19979 projection/34902 routine bytes. I: full independent47row ICA remains later. C: D0/DHA_NONE.

Same objective/branch/PR70/base0a81b931a11e6598540c2a6071b1e99ee895499e.
Retain all035-a acceptance and source/runtime bytes. This is the SINGLE
collected corrective review round; do not add optional refinements.

1. Correct overlap-limit explanations in QUICKSTART/INSTALL/docs/human-ui:
   source rejects when existing intersecting blocking count is >=8, so a new
   booking requires FEWER THAN8 existing intersecting records. State this
   clearly, including proposed-interval count vs maximum simultaneous sweep.
   Do not change stored cap8 or domain evaluation. Other default values intact.
2. Repair and strengthen global-policy insertion race evidence. Actual
   STRATEGIC diagnostic at literalimplementationa4c: delaying only operator
   policy validation150ms selects initializer-first scheduling; original race
   test then fails with uncaught ValidationError and missing worker outcome
   KeyError. Normal create_policy can reject duplicate active-global via
   full_clean ValidationError OR final DB IntegrityError; both legitimate.
   Catch only expected active-global constraint conflicts, never arbitrary
   errors. Use deterministic event/lock synchronization to exercise both
   initializer-first and configured-writer-first orderings; no fixed sleeps in
   durable tests, silent thread exceptions or reduced assertions. Verify exact
   preserved row values and single coupled audit, with bounded joins/cleanup.
   Private diagnostic receipt/log index:
   /home/ubuntu/codex-supervision/slaif-asset-reservation/workorders/035-race-probe.json
   Read selected failure evidence only; never dump credential-bearing logs.
3. Correct successor coverage wording: one of47 SAR clauses changed, so46
   other SAR clauses remain, not "all other47". Canonical A15/projection/PLAN
   bytes remain EXACTLY unchanged from035-a. No hash churn or machinery change.
4. Preserve immutable035-a report. New report explicitly supersedes its
   assertion that the796/7 pre-commit working-copy run was at the literal future
   implementation SHA. Describe that run as pre-commit/untracked snapshot
   failure; final full evidence is literalhead CI803pass. Do not invent a local
   full pass. Root fresh isolated pilot probes passed unchanged at preceding
   5205296eaa620e7c164d2075c2d25f3c1b51280d(12.12s) and candidatea4c(11.68s)
   using separate owned DBs; retain earlier agent failures honestly as local
   environment/time-sensitive observations, not new product claims. Report
   schema command data/audits remain unchanged. Local OAP role/environment
   failure is not a reason to edit machinery or bypass required CI.
5. Focused corrected tests/docs first. Commit final implementation then use
   full required exact-head CI suite/five jobs; this satisfies final full-suite
   requirement. No need to repeat the unchanged broad local suite unless a
   relevant new failure requires it. Preserve required report-head CI (the
  035-a report CI is already running; never cancel/waive it). Short immutable
   report with real commands/counts/limits/SELF and actualremoteverification.

No application/initializer/domain/settings/schema/migrations/dependency/
inventory/permissions/network/branding source change. Only specified docs,
race tests, coverage wording and normal order/active/newreport files. Owned
PG/source copies only; clear OAP_ROLE in product-test child environments to
avoid leaking launcher role into role-prerequisite fixtures. Existing owned
DB receipt033b-owned-test-db.json and installed tools remain available.
Strongest objection: test correction could conceal failed authority. Require
specific expected conflict types, deterministic opposite serial schedules,
unchanged values/audit and exact-head full CI; no weaker product assertion.
Coding never merges or exposes a real service.

## Deferred human adjudication
- Decision: NONE
