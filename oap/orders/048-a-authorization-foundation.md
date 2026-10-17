<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "048-a",
  "objective": 48,
  "round": "a",
  "slug": "authorization-foundation",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "1baffe27a66609944f4d7b8e5c12dc69dfaa00b9",
  "issue_number": 99,
  "branch": "codex/99-oap-048-a-authorization-foundation",
  "pr_mode": "CREATE_OR_RESUME",
  "pr_number": null,
  "previous_round": null,
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd",
    "PLAN.md": "2c856ae47ec985b953a8d26edbe2c07fd343833a41bc45aefcd304a7e67c1432",
    "ARCHITECTURE-for-agents.md": "fa3f9e5ffd4a466fb727c42145a6671a249dd959c5320e9b35fbc414eccbe4cb",
    "oap/coding-instructions/AGENTS.md": "1611e9700de5b311deeb45460162464f7f24462e74790dddfcec2bb016b30394"
  },
  "requirements": [
    "SAR-001",
    "SAR-007",
    "SAR-009",
    "SAR-011",
    "SAR-012",
    "SAR-014",
    "SAR-015",
    "SAR-018",
    "SAR-021",
    "SAR-026",
    "SAR-027",
    "SAR-032",
    "SAR-034",
    "SAR-035",
    "SAR-037",
    "SAR-038",
    "SAR-048",
    "SAR-052",
    "SAR-053"
  ],
  "allowed_paths": [
    "src/slaif_reservation/accounts/models.py",
    "src/slaif_reservation/accounts/admin.py",
    "src/slaif_reservation/accounts/authorization.py",
    "src/slaif_reservation/accounts/migrations/0005_user_external_identifier.py",
    "src/slaif_reservation/reservations/models.py",
    "src/slaif_reservation/reservations/migrations/0003_reservation_application_permissions.py",
    "src/slaif_reservation/reservations/management/commands/grant_management_access.py",
    "tests/test_authorization_foundation.py",
    "tests/test_authorization_upgrade.py",
    "tests/test_accounts.py",
    "tests/test_form_guidance.py",
    "tests/browser/test_authorization_admin_browser.py",
    "docs/authorization.md",
    "docs/ux/form-guidance-inventory.md",
    "ARCHITECTURE-for-agents.md",
    "oap/active",
    "oap/orders/048-a-authorization-foundation.md",
    "oap/reports/048-a-authorization-foundation.md"
  ],
  "forbidden_resources": [
    "Reservation scheduling/service/policy/exclusion/lifecycle/audit/idempotency/authentication/proxy/network/deployment behavior changes",
    "Existing merged migration bytes; inventory/bootstrap data; dependencies/lockfile; protected Administration boundary changes",
    "OAP helper/constitution/workflow/framework changes; full architecture/PLAN or historical reports/orders/coverage/bootstrap rewriting; CRITICAL mutation",
    "Real credentials/data/host/DNS/TLS/firewall/private exports/lab/execution; foreign resource cleanup; auth-home copying",
    "Other objective/PRs, merging or auto-merge, further delegation"
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human authorization extension2026-10-17 \u00a7\u00a72,7,10,11 and explicit OAP/CODING clarification",
      "section_or_evidence": "Reuse existing groups/individual grants; optional opaque unique identifier; deliberate preservation/setup and meaningful tests; bounded separate coding contexts."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE A16; SAR048/052/053; PLAN P08",
      "section_or_evidence": "Ten named application permissions, active-human/superuser rules,128character opaque identifier, one-time existing-human booking baseline, explicit chosen-staff setup; no future autoenrolment."
    },
    {
      "marker": "E",
      "source": "Merged047-a/issue97/PR98 and source inspection",
      "section_or_evidence": "Exact report5edd535/implementation546cdaa all5CIgreen, merged1baffe27; custom User UUID/email/permissions existing, latestaccounts0004/reservations0002; no externalID/custom app grants yet."
    },
    {
      "marker": "I",
      "source": "STRATEGIC frozen047 review and live local diagnostics",
      "section_or_evidence": "Source/projection semantic contract accepted; routinebytebudget revision40000projection/60000total documented privately and PRreview. Broken oldvenv/system3.14; ownedlocked3.13/PG tests required; env-uOAP_ROLE for harness."
    },
    {
      "marker": "C",
      "source": "CRITICAL register; human and A16 explicit decisions",
      "section_or_evidence": "No new unresolved product/risk dilemma. Ordinary additive schema/setup D0 with backup/rollback limitations; no real migration/deployment. NONE."
    }
  ],
  "decision_class": "D0",
  "target_gate": "Authorization foundation for continued development only; complete selected authorization milestone requires later enforcement/read-only interfaces/qualification/fresh independent ICA; no deployment",
  "expected_report_path": "oap/reports/048-a-authorization-foundation.md",
  "tests": [
    "focused real PostgreSQL account/custompermission/opaqueID/admin/setup tests, populated pre-upgrade MigrationExecutor preservation and no-future-autogrant tests",
    "member profile and bearer forged identifier-write refusal/preservation; existing account/admin protected-record and secret regressions",
    "real Chromium admin update/read-only denial and desktop1440/mobile390 accessible help/privacy-safe screenshots actually inspected (at most a few images per context)",
    "Ruff lint/format, mypy, manage.py check/makemigrations --check --dry-run, changed Markdown links, git diff --check, full160 OAP stdlib tests with OAP_ROLE unset",
    "normal full CI once at final implementation head plus path-gated oap-harness; preserve report-head checks and exact report-only publication; no unrelated bespoke qualification"
  ]
}
-->

#048-a — authorization permissions and external identifier foundation

## Goal and prerequisites
One implementation purpose: supply the existing-group permission and account-identity foundation for selected A16. Issue99; exact base1baffe27a66609944f4d7b8e5c12dc69dfaa00b9 is merged047-a/PR98. Its implementation and report heads passed allfive checks; merged-main pushCI may still be running and is not claimed passed.046/047 are completed, never replayed. Current coding wrapper is already in righttmux%3 and will launch a fresh context for this order. No accumulated images or prior-context assumption.

Do NOT switch management/booking enforcement, introduce asset restrictions, token read-all scopes or cross-user routes here. Those are separate purposes049–051. At this foundation stage existing workflows remain as before except the new optional account field and explicit permission setup. Document this precisely; no claim that the whole target is implemented.

## Ordered compact read set
C04 standard read set, then only: accounts/models.py User (and token protection definitions for preservation); accounts/managers.py; accounts/admin.py UserAdmin/get_form/help and GroupAdmin; reservations/models.py Reservation.Meta options only; current accounts0004/reservations0002 migration dependencies; tests/test_accounts.py and relevant admin guidance assertions in tests/test_form_guidance.py; existing browser admin login/accessible-surface helpers in tests/browser/test_form_guidance_browser.py and test_slaif_design.py only as needed. docs/authorization.md; docs/ux/form-guidance-inventory.md account rows. Read bounded local test notes at ~/codex-supervision/slaif-asset-reservation/workorders/group-authorization-runtime-20261017/local-testing.md. Full architecture/PLAN/history/source books are NOT routine reads. The compact projection carries A16 directly. Source hashes bind pre-edit base; preserve old norm clauses.

## Scope and acceptance criteria
1. Register the TEN A16 application permissions on the existing Reservation content type through normal model Meta/migration state, with useful human labels and stable reservations namespace. Exact codenames: book_assets,view_all_reservations,cancel_others_reservations,release_others_reservations,view_booking_policies,manage_booking_policies,view_maintenance_blackouts,manage_maintenance_blackouts,view_audit_history,export_audit_history. Reuse Django groups and user_permissions, not new memberships/backends or hardcoded group names. Introduce a small accounts/authorization.py constants/helper module to check an explicit capability for an active authenticated non-service-account human via Django permission machinery. Groups combine additively and direct grants survive; staff/old Administration View do not imply these application grants. Preserve trusted active human superuser has_perm semantics, with protected-record boundaries unchanged. Do not wire endpoint/service enforcement in this order. No process-global permission cache; callers later use fresh per-request/locked principals. Prove helper/group union/individual/no-grant/inactive/service/staff/superuser cases.
2. Add optional User.external_identifier, opaque case-sensitive string, maximum128characters, default/unassignedNULL, populated values database-unique, multiple users unset. Existing accounts migrate toNULL, never infer identifiers. Preserve numeric-looking strings and leadingzeroes; do not parse as integers or infer Linux meaning. Empty admin input clears toNULL; ordinary create/update paths must handle unset consistently without unique-blank collisions. No gratuitous format restrictions or whitespace/case normalization of populated opaque identifiers. Test fresh/persist/reload,leadingzeroes,case/length/duplicate rejection,multipleNULL and clearing/reassigning, with actual PostgreSQL constraints.
3. Expose the optional field in existing authorized User administration with meaningful label/help and accessible association; admin-only editing remains governed by existing staff admission/per-model permissions. Do not add it to member ProfileForm, bearer serializers/me responses or any new directory/API surface. Forged member profile/bearer requests cannot modify it; preserve ordinary profile values and UUID/email/password/token identity. Nonstaff and staff without account-change permission cannot change it. Protected tokens/reservations/policies/audits remain protected and credentials/verifiers are not rendered. Add the field to admin account form guidance inventory. New-user automatic permission/group assignment is forbidden; required booking-grant setup is explained in the guide now, and the later booking-enforcement order makes it mandatory in the relevant account help.
4. Add only forward migrations named in allowed_paths. Reservation model changes are Meta.permissions ONLY: no field/schema/constraint/manager/lifecycle edits. Account schema changes are external_identifier ONLY. Provide a one-time data migration that adds ONLY book_assets to existing non-service-account users (including inactive rows, so later normal reactivation preserves their former baseline); no management/read-all grants, no group creation/membership changes, no service-account grants. Existing direct/group permissions and every existing user/reservation/policy/audit/token/asset row identity/content remain unchanged apart from that exact added booking grant and newNULLfield. Django post_migrate normally creates permissions after data migrations; explicitly ensure the new book permission exists safely at the migration boundary using historical apps/dependencies rather than importing current models. Running normal migrate again must not grant newly created accounts or duplicate permissions/grants. No post_migrate/startup signal or create_user auto-enrolment. Tests execute from populated historical accounts0004/reservations0002 to current leaf migrations, snapshot meaningful old data (including existing direct/group grants and token/reservation/audit records without printing secrets), and prove preserved rows,baselinegrant scope,idempotence,unassignedIDs and no subsequent-user autogrants. Restore migration state safely in test finally/teardown; use real owned PostgreSQL,notSQLite/mocked migration executor. Document reverse/downgrade implications honestly: do not silently revoke operator-configured grants or claim Git rollback restores identity data; real upgrade requires operator backup/restore planning.
5. Add grant_management_access management command for explicit legacy-staff setup. Exact interface: repeated required --user UUID arguments selecting existing active non-service-account staff accounts, dry-run by default, --apply to add the nine A16 management/read-all capabilities directly to those selected users (all ten except book_assets). Do not create users, change staff/superuser flags, change groups or remove existing grants. Existing baseline booking grant is separate. Missing/malformed/nonexistent user, nonstaff, inactive or service account selection must refuse; validate EVERY selection before ANY write, including mixed valid/invalid batch; apply atomically, idempotently, and roll back on failure. Dry-run writes nothing, including no audit/setup side effects. Print safe action/count/capability summaries, no credentials/emails/raw identifiers beyond entered public UUIDs, no secret-bearing diagnostics. Document these are direct application grants, not implicit is_staff authority, and superuser semantics/per-model Administration access are separate. Never grant all future users/staff or add a default privileged group. Existing Administration changes use the framework's permission controls; do not invent a new account-management API or audit framework.
6. Update docs/authorization.md to distinguish IMPLEMENTED foundation (field,permission records,explicit setup command) from NOT YET IMPLEMENTED enforcement/read-all interfaces. Explain baseline grant scope, new-user group/individual setup, explicit chosen-staff dry-run/apply upgrade steps and backup/reverse limits; no fake existing endpoint/scope promises. Preserve the permission matrix, exact-asset and external-enforcer boundaries and remaining target obligations. Ordinary product docs remain product-first; no work-order ledger. Current root projection absolute sentence "no capability/field/etc exists yet" becomes stale once this order implements fields/permissions: change only those temporal status sentences to mark initial contract-time observations and refer to ordered implementation evidence; preserve every normative SAR/A16 clause and the full-source architecture digest (full architecture does not change here). No broad redistillation or budget/harness/governance work. Any truthful transitional staff/group help changes must describe CURRENT enforcement, not announce future behavior as existing.
7. Verify focused server/migration/command/admin tests and positive/negative browser path. Real Chromium admin edit/help at1440and390, actually view at most a few privacy-safe screenshots (avoid stored password/token/CSRF/verifier values); ensure no horizontal overflow, visible associated help and unauthorized forms/refused writes. Reuse established styling/test helpers; no redesign or16-image batch. Existing account and form-guidance tests remain meaningful; adjust only assertions affected by this new field/status, never weaken auth/validation coverage. Run Ruff/mypy/check/makemigrations --check --dry-run/changedlinks/git diff --check and OAP stdlib harness (env -u OAP_ROLE). Use focused tests while editing; normal full CI once at final implementation head, repair only demonstrated in-scope failures. Keep all five required jobs and truthful report-head separation. No bespoke HTTPS/Gunicorn/restore/wholevisual requalification for unchanged paths outside normal CI. Diagnose unrelated known flakes before any retry; do not change unrelated helper logic.

## Environment and resource boundaries
Use the bounded private local-testing.md notes. Python3.14 system and old .venv symlink are NOT the product test environment. Install pinned uv/lockedPython3.13 locally in an owned nonce root; create an owned PostgreSQL17 local Docker container with exact CID/nonce receipts and loopback ephemeral port. Copy only Git-listed nonignored source to an owned disposable checkout; sync final allowed edits before tests; no valuable .env/deployment paths. Sequential pytest processes only. No real DB/secrets/data/host/firewall/TLS/DNS/lab actions. Browser override/extracted libs are local qualification limitations, not product dependencies. Response FIFO is ~/codex-supervision/slaif-asset-reservation/response.fifo; use its existing qualified helper, no process-wide or /tmp searches. Source codex.sh is already handled by the client wrapper; do not start other agents.

## Non-goals and strongest reason not to change
No reservation-engine/policy/exclusion/lifecycle/API/authentication/abuse/proxy/network/defaultpolicy changes. No booking-group enforcement or management gates/scopes yet; no scope auto-expansion on old tokens. No dependency/runtime/asset/bootstrap changes, projects, ownership trees, Linux/PAM/SSH/execution or external enforcer implementation. Strongest objection: a migration/setup bug could silently privilege users or break upgrades; narrowly assign existing-human booking baseline only, require explicit selected-staff apply, validate batches before writes, prove populated upgrade preservation and future-user non-enrolment. This foundation is not target completion. Unknown consequential conflict goes to strategy; routine implementation mechanics D0.

## Recovery, publication and reporting
Operate only exact branch codex/99-oap-048-a-authorization-foundation from actual base above. Current047 branch and unused maintenance branch are preserved; never reset/clean/stash/force-push. Include exact order/active bytes. Include Closes #99 in PR body; use structured body/file, not interpolated shell strings. Create/amend the actual PR BEFORE report; wait outside model for CI with existing gh watch helpers. Capture literal full final implementation head after observed checks, then commit ONLY immutable oap/reports/048-a-authorization-foundation.md with that implementation head as first parent. Literal lines:
Implementation head SHA: <actual full object ID>
Report publication commit: SELF
Record acceptance per number, exact commands/counts/errors/skips/limits, changed paths, ownedresource receipts/cleanup and no credential artifacts; separate observed implementation CI from report-head CI NOT YET OBSERVED AT AUTHORING. Push, verify remote PR/head/orderhash/report/parent/report-only paths via helper, signal responseFIFO exact two bytesOK, then stop mutation. Never merge, self-approve, enable auto-merge, publish another order or delegate. Strategy owns review and subsequent activation. No ICA/deployment claim.

## Deferred human adjudication
- Decision: NONE
