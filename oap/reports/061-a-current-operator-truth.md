<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "061-a",
  "order_path": "oap/orders/061-a-current-operator-truth.md",
  "order_sha256": "272ec20188f2b4010b92bffa609e4a6d6c83cfb271430e917be2fa66c910a3be",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 126,
  "pr_number": 127,
  "branch": "codex/126-oap-061-a-current-operator-truth",
  "implementation_head": "de1c609b9db6fce78279d3f36541d1fce3637587",
  "base_sha": "921f7a70dbd5c9d450661746ddee0e70af2cac59",
  "previous_round": null,
  "pr_mode": "CREATE_OR_RESUME",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "de1c609b9db6fce78279d3f36541d1fce3637587",
    "runs": [
      {
        "run_id": 43000851682,
        "workflow": "CI",
        "jobs": {
          "quality": "PASS",
          "test": "PASS",
          "security": "PASS",
          "container": "PASS"
        }
      },
      {
        "run_id": 43000851588,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "PASS"
        }
      }
    ]
  },
  "local_equivalent_checks": "docs-only round: git diff --check clean, all changed relative Markdown targets verified to resolve, current absence-language scan clean, untouched canonical/operator/code docs verified unchanged by exact diff name-only listing; no application/runtime/dependency/test/Compose bytes changed, so no local product test run is in scope (see Acceptance 4)",
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 061-a — execution report: correct current booking and read-all operator prose

Implementation head SHA: de1c609b9db6fce78279d3f36541d1fce3637587
Report publication commit: SELF

## Identity and result

COMPLETE for order 061-a (D0, `Decision: NONE`), issue #126, PR #127
(CREATE_OR_RESUME, `Closes #126`), branch
`codex/126-oap-061-a-current-operator-truth`, base
`921f7a70dbd5c9d450661746ddee0e70af2cac59` (current main). The order file at
`oap/orders/061-a-current-operator-truth.md` (strategy-published bytes, SHA-256
`272ec20188f2b4010b92bffa609e4a6d6c83cfb271430e917be2fa66c910a3be`) and the
`oap/active` pointer (`061-a`, ID+LF) were committed together with the
implementation. All 12 order `source_hashes` were verified SHA-256-byte-
identical at the branch base before the first edit; governance revision
`14fc20b1ff52788974fd3f282322afc9d71362f9` was untouched; no other order,
report, migration or domain file was changed. No merge, no auto-merge, no
self-approval, no CRITICAL append, no DHA.

The branch is a single implementation commit
`de1c609b9db6fce78279d3f36541d1fce3637587` on base. No force-push, no history
rewrite, no renumbering.

This objective closes the three current-text contradictions found by the fresh
independent full SAR-001..056 ICA at exact main `921f7a70` (53 IMPLEMENTED;
SAR-036/037/053 PARTIAL; 0 ABSENT/UNPROVEN; exact-main CI test run 42998271752
ultimately SUCCESS with 1461 passed; no product-code blocker): current
INSTALL.md, docs/deployment.md and docs/README.md operator/index prose
contradicted the implemented group-authorization (SAR-048..SAR-053) contract.
A fresh full-matrix independent ICA at the exact merged revision after this PR
merges determines closure; this report is not that self-certification.

## Numbered acceptance evidence

### 1. Read-all truth in INSTALL

- Before (base `921f7a70`): the booking-authorization bullet in
  `INSTALL.md` ended "Project/group resource authorization beyond booking
  (projects, organizational memberships, cross-user read access) is not
  implemented yet; account creation does not create project-scoped resource
  permissions." — a present-tense absence claim false after the delivered
  read-all implementation.
- After (implementation head), one hunk inside that bullet: "Cross-user
  reservation reading is implemented as a separate read-only surface: the All
  reservations browser view requires the explicit
  `reservations.view_all_reservations` permission, and the cross-user bearer
  list/detail additionally requires the token's `reservations:read_all` scope
  plus the token owner's current `view_all_reservations` permission. Both are
  read-only; no cross-user mutation or general user-directory API is implied."
  The deferral sentence now reads "(projects, organizational memberships) and
  per-token asset restrictions are not implemented yet" — project/
  organizational-membership authorization and per-token asset restrictions
  stay deferred exactly as in current source.
- Grounding: the joint permission+scope dual gate, the issuance ceiling
  (a token can only carry `read_all` while the owner currently holds
  `view_all_reservations`) and the read-only contract are exactly as
  documented in `docs/authorization.md` (order-declared source hash
  `cba3ef323d...`, verified at base) and implemented in
  `src/slaif_reservation/accounts/authorization.py` and
  `src/slaif_reservation/api/read_all_views.py` (order-declared hashes
  verified at base). The full-matrix link
  `[docs/authorization.md](docs/authorization.md)` is preserved and resolves.
- Unchanged in the same bullet: the `reservations.book_assets` requirement,
  exact-asset allowed-group eligibility (restricted with no allowed groups
  denies everyone), the one-time baseline grant migration, and the
  "New ordinary accounts receive NO automatic grants" guidance. The paragraph
  states no cross-user mutation surface and no user-directory API.

### 2. Booking truth in deployment

- Before (base `921f7a70`): `docs/deployment.md` operating-limits paragraph:
  "Authenticated humans have broad reservation access under policy rules;
  site groups do not implement project/membership or per-token asset
  restrictions."
- After (implementation head), one replacement sentence: "Creating a
  reservation requires the explicit `reservations.book_assets` grant, a
  group-restricted asset requires at least one allowed-group membership, and
  existing policy rules still apply; new accounts receive no automatic
  booking grant." The following sentence "Site groups do not implement
  project/membership or per-token asset restrictions" is preserved verbatim.
- No Staff/superuser reinterpretation and no project-membership assertion was
  introduced; the rest of the paragraph (shared privileged DB role,
  institutional OIDC, public forgotten-password reset, general notifications,
  workload execution/gateway/scheduler, SmartScheduling cutover, logged-in
  own-password change, SMTP-conditional onboarding email, imported-inventory
  caveat) is byte-identical to base, and the surrounding
  network/HTTPS/SMTP/operator-boundary sections are untouched.

### 3. Historical-pack index

- Before (base `921f7a70`): `docs/README.md` Operators index entry: "internal-
  network preparation pack; use INSTALL for the current Internet-facing
  boundary."
- After (implementation head): "historical/superseded internal-network
  planning template, not current operator guidance; current installation and
  deployment are in [INSTALL.md](../INSTALL.md)." The link target
  `runbooks/internal-alpha-pilot-preparation.md` still resolves; the pack
  itself is byte-unchanged (its 060-a HISTORICAL/SUPERSEDED banner remains the
  in-document marker); no other index entry was churned (the companion
  readiness entry, already relabeled in 060-a, is untouched).

### 4. Evidence / publication

- Docs-only diff: `git diff --name-only 921f7a70..de1c609b` is exactly
  `INSTALL.md`, `docs/README.md`, `docs/deployment.md`, `oap/active`,
  `oap/orders/061-a-current-operator-truth.md` — all order-allowed paths. No
  README/QUICKSTART/PLAN/ARCHITECTURE/CRITICAL/projection/authorization/API-
  contract/runbook byte changed; no application source, migration, test,
  fixture, dependency/lock, Docker/Compose/proxy, security-setting, API
  behavior or OAP helper/workflow byte changed.
- `git diff --check` at the implementation head: clean.
- Changed relative Markdown targets all resolve at the implementation head:
  `docs/README.md` -> `../INSTALL.md` (root INSTALL.md) and
  `docs/README.md` -> `runbooks/internal-alpha-pilot-preparation.md`;
  `INSTALL.md` -> `docs/authorization.md` (pre-existing, re-verified). No
  fragment anchors were introduced.
- Current absence-language scan of the three changed files: no remaining
  "broad reservation access", "cross-user read access) is not implemented"
  or stale index phrasing.
- Exact-head CI at `de1c609b9db6fce78279d3f36541d1fce3637587` (both workflow
  runs' `headSha` verified equal to the implementation head): CI run
  43000851682 (quality, test, security, container all PASS) and oap run
  43000851588 (oap-harness PASS) — all five checks PASS (see OAP-META
  `observed_implementation_ci`).
- Publication sequence per CP-05: implementation commit (docs + order file +
  `oap/active` pointer) committed and pushed; PR #127 created with
  `Closes #126` before this report; PR head verified
  `de1c609b9db6fce78279d3f36541d1fce3637587`, MERGEABLE, base `main`. This
  report is the only file changed in the report commit, whose first parent is
  the implementation head `de1c609b9db6fce78279d3f36541d1fce3637587`. No real
  relay/recipient, no identity administration, no deployment; CODING did not
  merge and no auto-merge is enabled. No foreign PR113 mutation.

## Uncertainty and limits

- Report-head CI: the report commit's exact-head checks were not yet observed
  at authoring (it does not exist yet); they run on the identical docs-only
  diff and must be observed before strategic merge review.
- A fresh independent full SAR-001..056 architecture-to-new-main ICA is
  required after merge before any milestone-closure claim; this documentation
  change does not self-certify (CP-07).
- The `INSTALL.md` section-13 documentation-map line lists "pilot preparation
  pack" generically among the `docs/runbooks/` contents; it is a directory
  listing, not one of the three ordered contradictions, and was left untouched
  (no churn). If strategy wants that line relabeled, that is a separate order.
- No local product test run was performed because no product code, runtime,
  dependency, test or Compose byte changed; the exact-head CI `test` job
  (full suite, PostgreSQL, browser) is green at the implementation head.

## Deferred human adjudication

- Decision: NONE
