<!-- OAP-META
{
  "kind": "report",
  "id": "050-a",
  "order_path": "oap/orders/050-a-granular-management-authority.md",
  "order_sha256": "dfb0233cbb03333bfc6d42340a91db547c1e406e0c8ad10ce5e630ee331dee12",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 103,
  "pr_number": 104,
  "branch": "codex/103-oap-050-a-management-authority",
  "implementation_head": "95d29b82ca1ff3581f3b0647fbf335b58db2b019",
  "base_sha": "b873f4cf1071bded044ba456625b0ced355407a8",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "95d29b82ca1ff3581f3b0647fbf335b58db2b019",
    "runs": [
      {
        "run_id": 39086341421,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "success",
          "container": "success",
          "test": "success"
        }
      },
      {
        "run_id": 39086341485,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1207 passed, 1 warning in 598.03s (0:09:58)",
    "warning": "tests/test_product_entry.py:568 UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unrelated)",
    "oap_harness_summary": "Ran 160 tests in 30.887s / OK"
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 050-a — execution report: granular management authority and the All reservations browser

Implementation head SHA: 95d29b82ca1ff3581f3b0647fbf335b58db2b019
Report publication commit: SELF

## Identity and result

COMPLETE for order 050-a (D0) on the A16/SAR-048/SAR-050/SAR-053
granular-management-authority slice. Order
`oap/orders/050-a-granular-management-authority.md` (state FINAL; current
file digest sha256
`dfb0233cbb03333bfc6d42340a91db547c1e406e0c8ad10ce5e630ee331dee12`), repo
`ulfe-lmi/slaif-asset-reservation`, issue #103, branch
`codex/103-oap-050-a-management-authority`, base main
`b873f4cf1071bded044ba456625b0ced355407a8` (accepted merged PR #102 tree).
Actual PR number retrieved at publication: **104** (order `pr_number` remains
`null` in the immutable order file); PR #104 is OPEN on the exact branch and
its body ends with `Closes #103`. The order's seven `source_hashes` bindings
were recomputed as SHA256 of `git show b873f4cf1071bded044ba456625b0ced355407a8:<path>`
file bytes (not Git object IDs) and all match the order exactly
(ARCHITECTURE.md 4566e797…, PLAN.md 2c856ae4…, ARCHITECTURE-for-agents.md
41c32e0b…, accounts/authorization.py d1b0879f…, management_ui/auth.py
3127bd69…, management_ui/views.py 818f6371…, reservations/services.py
fcba3066…); strategy verified zero byte mismatches between canonical and
owned-copy source at publication. No merge, no auto-merge, no self-approval,
no CRITICAL mutation, no deployment, no real user/data/DB/host/secret work.

## Acceptance evidence

1. **One additive capability system and exact route inventory — PASS.**
   `src/slaif_reservation/accounts/authorization.py` now defines the nine
   `MANAGEMENT_PERMISSIONS` (all ten `reservations.*` codenames minus
   `book_assets`); `is_staff` alone admits only /admin/,
   `is_management_user` means any of the nine (NOT staff), and
   `book_assets` alone grants no management access. Superuser `has_perm`
   semantics retained; Administration still staff + per-model; protected
   records remain read-only. New small shared helper
   `web/templatetags/application_access.py` (`has_permission`,
   `has_any_permission`, `management_user`) derives booleans only. All 17
   current /manage/ routes and operation guards are inventoried with the
   order's exact matrix in `docs/authorization.md`
   ("Management route inventory (enforced)"). Proven by
   `tests/test_management_authorization.py` (real Permission rows, owned
   PG/HTTP/service calls): non-staff single-capability, no-cap,
   staff+unrelated-model-view-without-management-grant denied, combined
   groups + direct grants union, grant removal while the session is valid,
   inactive and service principals (including superuser variants) denied,
   anonymous login redirect, authenticated-without-cap 403, and direct
   GET/POST cannot be authorized by a hidden button.
2. **Shared mutation authority, not adapter-only checks — PASS.**
   `reservations/services.py` replaces the blanket staff lock with
   `_lock_capable_actor(actor, codename)`: create/update/deactivate policy
   requires `manage_booking_policies`, create/deactivate blackout requires
   `manage_maintenance_blackouts`, read from the fresh row-locked actor with
   transaction/lock order, full clean, protected write and audit coupling
   preserved. `cancel_reservation`/`release_reservation` permit the active
   human OWNER or the explicit `cancel_others_reservations` /
   `release_others_reservations` capability; service-account ownership or
   superuser never bypasses active-human eligibility. Bare read-all is never
   a mutation grant; manage-policy and manage-blackout do not imply one
   another. No generic reservation lock order, booking gate, counter,
   exclusion, time, policy math or idempotency internal changed. Tests prove
   post-revocation locked rechecks, wrong-mutation-cap denials (cancel vs
   release, policy vs blackout), retained conflict/cutoff/blackout/exclusion
   invariants and audit rollback, and owner lifecycle fully independent of
   `book_assets`/asset-group eligibility after its loss (real PG concurrency
   suite re-run green).
3. **Useful partial-access UI with no incidental disclosure — PASS.**
   `web/templates/web/base.html` nav separates the Management capability
   link from the staff-only Administration link and offers **All
   reservations** as a separate `<nav id="cross-user-navigation">` landmark
   distinct from My reservations (this resolves the
   `tests/browser/test_slaif_design.py` aria-current regression within the
   allowed base.html without touching navigation.js; the existing assertion
   is preserved and the focused design suite passes). Dashboard and `_nav`
   render only authorized modules/counts and never fetch or pass
   unauthorized counts; a mutation-only principal without read-all can
   submit an authorized action by known UUID but is safely redirected to the
   permitted management landing (no private detail redirect, generic
   message, no owner/free-text/record data). Partial access is explained in
   the dashboard. Policy/blackout view-only roles see no editor/deactivate
   controls; read-all-only sees no cancel/release forms. An
   `export_audit_history`-only user gets a usable existing AuditFilterForm on
   the management dashboard to download bounded CSV; audit-reader-only sees
   no export and direct export is 403. Proven by the new server and browser
   negative suites (no unauthorized counts, buttons, links, record DOM or
   redirect leakage).
4. **All reservations browser on existing routes — PASS.**
   `/manage/reservations/` and the detail view keep their URLs, are labelled
   All reservations / Reservation details, and require
   `view_all_reservations` only (model `view_reservation` alone is denied,
   staff included). Existing validated asset/status/lifecycle/search/aware
   from/to filters are reused with Paginator 50 and visible previous/next/
   page navigation that preserves all filters (the template previously had
   no links). Pagination with >50 matching synthetic records, invalid-filter
   empty/error behavior, and bounded output are tested. Detail shows owner
   (existing browser display identity), asset, original start/end,
   effective end, current status and `derive_lifecycle` with the existing
   half-open release/cancel history meaning; no email/profile/physical
   locator/secret expansion. A read-only viewer cannot mutate others even
   through a valid forged CSRF POST (403, no change); owner, member and API
   selectors remain owner-only even for a principal holding all management
   capabilities.
5. **Blackout preview privacy — PASS.**
   `reservations/services.py`
   `overlapping_blocking_reservations_queryset` gives a blackout
   viewer/manager WITHOUT read-all only the safe overlap count/confirmation
   needed to confirm a nonzero overlap and the released-prefix block; no
   affected row objects, UUIDs, names, emails, purposes, free text or
   private links reach HTML, hidden fields or redirects. With
   `view_all_reservations` the existing full affected list/links render.
   Creation/deactivation audit and no-automatic-reservation-rewrite are
   preserved. Tests exercise create-unconfirmed, confirmed-create and
   detail-read paths with privacy canaries and a forged-row/false-confirm
   bypass attempt. Audit export authority stays separate with the existing
   500-row/7-day/safe-CSV bounds and no token/credential/header/request/
   private-payload/locator/purpose/cancellation-reason columns.
6. **Deliberate upgrade and current help/docs — PASS.**
   No new migrations, permissions or default grants
   (`manage.py makemigrations --check --dry-run`: No changes detected).
   Existing 048 `grant_management_access` remains the dry-run-first,
   idempotent, explicit active-human selection path. `accounts/admin.py`
   help text now states the enforced semantics: Staff = Administration
   admission only, group/individual application grants are active,
   superuser/human boundaries; all admin model-permission, protected
   mutation, password and UID logic preserved; protected-record guidance
   names the application permissions needed without linking unavailable
   modules. Docs updated only where now-false: `docs/authorization.md`
   (concrete 17-route matrix, example operator groups, deliberate upgrade
   steps before returning service to users, non-staff individual/group
   grant examples), `README.md`, `INSTALL.md`, `docs/human-ui.md`,
   `docs/security-model.md`, `docs/runbooks/management-blackouts.md`,
   `docs/ux/form-guidance-inventory.md`, `docs/README.md` index text. No
   ledger/chronology/new ADR; Compose project names, secrets, proxy,
   database and deployment boundaries retained; accounts are not
   auto-added to privileged groups; bearer read-all/scope issuance remains
   the separate planned 051 contract, owner API unchanged.
7. **Meaningful positive + negative evidence — PASS.**
   New `tests/test_management_authorization.py` (17 tests) with real
   Permission rows and owned PG/HTTP/service calls maps ALL 17 routes and
   GET/POST actions: valid payloads/CSRF, no hidden-action bypass,
   view-only read/mutation denials, wrong-mutation-cap denials,
   mutation-only success without read-all plus safe redirects and no
   unauthorized DOM, superuser/staff/service/inactive semantics, and the
   shared locked service guards after revocation. Existing owner bearer
   read/mutation stays owner-only even for superuser/staff/all-caps.
   Affected concurrency, import-lock, restore and policy suites reused and
   green to preserve lock/backup behavior.
8. **Existing positive fixtures, narrow adaptations — PASS.**
   Every real management mutation call site was inventoried before editing;
   only legitimate old management actors received explicit real application
   permissions (dedicated full-manager fixtures intentionally grant all
   nine; a staff flag by itself is not a grant; `user_permissions.add()`
   receives unpacked `*Permission.objects.filter(...)` per this Django
   version). No-grant ordinary/staff/service/inactive negatives and the
   model-view distinction preserved; 049 root fixes, source clock/resource
   ownership guards and the historical no-grant import exception intact.
   Now-false hardcoded staff/help/nav text updated to actual current
   semantics; no assertion weakening, no global autouse grants, no
   UserManager defaults, no model mocks. 17 existing test files touched
   only for legitimate grants and now-false assertions.
9. **Focused Chromium evidence — PASS.**
   `tests/browser/test_management_authorization_browser.py` (5 tests, real
   Chromium in the owned copy): read-all-only non-staff navigation/
   list/filter/page/detail with NO cancel/release/edit controls; valid
   CSRF forged others-POST 403 with no change; non-staff single-module
   manager actionable with other modules and Administration 403; blackout
   manager without read-all sees only safe overlap confirmation;
   audit-reader-no-export and export-only filtered download with no history
   UI. Default and custom themes at 1440/390 with visible labels, help,
   mobile menu, focusability, no page overflow, no user-visible Django.
   Synthetic meaningful records only. Exactly TWO retained selected
   screenshots, both actually viewed in this fresh context:
   `all-reservations-1440.png` (separate All reservations nav landmark,
   filter form with help, reservation table) and
   `partial-management-390.png` (mobile menu, partial-access manager seeing
   only the authorized Blackouts module).
10. **Verification and report — PASS.** Focused new + affected old server
    and browser suites plus real PG concurrency during edits (counts below);
    final static checks re-verified in this publication round on the actual
    canonical files at the implementation head: `ruff check .` all checks
    passed; `ruff format --check .` 235 files already formatted;
    `mypy src` no issues in 140 source files; `manage.py check` no issues
    (0 silenced); `manage.py makemigrations --check --dry-run` No changes
    detected (local RuntimeWarning only, see Commands);
    `manage.py spectacular --validate --fail-on-warn` OK; changed-docs
    links/anchors scan OK (64 relative links/anchors across the seven
    changed docs files all resolve, plus three pre-existing directory
    links verified present); `git diff --check` clean; OAP harness with
    OAP_ROLE unset: `Ran 160 tests ... OK` (36.13s local; 30.887s in CI).
    Full normal CI observed once at the final implementation head (below).
    No local full-suite qualification sweep completed (recorded honestly
    under Commands); no rehearsal/HTTPS/Gunicorn/restore-whole/whole-visual
    local detour. Canonical files were formatted before copy-sync to the
    owned test environment.

## Changed files and scope

Implementation commit `95d29b82ca1ff3581f3b0647fbf335b58db2b019` changes
exactly 44 files, all inside the order's `allowed_paths`
(2988 insertions, 269 deletions vs base):

- Source: `src/slaif_reservation/accounts/admin.py`,
  `src/slaif_reservation/accounts/authorization.py`,
  `src/slaif_reservation/reservations/services.py`,
  `src/slaif_reservation/management_ui/auth.py`,
  `src/slaif_reservation/management_ui/views.py`,
  `src/slaif_reservation/web/templatetags/application_access.py` (new),
  `src/slaif_reservation/web/templates/web/base.html`,
  `src/slaif_reservation/web/templates/admin/change_form.html`, and 12
  `management_ui` templates (dashboard, _nav, policy list/detail, blackout
  list/detail/form, reservation list/detail, audit list).
- Tests (new): `tests/test_management_authorization.py`,
  `tests/browser/test_management_authorization_browser.py`; tests
  (adapted): `tests/test_management_ui.py`, `tests/test_reservations_services.py`,
  `tests/test_reservations_concurrency.py`, `tests/test_default_policy.py`,
  `tests/test_legacy_import.py`, `tests/test_legacy_import_concurrency.py`,
  `tests/test_import_lock_order.py`, `tests/test_api_v1_reservations.py`,
  `tests/test_form_guidance.py`, `tests/test_reservation_shortcuts.py`,
  `tests/test_pilot_path.py`, `tests/test_product_entry.py`,
  `tests/test_restore_drill.py`, `tests/browser/test_form_guidance_browser.py`,
  `tests/browser/test_reservation_shortcuts_browser.py`.
- Docs: `README.md`, `INSTALL.md`, `docs/authorization.md`,
  `docs/human-ui.md`, `docs/security-model.md`,
  `docs/runbooks/management-blackouts.md`, `docs/ux/form-guidance-inventory.md`.
- Order machinery: `oap/orders/050-a-granular-management-authority.md`
  (immutable order, state FINAL) and `oap/active` (contains `050-a`)
  committed with the implementation. No CRITICAL file touched. This report
  is the only changed file in its report-only commit.

## Commands and results

Owned disposable environment `~/codex-work/slaif-auth-048-922064` (private
0700 source copy, no git, locked Python 3.13, real Chromium, PostgreSQL 17
CID `7680db038ecebff114a19a929c6b2e3800d7274b23254a41707c2873d7c4067d` on
loopback 22708) with canonical source byte-identical to the copy.

- Focused server (owned PG): `tests/test_management_authorization.py`
  **17 passed**; focused affected nav/UI suites
  (`test_management_authorization`, `test_product_entry`,
  `test_form_guidance`, `test_management_ui`) **82 passed**; affected
  service/concurrency/import-lock/restore/policy/API suites re-run green
  (real PG concurrency included).
- Focused browser (real Chromium): new
  `tests/browser/test_management_authorization_browser.py` **5 passed**;
  affected browser suites green.
- Extra full local browser run: `tests/browser` directory **69 passed**
  (an additional run beyond the focused browser suites; recorded for the
  record, not required by the order).
- Aborted local full server sweep: `pytest tests --ignore=tests/browser
  --ignore=tests/oap` was launched and **aborted by strategy before
  completion** (it entered real Gunicorn qualification unrelated to this
  objective). No full local qualification is claimed; the interrupted
  pytest exited and strategy terminated only the exact recorded owned
  Gunicorn process group (ownership proven via owned .venv executable/cwd/
  ancestry/group identity). No foreign resources touched. The full local
  suite is qualified by normal full CI at the implementation head instead
  (1207 passed, below).
- Not run locally (environment gaps, covered by green CI at the
  implementation head): `tests/test_restore_drill.py`'s dump/restore round
  trip (pg_dump/pg_restore absent on this host), `test_branding` /
  `test_operational_hardening` (Docker/git absent in the owned copy), and
  browser-only tests from non-browser runners.
- Static (canonical files, re-verified at publication): `ruff check .`
  passed; `ruff format --check .` 235 files already formatted; `mypy src`
  no issues (140 files); `manage.py check` 0 issues;
  `manage.py makemigrations --check --dry-run` No changes detected (with a
  local RuntimeWarning that the default dev database at 127.0.0.1:5432 was
  unreachable — a host environment gap only; the same check runs against
  real PostgreSQL 17 in the CI test job and passes);
  `manage.py spectacular --file build/openapi/schema.yaml --validate
  --fail-on-warn` OK; changed-docs links/anchors OK; `git diff --check`
  OK; OAP harness (OAP_ROLE unset) 160 tests OK.

## CI observed before authoring

At implementation head `95d29b82ca1ff3581f3b0647fbf335b58db2b019`:

- CI run **39086341421** (workflow `ci`): container pass 31s, quality
  pass 16s, security pass 13s, test pass 11m0s — summary
  `1207 passed, 1 warning in 598.03s (0:09:58)`; the single warning is the
  pre-existing `UserWarning: Overriding setting DATABASES...` in the
  intentional DB-unavailable negative test
  `tests/test_product_entry.py::test_error_rendering_is_safe_when_db_is_unavailable`,
  unrelated to this round.
- oap run **39086341485** (workflow `oap`): oap-harness pass 36s —
  `Ran 160 tests in 30.887s / OK`.

All required implementation-head checks observed PASS. Report-head CI is
**NOT YET OBSERVED AT AUTHORING**; it is observed separately by strategy as
part of the frozen-head review. Later publication verification goes to the
private receipt.

## Security, data, dependencies and local tools

No secrets, credentials or private data in this report or the change;
synthetic 0600 credential files in the owned environment were never
printed. No real users, data, databases, hosts, secrets, exposure, DNS, TLS
or firewall work; no deployment. The repo `.venv` is permission-broken on
this host, so product/static tooling ran from the owned copy's venv
(`ruff`, `mypy`, `python`) against the canonical files. No foreign process,
container or resource cleanup occurred except the strategy-proven owned
Gunicorn group of the aborted sweep. No new dependencies; no lockfile
change. No merge, no auto-merge, no delegation, no subagents.

## DHA outcome and unresolved gates

Deferred human adjudication outcome per the order: **Decision: NONE**. No
CRITICAL entry appended, no gate cleared, no adjudication requested or
performed by coding.

## Limitations and recommendation

- Report-head CI not yet observed at authoring; strategy performs the
  frozen-head review and required report-head CI.
- Local host gaps (pg_dump/pg_restore absent; Docker/git absent in the
  owned copy; unreachable default dev DB for the local makemigrations
  consistency warning) left those specific local runs unperformed; all are
  covered by the observed green full CI at the implementation head
  (1207 passed).
- The immutable order file carries `pr_number: null`; the actual PR number
  104 is recorded here as retrieved.
- Recommendation: strategy proceeds with frozen-head review and
  report-head CI observation. No next active order, merge, release or
  self-certification is made by this report.
