<!-- OAP-META
{
  "kind": "report",
  "id": "048-a",
  "order_path": "oap/orders/048-a-authorization-foundation.md",
  "order_sha256": "026ada99f163fab3f7ee5a01688bcf4fd1fc86510c2059fa6e90e71e731f8e74",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 99,
  "pr_number": 100,
  "branch": "codex/99-oap-048-a-authorization-foundation",
  "implementation_head": "6b548eb465eb9fc679546c6c7c57c264a2f13432",
  "base_sha": "1baffe27a66609944f4d7b8e5c12dc69dfaa00b9",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "6b548eb465eb9fc679546c6c7c57c264a2f13432",
    "runs": [
      {
        "run_id": 39059948935,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      },
      {
        "run_id": 39059948927,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "test": "success",
          "security": "success",
          "container": "success"
        }
      }
    ]
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 048-a — authorization permissions and external identifier foundation

Implementation head SHA: 6b548eb465eb9fc679546c6c7c57c264a2f13432
Report publication commit: SELF

COMPLETE for the 048-a authorization foundation (D0). Branch
`codex/99-oap-048-a-authorization-foundation` from exact base
`1baffe27a66609944f4d7b8e5c12dc69dfaa00b9` (merged 047-a/PR98). PR #100 created
BEFORE this report with `Closes #99` in its body. Foundation only: permission
records, optional opaque account identifier, one-time existing-human booking
baseline, explicit chosen-staff setup command, docs and tests. NO endpoint/service
enforcement, no booking gates, no API surface, no deployment, no dependency or
bootstrap change. This is not target completion: enforcement, read-all interfaces
and qualification/fresh independent ICA are later purposes (049–052).

## Acceptance evidence

1. Ten A16 application permissions registered on the existing `Reservation`
   content type via `Meta.permissions` in
   `src/slaif_reservation/reservations/migrations/0003_reservation_application_permissions.py`
   (`AlterModelOptions` only; no field/schema/constraint/manager/lifecycle change).
   Exact codenames with human labels in the stable `reservations` namespace:
   `book_assets`, `view_all_reservations`, `cancel_others_reservations`,
   `release_others_reservations`, `view_booking_policies`,
   `manage_booking_policies`, `view_maintenance_blackouts`,
   `manage_maintenance_blackouts`, `view_audit_history`,
   `export_audit_history`. Groups and `user_permissions` reused; no new
   memberships, backends or hardcoded group names. New
   `src/slaif_reservation/accounts/authorization.py` provides the A16 constants and
   `has_reservation_permission`, checking an explicit capability for an active,
   authenticated, non-service-account human through Django permission machinery;
   no process-global permission cache (fresh per-call permission checks). Proven by
   `tests/test_authorization_foundation.py` (18 passed): helper positive/negative,
   group union, individual direct grant, no-grant denial, inactive denial,
   service-account denial, staff-without-grant denial, active-human superuser
   semantics preserved; protected-record boundaries unchanged. No endpoint/service
   enforcement wired anywhere in this change.
2. `User.external_identifier` added by
   `src/slaif_reservation/accounts/migrations/0005_user_external_identifier.py`:
   optional opaque case-sensitive `CharField(max_length=128)`, `NULL` when
   unassigned, database-unique when populated (PostgreSQL allows multiple NULLs),
   no format restrictions or normalization (numeric-looking strings and leading
   zeroes preserved exactly; never parsed as integers or given Linux meaning).
   Existing accounts migrate to NULL, never inferred. Empty admin input clears to
   NULL (verified empirically against real PostgreSQL: form submits empty ->
   stored NULL, no unique-blank collision). Proven by `tests/test_accounts.py`
   (8 passed, including 6 new external-identifier tests: fresh/persist/reload,
   leading zeroes, case and length and duplicate rejection, multiple NULL,
   clearing/reassigning) on real PostgreSQL constraints.
3. Field exposed ONLY in the existing authorized User administration
   (`src/slaif_reservation/accounts/admin.py`): meaningful label, bound visible
   help text, associated form field; admin-only editing remains governed by the
   existing staff admission gate and per-model account-change permissions. NOT
   added to member `ProfileForm`, bearer serializers, `/me`, or any new
   directory/API surface. Proven: forged member-profile and bearer requests cannot
   modify the field (rejection tests in `tests/test_authorization_foundation.py`),
   ordinary profile values and UUID/email/password/token identity preserved;
   nonstaff and staff-without-account-change cannot change it; protected
   tokens/reservations/policies/audits remain protected and no
   credentials/verifiers rendered. `docs/ux/form-guidance-inventory.md` gained the
   new account form row. Real Chromium (`tests/browser/test_authorization_admin_browser.py`,
   1 passed): authorized admin edit, read-only denial, accessible associated help at
   desktop 1440 and mobile 390; 2 privacy-safe screenshots actually inspected
   (synthetic test account only; no stored password/token/CSRF/verifier values; no
   horizontal overflow; password status shown as "Password set."). No new-user
   automatic permission/group assignment anywhere; the booking-grant setup is
   documented now and the later enforcement order will make it mandatory in account
   help.
4. Forward migrations only, exactly the allowed-path names. Reservation model
   change is `Meta.permissions` ONLY; account schema change is
   `external_identifier` ONLY. One-time data migration (in `accounts/0005`,
   `RunPython`) adds ONLY `book_assets` to existing non-service-account users,
   including inactive rows (later normal reactivation preserves the former
   baseline); it resolves the permission via historical apps/dependencies at the
   migration boundary (no current-model import), no management/read-all grants, no
   group creation/membership changes, no service-account grants, no
   post_migrate/startup signal/create_user auto-enrolment. Proven by
   `tests/test_authorization_upgrade.py` (1 passed): executes on real owned
   PostgreSQL 17 from a populated historical `accounts/0004` + `reservations/0002`
   state (existing users with direct and group grants, tokens, reservations,
   audits, assets) to the current leaf; snapshots meaningful old rows (no secrets
   printed) and proves preserved row identity/content, exact baseline-grant scope,
   idempotence (re-run grants nothing new), unassigned identifiers, and that users
   created AFTER the migration receive no auto-grants; migration state restored in
   teardown. Documented honestly in `docs/authorization.md`: reverse/downgrade does
   not silently revoke operator-configured grants and Git rollback does not restore
   identity data; a real upgrade requires operator backup/restore planning.
5. `grant_management_access` command
   (`src/slaif_reservation/reservations/management/commands/grant_management_access.py`):
   repeated required `--user` UUID arguments selecting existing active
   non-service-account staff accounts; dry-run by default; `--apply` adds the nine
   A16 management/read-all capabilities (all ten except `book_assets`) directly to
   the selected users only. Does not create users, change staff/superuser flags,
   groups, or remove existing grants. Missing/malformed/nonexistent, nonstaff,
   inactive or service-account selections refuse; EVERY selection is validated
   before ANY write (mixed valid/invalid batch refuses with zero writes); applies
   atomically and idempotently, rolling back on failure. Dry-run writes nothing
   (no audit/setup side effects). Prints safe action/count/capability summaries —
   public UUIDs only, no emails, identifiers or secrets. Documented in
   `docs/authorization.md` as direct application grants, not implicit `is_staff`
   authority, with superuser/per-model Administration semantics separate; never
   grants future users/staff and creates no default privileged group. Proven by
   4 dedicated command tests in `tests/test_authorization_foundation.py`
   (dry-run no-op, apply exact nine capabilities, idempotent re-apply, mixed
   valid/invalid batch validation-before-write).
6. `docs/authorization.md` now distinguishes IMPLEMENTED foundation (field,
   permission records, explicit setup command) from NOT YET IMPLEMENTED
   enforcement/read-all interfaces; it explains baseline grant scope,
   new-user group/individual setup, the explicit chosen-staff dry-run/apply
   upgrade steps and backup/reverse limits, with no fake existing endpoint/scope
   promises; the permission matrix, exact-asset and external-enforcer boundaries
   and remaining target obligations are preserved. Root projection
   `ARCHITECTURE-for-agents.md`: only the stale temporal status sentences were
   changed to mark contract-time observations and refer to ordered implementation
   evidence; every normative SAR/A16 clause is preserved and the full-source
   architecture digest remains
   `4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd` (full
   architecture unchanged). No broad redistillation; no work-order ledger in
   product docs; staff/group help describes CURRENT enforcement only.
7. Verification (focused, owned environment; `OAP_ROLE` unset for every test
   process including role-simulation harness fixtures):
   - Focused pytest on owned Python 3.13.14 + PostgreSQL 17 + Chromium:
     `uv run pytest tests/test_authorization_foundation.py
     tests/test_authorization_upgrade.py tests/test_accounts.py
     tests/test_form_guidance.py` -> 59 passed (18 + 1 + 8 + 32; 0 failed/
     skipped/error). `uv run pytest
     tests/browser/test_authorization_admin_browser.py --output <owned>` -> 1
     passed. No other existing admin/privacy test actually exercises the changed
     User-admin surface (verified by inspection), so none were added to the
     focused set.
   - `ruff check src tests`: All checks passed. `ruff format --check`: 215 files
     already formatted. `mypy src`: Success, no issues in 137 source files.
     `manage.py check` (test settings): no issues. `makemigrations --check
     --dry-run`: No changes detected. Changed-doc link check over the three
     changed Markdown files: 0 relative links present, nothing broken. `git diff
     --check`: clean.
   - OAP stdlib harness: `env -u OAP_ROLE python -m unittest discover -s tests/oap
     -p 'test_*.py'` -> Ran 160 tests, OK.
   - Normal full CI at exact implementation head
     `6b548eb465eb9fc679546c6c7c57c264a2f13432` (observed): CI run 39059948927 —
     quality pass (13s), security pass (12s), container pass (31s), test pass
     (10m14s; full suite including operational/HTTPS/restore/Gunicorn
     regressions); oap run 39059948935 — oap-harness pass (37s). All five required checks success,
     none missing/skipped/cancelled.
   - No bespoke HTTPS/Gunicorn/restore/whole-visual requalification of unchanged
     paths outside normal CI (see environment section below for the honest record
     of an earlier local detour).

## Changed paths (implementation commit 6b548eb on top of order commit 45d6a71)

Order commit `45d6a71`: `oap/orders/048-a-authorization-foundation.md` (exact
order bytes, +145) and `oap/active` (`048-a` byte-for-byte; +1/-1).
Implementation commit `6b548eb` (14 files, +1838/−111), all within
allowed_paths:
`ARCHITECTURE-for-agents.md`, `docs/authorization.md`,
`docs/ux/form-guidance-inventory.md`, `src/slaif_reservation/accounts/admin.py`,
`src/slaif_reservation/accounts/authorization.py`,
`src/slaif_reservation/accounts/migrations/0005_user_external_identifier.py`,
`src/slaif_reservation/accounts/models.py`,
`src/slaif_reservation/reservations/management/commands/grant_management_access.py`,
`src/slaif_reservation/reservations/migrations/0003_reservation_application_permissions.py`,
`src/slaif_reservation/reservations/models.py`,
`tests/browser/test_authorization_admin_browser.py`, `tests/test_accounts.py`,
`tests/test_authorization_foundation.py`, `tests/test_authorization_upgrade.py`,
`tests/test_form_guidance.py`. No dependency/lockfile, bootstrap, migration bytes
beyond the two new forward files, deployment or protected-boundary change.
`git diff --check`: clean.

## Owned environment and receipts

- Owned nonce root `/home/janezp/codex-work/slaif-auth-048-922064` (mode 0700,
  nonce 922064). Pinned uv 0.11.23 + locked Python 3.13.14 installed locally in
  the owned root; owned virtualenv at `<root>/source/.venv`.
- Owned PostgreSQL 17 Docker container `slaif-auth-048-922064`, exact CID
  `7680db038ecebff114a19a929c6b2e3800d7274b23254a41707c2873d7c4067d`, image
  `postgres:17@sha256:d13db94ae661d517c5ed57c509a578d5ea64aae639871ba25294f4f42d83de28`,
  127.0.0.1 loopback ephemeral port 22708 (receipt `<root>/db-receipt.txt`;
  credentials in mode-0600 files, never printed here).
- Owned disposable source copy `<root>/source`: only Git-listed non-ignored files
  synced from the dev checkout (verified byte-identical via md5 over all 576
  listed files before the focused runs); no valuable .env/deployment paths. No
  Git history was manufactured in this copy.
- Chromium in `<root>/browsers` with
  `PLAYWRIGHT_HOST_PLATFORM_OVERRIDE=ubuntu24.04-x64` and
  `PLAYWRIGHT_BROWSERS_PATH=<root>/browsers` (local qualification limitations,
  not product dependencies); artifacts under `<root>/browser-artifacts`.
- Sequential pytest processes only; no foreign container was touched
  (`slaif-asset-reservation-app-1`, `slaif-asset-reservation-db-1`,
  `slaif182a-pg-*`, `slaif-rs-*` all untouched).

## Environment/unrelated local evidence (not product qualification)

Before the STRATEGIC clarification of 2026-10-17, an extra LOCAL full-suite
attempt was made against the owned disposable source copy (which, by design,
carries no Git metadata). It reached only unchanged deployment/operational tests
and failed for environment reasons outside this order's scope:
`test_https_boundary` requires Caddy 2.11.6 (host has 2.11.7);
`test_restore_drill` requires `pg_dump` (absent on host); the
`test_operational_hardening` rehearsal tests require Git metadata in the copy and
were additionally blocked by an unrelated foreign 5-day pilot compose stack on
the host; `test_qualification_image_ownership` is a known mtime flake;
`pilot_path[chromium]` errors without
`PLAYWRIGHT_HOST_PLATFORM_OVERRIDE`. These are source-copy/test-environment
boundary evidence, NOT demonstrated product defects and NOT product
qualification. Per the STRATEGIC clarification that order's acceptance 7 /
non-goals are restored: the required full suite is the normal FULL CI on the real
PR checkout (observed green above, including the operational/HTTPS/restore/
Gunicorn regressions). Those tests and their helpers were not altered, no
Caddy/pg_dump was installed, no synthetic Git was initialized for them, and no
local full pytest run was repeated after the clarification.

## Uncertainty, privacy, dependencies, DHA, limits

- Report-head CI is not observed at authoring; strategy observes it after this
  immutable report is published. Implementation CI is separately recorded above.
- No credentials, private artifacts or sensitive data in this report; test
  evidence uses synthetic values only (e.g. `auth048-member@example.com`).
- No CRITICAL mutation; DHA per the order's deferred adjudication:
  `Decision: NONE`. No product milestone acceptance, release or deployment
  authorization; no ICA claim — the SAR-048..SAR-053 foundation stays UNPROVEN
  until the later enforcement orders and a fresh independent ICA at the exact
  merged revision.
- Limits: local verification was focused (order acceptance 7) plus the OAP
  harness; full-suite qualification rests on normal CI at the implementation
  head, which is the required full suite for this order.
