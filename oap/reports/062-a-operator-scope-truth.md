<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "062-a",
  "order_path": "oap/orders/062-a-operator-scope-truth.md",
  "order_sha256": "20d61dc2e2996498aaeed7d55ec9f1cf02d02186ad4d09b1c2303b6b67cdcf5b",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 128,
  "pr_number": 129,
  "branch": "codex/128-oap-062-a-operator-scope-truth",
  "implementation_head": "701fcba038f5dc5ca4047cbc8001afac98a1b64e",
  "base_sha": "50502f2e158d64fb0f16135e0ea187fa44b82589",
  "previous_round": null,
  "pr_mode": "CREATE_OR_RESUME",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "701fcba038f5dc5ca4047cbc8001afac98a1b64e",
    "runs": [
      {
        "run_id": 43008266847,
        "workflow": "CI",
        "jobs": {
          "quality": "PASS",
          "test": "PASS",
          "security": "PASS",
          "container": "PASS"
        }
      },
      {
        "run_id": 43008266886,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "PASS"
        }
      }
    ]
  },
  "local_equivalent_checks": "docs-only round: git diff --check clean at implementation head, all changed relative Markdown targets verified to resolve, present-tense absence-language scan of the five changed docs clean in context, untouched canonical/operator/code/runbook-body docs verified unchanged by exact diff name-only listing; no application/runtime/dependency/test/Compose/README/INSTALL/deployment/authorization/domain-model/form-inventory bytes changed, so no local product test run is in scope (see Acceptance 4)",
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 062-a — execution report: correct current operator and canonical authorization wording

Implementation head SHA: 701fcba038f5dc5ca4047cbc8001afac98a1b64e
Report publication commit: SELF

## Identity and result

COMPLETE for order 062-a (D0, `Decision: NONE`), issue #128, PR #129
(CREATE_OR_RESUME, `Closes #128`), branch
`codex/128-oap-062-a-operator-scope-truth`, base
`50502f2e158d64fb0f16135e0ea187fa44b82589` (current main). The order file at
`oap/orders/062-a-operator-scope-truth.md` (strategy-published bytes, SHA-256
`20d61dc2e2996498aaeed7d55ec9f1cf02d02186ad4d09b1c2303b6b67cdcf5b`) and the
`oap/active` pointer (`062-a`, ID+LF, verified by od) were committed together
with the implementation. All 12 order `source_hashes` were verified
SHA-256-byte-identical at the branch base before the first edit; governance
revision `14fc20b1ff52788974fd3f282322afc9d71362f9` was untouched; no other
order, report, migration or domain file was changed. No merge, no auto-merge,
no self-approval, no CRITICAL append, no DHA.

The branch is a single implementation commit
`701fcba038f5dc5ca4047cbc8001afac98a1b64e` on base plus this report-only child.
No force-push, no history rewrite, no renumbering.

This objective closes the definite current-text contradictions found by the
fresh independent full SAR-001..056 ICA at exact clean merged main
`50502f2e158d64fb0f16135e0ea187fa44b82589` (52 IMPLEMENTED / 4 PARTIAL;
exact-main CI run 43004913109 and OAP run 43004913190 five/five SUCCESS; no
product-code blocker). The linked developer domain/form-inventory cluster is
deliberately reserved for a separate follow-on objective per the order. A
fresh full-matrix independent ICA at the exact merged revision after this PR
(and the follow-on objective) merges determines closure; this report is not
that self-certification.

## Numbered acceptance evidence

### 1. PLAN dated/current truth

- **P-03 (stale cap removed).** Base line: "The full canonical architecture
  and SAR requirement index are in ARCHITECTURE.md (SAR index, SAR-001 through
  SAR-038)." Now: "The full canonical architecture and the current SAR
  requirement index are in ARCHITECTURE.md (its full current SAR index)." No
  hardcoded range remains, so no future expansion can leave a stale cap
  behind.
- **P-04 (selection-era context dated, current exceptions stated).** The
  2026-10-04 selection sentence now reads "at that selection
  projects/memberships/resource restrictions were deferred and real Internet
  exposure remained a human D2 decision", and the former present-tense
  "Current alpha scope excludes OIDC/password reset/email/notifications, ..."
  list is explicitly labeled "The selection-era exclusions stated on that
  date ( ... ) are preserved as dated selection context, not current
  claims." Human provenance (attributable human, P-06,
  M-INTERNET-UX-PILOT) and the D2 gate are untouched.
- A new short paragraph follows, stating the implemented A-16/A-17
  exceptions by name: exact-asset group booking eligibility, explicit
  management and read-all capabilities, configured administrator onboarding
  email, logged-in own-password change — and re-stating what remains
  deferred and separate (projects/organizational memberships and delegated
  group ownership, OIDC and public forgotten-password reset, general
  notifications, real Internet exposure/deployment as human D2), linked to
  `[Authorization](docs/authorization.md)`. P-04 gains no PR ledger, no
  milestone-closure claim and no risk-gate change; the following
  "A first external or institutional pilot..." paragraph is unchanged.
- Grounding (read-only, order-declared sources verified at base): the
  A-16/A-17 selected-target clauses and SAR-048..SAR-056 in the compact
  projection and root ARCHITECTURE.md (hash `f7b5c988...`), and the current
  implementation in `src/slaif_reservation/accounts/authorization.py`
  (hash `47a206e9...`), `src/slaif_reservation/management_ui/views.py`
  (hash `b9f589ca...`), `src/slaif_reservation/management_ui/auth.py`
  (`management_required` fail-closed capability gate) and
  `src/slaif_reservation/web/urls.py` (`profile/password/` route, SAR-054).

### 2. Operator/user entry text

- **SECURITY.md.** Base: "Project/group resource authorization and
  database-role separation are deferred; ...". Now: "Project/
  organizational-membership authorization and database-role separation are
  deferred, while exact-asset group booking eligibility is implemented; ..."
  with the link list extended to include
  `[Authorization](docs/authorization.md)`. The deferral is narrowed exactly
  as ordered; no new public-readiness claim.
- **QUICKSTART.md.** The member-UI list now includes `/profile/password/`
  (change your own password). The base "Staff-only areas: `/manage/` ... and
  `/admin/`." is replaced by: "`/manage/` (policies, blackouts, cross-user
  reservations, audit) admits any signed-in active non-service-account human
  holding the matching documented management capability, including non-staff
  accounts. `/admin/` requires staff admission plus the relevant model
  permissions." This matches the verified source gate: `management_required`
  denies any authenticated caller missing every named capability (staff
  alone confers nothing) and `has_reservation_permission`/
  `has_any_reservation_permission` fail closed for service accounts and
  inactive users; `/profile/password/` exists in `web/urls.py` for signed-in
  users. No claim is made that all authenticated users can book or read all.
- **docs/human-ui.md.** Base: "Staff can configure different policies." Now:
  "Operators holding the manage-booking-policies capability can configure
  different policies." (the `reservations.manage_booking_policies`
  application permission, which includes that module's read interface per
  SAR-048).

### 3. Historical index label

- **docs/runbooks/README.md.** The preparation-pack entry is now:
  "- [Internal-alpha pilot preparation](internal-alpha-pilot-preparation.md)
  — historical/superseded planning pack, not current operator guidance;
  current installation and operation live in [INSTALL](../INSTALL.md)."
  `docs/runbooks/internal-alpha-pilot-preparation.md` (body and its 060-a
  top banner) is byte-untouched (verified by diff name-only listing); no
  other runbook changed. The optional first-deployment SMTP clarity was
  correctly left out of scope.

### 4. Evidence/publication and scope proof

- `git diff --check` at the implementation head: clean (exit 0).
- Changed-path proof (implementation commit name-only): exactly
  `PLAN.md`, `QUICKSTART.md`, `SECURITY.md`, `docs/human-ui.md`,
  `docs/runbooks/README.md`, `oap/orders/062-a-operator-scope-truth.md` and
  `oap/active` — all within the order's allowed_paths; README/INSTALL/
  deployment/authorization/domain-model/form-guidance/ARCHITECTURE/
  CRITICAL/projection, all application source/migrations/tests/fixtures,
  dependencies/uv.lock, Docker/Compose/proxy/security settings, OAP helpers/
  workflows and historical audit/order/report/runbook bodies are unchanged.
- Link/anchor check: every changed relative Markdown target resolves at the
  implementation head (`docs/authorization.md` from repo root in PLAN.md and
  SECURITY.md; `../INSTALL.md` from `docs/runbooks/`); no changed anchor
  references; pre-existing links in the touched files were not modified.
- Absence-language scan of the five changed docs: remaining "absent/
  missing/staff-only" hits were each read in context and are unrelated true
  statements (bootstrap process-state provenance in PLAN, policy
  missing/ambiguous fail-closed in QUICKSTART and human-ui, staff-only
  internal location metadata in human-ui, historical ICA-finding record in
  PLAN). No present-tense absence claim about group eligibility, management
  capabilities, onboarding email or own-password change remains in the
  changed text, and no new false public-readiness or cross-user access claim
  was introduced.
- **Five exact-head CI at implementation head
  `701fcba038f5dc5ca4047cbc8001afac98a1b64e`: PASSED** — `gh pr checks 129`:
  quality pass (14s), test pass (10m24s), security pass (16s), container
  pass (54s), all under CI run 43008266847; oap-harness pass (45s) under OAP
  run 43008266886. Five/five SUCCESS, no missing/skipped/cancelled check.
- No local product test run was executed in this round: the diff is pure
  Markdown in the five allowed docs plus the order/pointer bytes, and the
  order's test list assigns evidence to link/anchor/absence scans, the
  docs-only diff proof and the normal five exact-head CI, all of which were
  performed. No unrelated local bespoke qualification was added.
- PR #129 was opened before this report with `Closes #128`; publication
  remote checks (remote head/report bytes/parent/report-only diff) are
  recorded in the private execution receipt, not here.

## Uncertainty, dependencies, DHA and limits

- Report-head CI is NOT YET OBSERVED AT AUTHORING; it is reported separately
  from the observed implementation-head CI above and no future check success
  is claimed.
- This is docs truth only: no security/authorization behavior, reservation
  semantics, route or migration changed. The strongest objection (erasing
  historical human selections or overstating current rights) is addressed by
  keeping the 2026-10-04 selection prose explicitly dated and by stating
  only capability-gated current access with its exact deferrals.
- The follow-on linked developer-reference (domain/form inventory) objective
  and the final fresh independent full SAR-001..056 ICA at the exact merged
  revision remain separate; nothing here claims milestone closure, ICA
  acceptance, real SMTP/deployment or strategic acceptance of this report.
- DHA: NONE. No CRITICAL append; no human disposition requested or invented.
