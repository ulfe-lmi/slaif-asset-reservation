<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "051-a",
  "order_path": "oap/orders/051-a-read-all-bearer-authority.md",
  "order_sha256": "ee819c8667dfe53c24b9b42cc6710df1aada6e3c0b32a21e569dabc46abf070c",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 105,
  "pr_number": 106,
  "branch": "codex/105-oap-051-a-read-all-bearer-authority",
  "implementation_head": "52045f887a2a5994a9b1d9f757cf8be1d2b32683",
  "base_sha": "3461fa0106c55994a959f88450d4866b018ad890",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "52045f887a2a5994a9b1d9f757cf8be1d2b32683",
    "runs": [
      {
        "run_id": 39097711178,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "success",
          "container": "success",
          "test": "success"
        }
      },
      {
        "run_id": 39097711173,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1237 passed, 1 warning in 617.32s (0:10:17)",
    "warning": "tests/test_product_entry.py:568 UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unrelated)",
    "oap_harness_summary": "Ran 160 tests in 30.698s / OK",
    "first_head_note": "CI run 39096906439 (CI workflow) at candidate implementation head 3589a8b589e116614eb86612be9c75c504c2269f: quality/security/container/oap-harness success, test failure (tests/test_assets_web_api.py::test_api_root_reports_asset_endpoint — exact API-root endpoints dict, file outside the order's allowed paths). Repaired in-scope by commit 52045f8 keeping the static root link list unchanged (order item 1 permits but does not require the link); all five checks then success at 52045f8."
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 051-a — execution report: explicit read-all bearer authority and minimal reservation data

Implementation head SHA: 52045f887a2a5994a9b1d9f757cf8be1d2b32683
Report publication commit: SELF

## Identity and result

COMPLETE for order 051-a (D0) on issue #105 / PR #106 (CREATE) / branch
`codex/105-oap-051-a-read-all-bearer-authority`, base main
`3461fa0106c55994a959f88450d4866b018ad890` (merged 050/PR #104, issue #103
closed). The order file (`oap/orders/051-a-read-all-bearer-authority.md`,
state FINAL, `Decision: NONE`) and the `oap/active` pointer (`051-a` + LF)
were committed with the implementation work as the order's allowed paths
require. Implementation commits: `3589a8b` (implementation + tests + docs)
and `52045f8` (in-scope CI repair: static API-root link list left
unchanged). No merge, no auto-merge, no self-approval.

## Acceptance evidence (order criteria 1–10)

All evidence below was produced against the owned disposable environment
`~/codex-work/slaif-auth-048-922064` (source copy without `.git` by design,
owned PostgreSQL 17 on loopback 22708, owned Chromium with the Ubuntu24
override). Canonical-repo edits were copied into the exec copy and parity
proven (`diff -rq` clean over `src/`, `tests/`, `docs/`, `README.md`,
`oap/active`, order file) before each test claim. Evidence labels are
truthful; the full-suite qualification is the normal CI run at the exact
implementation head (see "CI observed before authoring").

1. **Explicit new interface and both authority gates** — PASSED.
   `src/slaif_reservation/api/read_all_views.py` adds exactly
   `GET /api/v1/all-reservations/` and `GET /api/v1/all-reservations/<uuid>/`
   (registered in `api/urls.py`). `ReadAllBearerAPIView` reuses
   `BearerAPIView`/`ApiTokenAuthentication`/shared abuse controls; the
   `reservations:read_all` scope gate is the existing `HasApiTokenScope`
   (missing scope → existing `403 insufficient_scope`) and the owner's
   CURRENT `reservations.view_all_reservations` is rechecked per request
   through the existing active-human helper `has_reservation_permission`
   (missing capability → existing `PermissionDenied` → `403
   permission_denied`). Both run in `check_permissions` BEFORE any
   reservation row is fetched; no process-global grant cache; no
   `SessionAuthentication` fallback; no global DRF settings change. Every
   response (success, error, 405) carries `Cache-Control: private,
   no-store` and a `Vary` header including `Authorization`; old endpoint
   headers are unchanged. Authorized missing UUID returns the existing
   `404 reservation_not_found`. Tests: `tests/test_read_all_api.py::
   test_dual_gate_matrix` (scope-only/permission-only/both/neither),
   `test_staff_and_model_view_alone_do_not_qualify`,
   `test_capability_removal_takes_effect_with_same_valid_token`,
   `test_token_lifecycle_states_still_authenticate_closed` (expired,
   revoked, inactive owner, service-account owner incl. superuser),
   `test_shared_abuse_budgets_still_apply` (429 preserved),
   `test_new_routes_are_read_only` (POST/PUT/PATCH/DELETE → 405 for
   authorized requests; no nested cancel/release routes),
   `test_authorized_missing_uuid_uses_existing_404`,
   `test_privileged_responses_carry_safe_cache_headers` (incl.
   old-endpoint-unchanged negative). All PASSED locally (17 tests in file)
   and included in the CI full suite (1237 passed).
2. **Owner-only compatibility, no silent global helper** — PASSED.
   `_filtered_reservations` in `api/reservation_views.py` keeps its
   unconditional owner filter; only the exact validated filter expressions
   were extracted into `_apply_reservation_filters` (shared by the
   owner-scoped list and the authorized global list; `from` = lower overlap
   bound `effective_end_at > from`, `to` = upper bound `start_at < to`,
   strict half-open). The global queryset is constructed only inside the
   authorized new views. `tests/test_read_all_api.py::
   test_owner_endpoints_stay_owner_only_with_all_caps_and_both_scopes`
   (superuser owner with every application capability and both scopes:
   owner list shows only own record, other-owner detail → 404, cross-owner
   cancel/release → 404, other record status unchanged),
   `test_overlap_filters_are_strict_half_open`,
   `test_status_asset_lifecycle_filters_and_pagination` (default 50 / max
   100 / offset, history before `from` included, cancelled never blocks),
   and `test_asset_inventory_and_docs_boundaries_unchanged` all PASSED.
3. **Minimal explicit representation** — PASSED.
   Dedicated read-only allow-list serializers (`ReadAll*Serializer`) and
   `read_all_reservation_representation()` in `api/serializers.py`; the
   row is rendered through the serializer, so the declared fields are the
   exact mechanical allow-list (not `ModelSerializer(fields="__all__")`,
   not the owner `reservation_representation`, which carries private
   purpose/reason). Row: `id`; `asset {id, slug, name, kind}`; `owner
   {id: stable UUID, external_identifier: opaque string or null}`;
   `status`; derived `lifecycle`; aware UTC `start_at`/`end_at`/
   `effective_end_at`/`released_at`/`cancelled_at`; `blocking_interval` =
   half-open `{start_at, effective_end_at}` for confirmed/released,
   `null` for cancelled. `tests/test_read_all_api.py::
   test_list_returns_exactly_the_minimal_allowlist` (exact key sets plus
   privacy canaries: no email/display/profile/flags/free-text/locator
   leakage in list, detail or errors), `test_unassigned_external_identifier_
   is_explicit_null`, `test_max_length_and_case_sensitive_external_
   identifier` (null, `001001`, 128 chars, case-sensitive),
   `test_blocking_interval_semantics_per_status` (real
   service-produced confirmed/released/cancelled bookings; original end
   immutable) all PASSED.
4. **Issuance ceilings only at new issuance** — PASSED.
   `reservations:read_all` added to the syntactic allow-list in
   `accounts/tokens.py` (no migration; the JSON scope check is
   nonempty/known-scope only). `accounts/authorization.py` adds the closed
   `SCOPE_ISSUANCE_CAPABILITIES` mapping (`create` → `book_assets`,
   `read_all` → `view_all_reservations`) with `can_issue_scope` /
   `issuable_token_scopes` (fail-closed on unknown scopes, no caching).
   `issue_api_token` in `accounts/services.py` rejects a ceiling-exceeding
   scope on the FRESH row-locked owner (`_lock_active_human`) BEFORE any
   token ID/secret/verifier/persistence/audit write, using the existing
   `TOKEN_SCOPE_INVALID`; a denial writes nothing. No authority logic was
   placed in `normalize_api_token_scopes`, model clean, generic lock,
   revoke or last-use. `tests/test_token_scope_authority.py` (10 tests)
   PASSED: issuance 2×2 (no-staff reader can issue read-all but not
   create; booking-only can create but not read-all), denial writes
   nothing (no token row, no audit, no secret), stale-instance permission
   cache cannot bypass the locked check, additive union, old token keeps
   its stored scope after capability removal (authenticates, owner scopes
   work, cross-user 403, revoke works), superuser issuance ceilings,
   inactive/service-account issuance rejected, forged and
   GET→POST-revoked POST denied (safe form error + service denial),
   owner list/revoke after losing rights.
5. **Member token UI** — PASSED.
   `ApiTokenCreationForm(owner=None)` in `web/forms.py` offers only the
   scopes the server-request owner can currently issue (conservative when
   no owner: never defaults to the privileged choices); `token_create` in
   `web/views.py` passes `owner=request.user` on BOTH GET and POST; a
   `TOKEN_SCOPE_INVALID` service denial becomes a safe field error on
   `scopes`. `web/templatetags/form_guidance.py` adds the human label
   "Read other people's reservations (read-only)" and per-choice effects
   (read_all: read-only, requires the current capability, removal stops
   the scope on the next request while other scopes keep working; create:
   notes the current booking capability and asset-group eligibility at
   booking time). Stored/wire values remain the exact machine keys.
   `tests/test_form_guidance.py` (32 tests) PASSED (read_all absent for a
   member without the capability, create-effect text, forged read_all
   POST rejected). Real Chromium (owned, Ubuntu24 override):
   `tests/browser/test_token_scope_authority_browser.py` (3 tests)
   PASSED — choice visibility per capability at 1440/390, per-choice
   help with accessible associations, valid-CSRF forged/unavailable-scope
   POST and revoked GET→POST cannot create, owner list/revoke after
   losing rights, no framework branding, no horizontal overflow,
   default + custom branding. Two safe pre-issuance form screenshots were
   captured, actually viewed, and retained privately (exec
   `browser-artifacts/oap-051-a-retained/`); no one-time token plaintext,
   password, header, CSRF, cookie or raw trace appears in any artifact.
6. **Real negative/positive evidence** — PASSED.
   Covered by the matrices above (real PostgreSQL 17 and real HTTP via
   the Django test client and real Playwright/Chromium): both-gate 2×2,
   group+individual union, removal with the SAME valid token,
   direct-permission removal, inactive/service/superuser, expiry +
   revocation, issuance 2×2 with no-wanted-writes/audit assertions,
   stale-instance rejection, exact allow-list/privacy canaries
   (null / `001001` / length 128 / case), original-vs-effective end and
   half-open `blocking_interval` per status, strict boundary filter
   behavior, and unchanged overlap/lifecycle/audit/idempotency/booking
   rules (affected old suites green locally and in CI).
7. **Existing fixtures without weakening** — PASSED.
   All `issue_api_token` call sites were inventoried first. Fixes, all in
   order-allowed test files and all preserving the original assertions:
   `tests/test_authorization_foundation.py::
   test_bearer_api_neither_reveals_nor_modifies_identifier` and the two
   `no_grant` create-token sites in `tests/test_booking_authorization.py`
   now mint a LEGITIMATE historical token (grant `book_assets` → issue →
   revoke) before use, retaining the final no-grant 403 and owner
   lifecycle; `tests/test_pilot_readiness_check.py`'s
   expired-idempotency token fixture gained an explicit `book_assets`
   grant (readiness command logic unchanged); `tests/test_api_schema.py`
   asserts the two new OpenAPI paths (its root-endpoints assertion was
   reverted in the CI fix below); `tests/test_form_guidance.py` updated
   for the new choice set and effects. No permission auto-grant was
   introduced in any shared helper, fixture, conftest, `UserManager` or
   signal. The read-only `token_for` usage in the operational-hardening
   tests was inventory-verified as unaffected.
8. **Focused Chromium and actual screens** — PASSED (see criterion 5).
   Max two selected screenshots of safe FORM pages (before issuing any
   plaintext token), actually viewed at the final state, retained
   privately before later Playwright cleanup; no 16-image bundle, no
   screenshot of any one-time token/password/header/CSRF/raw response.
9. **Current product docs and external boundary** — PASSED.
   Updated: `docs/api-contract.md` (scope list, owner-only `read`
   clarification, issuance ceilings, "Dual gate for
   `reservations:read_all`" section, both endpoint sections with overlap
   filter semantics, "Representation" allow-list spec, enforcer guidance
   — opaque mapping of `external_identifier`, aware `[start, end)`
   `blocking_interval` evaluation, cancelled null, no atomic
   full-pagination snapshot, external enforcer owns account
   enablement/enforcement/polling/caches/refresh/outages, no
   user-directory/free-text/audit permission, entitlement is not login
   authority — and the deferred list); `docs/authorization.md` (status
   header, available-now bullet, current baseline, "Owner-only vs
   separate read-all bearer contract (implemented)", Reservation-readers
   group row requiring the explicit NEW token scope with no existing-token
   expansion); `docs/human-ui.md` (API tokens: read-only read_all scope,
   form offers only currently issuable scopes, post-removal behavior);
   `docs/security-model.md` (bearer endpoint paragraph: new read-only
   cross-user surface with dual gate and minimal representation; the old
   blanket "reservation reads constrained to the owner" claim qualified
   with the explicit authorized minimal owner-ID surface);
   `docs/ux/form-guidance-inventory.md` (Scopes row: per-choice effects
   incl. read_all and create current-capability note, choices filtered to
   currently issuable scopes); `README.md` (Agents row: explicit
   read-only cross-user all-reservations surface; limitation bullet:
   cross-user read now implemented, projects/org/delegated groups still
   not). `docs/README.md` checked: no change needed. New/changed anchors
   verified against GitHub anchor rules (`#dual-gate-for-reservationsread_
   all`, `#representation`, `#authentication-and-scopes`,
   `#management-route-inventory-enforced`). No history rewrite, no new
   ADR, no architecture hash churn. `config/settings/base.py` changed
   ONLY the `SPECTACULAR_SETTINGS.DESCRIPTION` documentation literal
   (dual-gate mention).
10. **Verification and strict publication** — PASSED (see "Commands and
    results"). No local full pytest / full server / full browser /
    OAP-whole / rehearsal / operational / HTTPS / Gunicorn / restore-drill
    sweeps: NOT RUN locally by design; the normal full CI at the exact
    implementation head provides that qualification (1237 passed).
    `tests/oap/test_ba26_27_40_41_wrapper.py` verified byte-identical to
    the base (repo and exec copy). No new dependencies; `uv.lock`
    untouched.

## In-scope CI repair (truthful record)

The first implementation commit `3589a8b589e116614eb86612be9c75c504c2269f`
also added a static `all_reservations` link to the public API-root
endpoints dict (order item 1: "Public API root may add only static new
link"). CI run 39096906439 (test job) failed on
`tests/test_assets_web_api.py::test_api_root_reports_asset_endpoint`,
which asserts the exact root dict and whose file is NOT in the order's
`allowed_paths` (it cannot be modified in this round). D0 resolution, in
commit `52045f887a2a5994a9b1d9f757cf8be1d2b32683`: the root endpoints
dict is left unchanged (the order's "may" is not exercised), the
`test_api_schema.py` root assertion reverted to the original four entries
while KEEPING its two new OpenAPI path assertions, and
`docs/api-contract.md`'s `GET /api/v1/` section updated accordingly. The
two new bearer routes remain fully documented in the API contract and the
generated OpenAPI schema. Local re-verification after the fix:
`tests/test_api_schema.py` + `tests/test_assets_web_api.py` +
`tests/test_read_all_api.py` = 50 passed; ruff check/format, mypy (141
files), `manage.py check`, `makemigrations --check --dry-run` (no
changes) and `spectacular --validate --fail-on-warn` all green again.

## Changed files and scope

28 files in the two implementation commits, every one inside the order's
`allowed_paths` (verified programmatically; no other file changed):

- `src/slaif_reservation/accounts/authorization.py` (scope-capability
  mapping + helpers)
- `src/slaif_reservation/accounts/services.py` (issuance ceilings)
- `src/slaif_reservation/accounts/tokens.py` (new scope in allow-list)
- `src/slaif_reservation/api/read_all_views.py` (NEW; dual-gate base +
  list/detail views)
- `src/slaif_reservation/api/reservation_views.py` (filter extraction;
  owner filter untouched)
- `src/slaif_reservation/api/serializers.py` (dedicated read-only
  allow-list representation)
- `src/slaif_reservation/api/urls.py` (two read-only routes)
- `src/slaif_reservation/api/views.py` (unchanged at final head after CI
  fix)
- `src/slaif_reservation/web/forms.py` (issuable-scope choices)
- `src/slaif_reservation/web/views.py` (owner on GET+POST; safe scope
  error)
- `src/slaif_reservation/web/templatetags/form_guidance.py` (label +
  effects)
- `src/slaif_reservation/config/settings/base.py` (SPECTACULAR
  DESCRIPTION literal only)
- `tests/test_read_all_api.py` (NEW, 17 tests)
- `tests/test_token_scope_authority.py` (NEW, 10 tests)
- `tests/browser/test_token_scope_authority_browser.py` (NEW, 3 tests)
- `tests/test_api_schema.py`, `tests/test_authorization_foundation.py`,
  `tests/test_booking_authorization.py`, `tests/test_form_guidance.py`,
  `tests/test_pilot_readiness_check.py` (fixture/assertion updates,
  criterion 7)
- `docs/api-contract.md`, `docs/authorization.md`, `docs/human-ui.md`,
  `docs/security-model.md`, `docs/ux/form-guidance-inventory.md`,
  `README.md`
- `oap/active` (050-c → 051-a, exact `051-a` + LF) and
  `oap/orders/051-a-read-all-bearer-authority.md` (committed as ordered)

No model, migration, schema, constraint, unit, lifecycle, policy,
exclusivity, booking-eligibility, audit or idempotency storage change. No
existing token scope backfill/mutation. No new dependencies.

## Commands and results

Executed in the owned environment (parity proven before each claim):

- `./run.sh run ruff check .` → PASSED ("All checks passed!") — after 9
  D0 test-file lint fixes (5× E501 line length, 2× F401 unused import,
  1× F841 unused variable, 1× E501) and `ruff format` on the five
  affected test files; all within allowed paths.
- `./run.sh run ruff format --check .` → PASSED (239 files).
- `./run.sh run mypy src` → PASSED ("no issues found in 141 source
  files").
- `DJANGO_SETTINGS_MODULE=...test ./run.sh run python manage.py check` →
  PASSED ("0 issues").
- `./run.sh run python manage.py makemigrations --check --dry-run` →
  PASSED ("No changes detected").
- `./run.sh run python manage.py spectacular --validate --fail-on-warn` →
  PASSED (exit 0).
- `git diff --check` → PASSED (clean).
- `./run.sh run pytest --ds=slaif_reservation.config.settings.test tests/test_read_all_api.py tests/test_token_scope_authority.py` → PASSED (27 passed).
- Same command with `tests/test_api_tokens.py tests/test_authorization_foundation.py tests/test_booking_authorization.py tests/test_pilot_readiness_check.py tests/test_form_guidance.py` → PASSED (186 passed).
- Same command with `tests/test_api_v1_reservations.py tests/test_abuse_controls.py tests/test_product_entry.py tests/test_management_authorization.py tests/test_pilot_path.py tests/test_management_ui.py tests/test_accounts.py tests/test_web_human_mvp.py tests/test_api_schema.py` (2 inline browser tests deselected, then run under the browser runner) → PASSED (142 passed, 2 deselected).
- `./run-browser.sh run pytest --ds=... tests/browser/test_token_scope_authority_browser.py` → PASSED (3 passed; final run, screenshots retained).
- Same runner with `tests/browser/test_form_guidance_browser.py tests/browser/test_human_mvp_browser.py tests/browser/test_pilot_path_browser.py tests/browser/test_branding_browser.py` → PASSED (31 passed).
- Same runner with the two deselected inline browser tests (`tests/test_product_entry.py::test_error_rendering_is_safe_when_db_is_unavailable`, `tests/test_pilot_path.py::test_integrated_pilot_path_shared_state_across_surfaces`) → PASSED (2 passed).
- Full local pytest / full browser sweep / operational / rehearsal /
  HTTPS / Gunicorn / restore drills → NOT RUN locally (order forbids;
  normal full CI at the exact head provides qualification).
- `tests/oap/test_ba26_27_40_41_wrapper.py` → verified byte-identical to
  base in both repo and exec copy (not committed, unchanged).

Local focused total: 391 passed, 0 failed.

## CI observed before authoring

At the exact implementation head
`52045f887a2a5994a9b1d9f757cf8be1d2b32683` (PR #106), all five checks
observed:

- CI run `39097711178` (workflow `CI`): quality SUCCESS, security
  SUCCESS, container SUCCESS, test SUCCESS. Test job: "1237 passed, 1
  warning in 617.32s (0:10:17)"; the single warning is the pre-existing,
  intentional DB-unavailable negative test in
  `tests/test_product_entry.py` (DATABASES override UserWarning).
- oap run `39097711173` (workflow `oap`): oap-harness SUCCESS ("Ran 160
  tests in 30.698s / OK").

Earlier at candidate head `3589a8b589e116614eb86612be9c75c504c2269f`:
CI run `39096906439` — quality/security/container SUCCESS, test FAILURE
(the out-of-allowed-paths exact root-dict test, repaired as described
above); oap run `39096906469` — oap-harness SUCCESS.

Report-head CI: NOT YET OBSERVED AT AUTHORING (the report commit is the
last commit of this round; its checks are a normal follow-up, not a
completion claim).

## Security, data, dependencies and local tools

No secrets, tokens, CSRF values, verifiers, peppers, DB URLs, cookies or
Authorization material appear in this report, the commits, the PR, logs
or the retained artifacts. The two retained screenshots are safe
pre-issuance form pages only (viewed; no one-time plaintext token is
shown anywhere). The owned disposable environment (PG17 loopback 22708,
owned Chromium) was reused as instructed; no foreign cleanup, no
production/lab/Neumann contact, no DNS/TLS/firewall/exposure change, no
new dependencies, no runtime configuration change beyond the permitted
SPECTACULAR description literal. Ruff/mypy/pytest were run from the
owned `uv` environment only.

## DHA outcome and unresolved gates

Order DHA: `Decision: NONE` — no CRITICAL append was required or made;
`CRITICAL.md` unchanged. No new DHA candidate arose: the only judgment
needed (not exercising the optional static API-root link because the
asserting test file is outside the allowed paths) is a routine D0
in-scope mechanics decision recorded above.

## Limitations and recommendation

- Full qualification (full pytest incl. browser, operational checks,
  restore drill, container smoke) came from the normal five exact-head CI
  checks, not from local sweeps, as the order requires.
- The A-16 facets remain UNPROVEN until the fresh independent ICA at the
  exact merged revision; strategic review/merge and human release remain
  separate.
- The external enforcer boundary (account mapping, enforcement, polling,
  caches/refresh, outages) is documented but lives outside this
  application.
Recommendation: strategy may proceed to review/acceptance of PR #106 at
implementation head `52045f887a2a5994a9b1d9f757cf8be1d2b32683`; no
further coding mutation is made in this round after this report.
