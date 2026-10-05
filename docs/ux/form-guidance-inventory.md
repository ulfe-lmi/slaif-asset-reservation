# Form and choice guidance inventory

**Order:** 037-a (SAR-044). This inventory was completed before the guidance
edits and maps every ACTUAL runtime control (bound form fields, model-generated
admin add/change/password/group fields, dynamically renamed fields, and raw
template filters/actions) to rendered, accessible guidance. The earlier
39-declared-field AST baseline is superseded: it missed dynamically renamed
fields (`from`/`to`), model-generated admin fields, the admin add-form
password pair, the per-user password-change form, the group permissions
control, the raw member/staff filter forms, and the one-time-token display.

Coverage rules: every editable control has either (a) a meaningful label plus
nearby rendered help with matching IDs and `aria-describedby` (checkbox groups
use an accessible fieldset with legend), or (b) an explicit self-evident
justification recorded below. No filler "Enter name" style text.
Wire values, validation, permissions, admission and crypto are unchanged.

## 1. Member surfaces (web)

| Control | Route / template | Bound | State before 037-a | Guidance added (label / help) |
|---|---|---|---|---|
| Email | `/login/`, `web/login.html`, `HumanAuthenticationForm.username` | yes | label "Email" only | help: account email, created by an administrator, no self-registration; `aria-describedby` wired |
| Password | `/login/`, `HumanAuthenticationForm.password` | yes | label only | self-evident (standard password entry under a generic-denial form); unchanged |
| Display name | `/profile/`, `ProfileForm.display_name` | yes | label only | help: shown to staff in management views, blank shows email only |
| Timezone | `/profile/`, `ProfileForm.timezone` | yes | unassociated `<p class="help">` | help: required IANA name, drives all entered/shown times, blank/unknown rejected; `aria-describedby` wired |
| Start | `/assets/<id>/reserve/`, `ReservationForm.start` | yes | label "Start" only | help: local date/time in the user's timezone, must be in the future |
| Start occurrence | `ReservationForm.start_fold` | yes | label "Start occurrence" | help: only relevant at DST transitions (ambiguous/nonexistent local times); Automatic = system default |
| End | `ReservationForm.end` | yes | label "End" only | help: local end; asset held from start until end, end instant free again |
| End occurrence | `ReservationForm.end_fold` | yes | label "End occurrence" | same DST relevance as start occurrence |
| Purpose | `ReservationForm.purpose` | yes | label "Purpose" | help: optional unless the asset's policy requires it; staff can read it |
| Cancel reason | reservation detail, `CancellationForm.reason` | yes | label "Reason" | help: optional, recorded with the cancellation, visible to staff; cancel warning line |
| Release action | reservation detail (active) | button | bare button | warning: ends the reservation now, frees the remaining time, cannot be undone |
| Token name | `/tokens/create/`, `ApiTokenCreationForm.name` | yes | label "Token name" | help: label only, never changes permissions |
| Scopes (group) | `ApiTokenCreationForm.scopes` (CheckboxSelectMultiple) | yes | machine-string choices only | fieldset + legend; human labels replace machine strings; per-choice effect line incl. `assets:read` reserved (no inventory discovery today); exact stored values unchanged |
| Lifetime in days | `ApiTokenCreationForm.lifetime_days` | yes | help "Maximum allowed lifetime is N days." | help: days until self-expiry, 1–N, shorter limits leak damage |
| Token list scopes column | `/tokens/`, `token_list.html` | display | machine strings joined | human labels via `scope_label` filter |
| Token created scopes | `token_created.html` | display (one-time) | machine strings | human labels via `scope_label`; token secrecy/history behavior unchanged |
| Asset search `q` | `/assets/`, raw GET filter | no (raw) | inline label only | help: matches name, slug or description |
| Asset kind | raw filter select | no | inline label | help: one asset kind (Machine/GPU/CPU pool/Service/Other) |
| Asset parent | raw filter select | no | inline label | help: only child assets of that machine |
| Asset tag | raw filter select | no | inline label | help: assets carrying that tag |
| Asset reservable | raw filter select | no | inline label | help: only bookable assets / only non-bookable |
| Availability free "latest valid start" | `web/_availability.html` | display | unlabeled parenthetical | help line explaining the latest valid start within a free interval |
| Browsable API token input | `/api/` (DRF Browsable API) | yes | standard auth input | self-evident API-surface input; API contract doc is the guidance; unchanged (API surface, not a member/staff/admin form) |
| Logout / pagination / table links | various | buttons/links | — | self-evident; unchanged |

## 2. Staff surfaces (management UI, `/manage/`)

| Control | Route / template | Bound | State before 037-a | Guidance added |
|---|---|---|---|---|
| Policy name | policy form, `ReservationPolicyForm.name` | yes | label "Name" | help: short unique policy name |
| Policy asset target | `ReservationPolicyForm.asset` | yes | help "Leave empty for the global policy." | help: exact-asset → parent-machine → global resolution order; two active at one level fail closed |
| Min duration | `min_duration_minutes` | yes | label "Minimum duration" | label "(minutes)" + help: shortest allowed booking, 1440 min = 24 h = 1 day |
| Max duration | `max_duration_minutes` | yes | label "Maximum duration" | help: longest single booking, 2880 min = 48 h = 2 days |
| Booking horizon | `booking_horizon_days` | yes | label "Booking horizon days" | help: how far into the future a booking may START (not end), 7 = within 7 days |
| Lead | `min_lead_minutes` | yes | label "Minimum lead minutes" | help: gap between booking and start; 0 = start now allowed |
| Cutoff | `cancellation_cutoff_minutes` | yes | label "Cancellation cutoff minutes" | help: minutes before start when members stop being able to cancel; 0 = cancellable up to start |
| Max upcoming | `max_upcoming_per_principal` | yes | label only | help: not-yet-started bookings per principal across all assets and their tokens; reject at count |
| Max concurrent | `max_concurrent_per_principal` | yes | label only | label "Maximum overlapping records per principal" + help: counts existing confirmed/released records intersecting the proposed interval; 8 rejects at >= 8 intersecting (record count, not occupancy sweep) |
| Purpose required | `purpose_required` | yes | label only | help: members must enter a purpose for new bookings |
| Blackout asset | `MaintenanceBlackoutForm.asset` | yes | label "Asset" | help: the single exact asset that stops accepting new bookings |
| Blackout timezone | `timezone` | yes | label "Timezone" | help: IANA name interpreting the entered start/end |
| Blackout start/end + occurrence | `start`, `end`, `start_fold`, `end_fold` | yes | labels only | local wall-time help + DST occurrence relevance |
| Blackout reason | `reason` | yes | label "Reason" | help: required, stored and visible to staff |
| Overlap confirm | `confirm_overlaps` | yes | label "Create despite overlapping reservations" | help: creating never cancels/releases overlapping reservations; it only blocks new bookings |
| Policy deactivation | `policy_detail.html` | button | bare button | warning: stops applying to new bookings immediately, existing bookings unchanged, fail-closed if it was the only match |
| Blackout deactivation | `blackout_detail.html` | button | bare button | warning: new overlapping bookings allowed again immediately, history preserved |
| Staff cancel reason | `ManagementCancellationForm.reason` | yes | label "Reason" | help: optional, recorded and visible to staff; cancel warning |
| Staff release | `reservation_detail.html` | button | bare button | warning: ends the reservation now, original end preserved in history |
| Reservation filter `asset` | `ReservationFilterForm.asset` | yes (rendered raw) | bare label | help: narrow to one asset |
| Reservation filter `q` | `q` | yes | bare label | help: matches owner email/name or asset slug/name |
| Reservation filter `status` | `status` | yes | bare label | help: confirmed / cancelled / released |
| Reservation filter `lifecycle` | `lifecycle` | yes | bare label | help: active = running now, upcoming = not started, completed, cancelled, released = ended early |
| Reservation filter `from`/`to` | renamed from `from_at`/`to_at` | yes | bare labels "From"/"To" | labels "From (start at or after)" / "To (start before)" + aware ISO-8601 help (e.g. 2026-10-05T10:00:00+02:00) |
| Audit filter `action` | `AuditFilterForm.action` | yes | bare label | help: which operation was recorded |
| Audit filter `target type` | `target_type` | yes | bare label | help: record type the action applied to (e.g. reservation) |
| Audit filter `actor` | `actor` | yes | bare label | help: part of a name/email or exact user UUID |
| Audit filter `source` | `source` | yes | bare label | help: web / API / admin service / migration |
| Audit filter `correlation` | `correlation_id` | yes | bare label | help: UUID linking the events of one operation |
| Audit filter `occurred from/to` | `occurred_from`/`occurred_to` | yes | bare labels | aware ISO-8601 help |
| Audit export link | `audit_list.html` | link | bare "Export CSV" | help: exports the current filtered view (default: last 7 days, bounded rows) |
| Policy list resolver select | `policy_list.html` raw select | no | bare label | help: resolves exact → parent → global effective policy |
| Dashboard counts | `dashboard.html` | display | — | self-evident counts; unchanged |

## 3. Administration (Django admin)

| Control | Route | Bound | State before 037-a | Guidance added |
|---|---|---|---|---|
| Admin login email | `/admin/login/`, `SlaifAdminAuthenticationForm.username` | yes | label "Email" | help: the administration account email; `aria-describedby` wired |
| Admin login password | same | yes | bare field | help: wrong/inactive/service-account identities get the same generic error |
| User add: email / password1 / password2 / is_staff / is_superuser | `/admin/accounts/user/add/` | add form | bare fields | help on each: account email (admin-created), initial password + confirm, staff = management/administration access, superuser = full rights |
| User change: email | `/admin/accounts/user/<id>/change/` | yes | bare | help: sign-in identifier, admin-created accounts |
| User change: password | same | yes (read-only) | inherited hash summary (algorithm + masked salt/hash) + broken relative "Reset password" link | REPLACED: safe status only ("Password set" / "No password set" / unrecognized format) + real permitted action = per-user password-change form (`.../password/`, permission-checked, audited); no hash fragment rendered |
| User change: display name / timezone | same | yes | bare | help: shown to staff / IANA name for web booking |
| User change: is_service_account | same | yes | bare | help: machine account, cannot sign in to member site or administration |
| User change: is_active / is_staff / is_superuser | same | yes | bare | precise flag effects |
| User change: groups / user_permissions | same | yes (filter_horizontal) | bare | help: site permissions only — NOT project/membership authorization, do not change reservable-asset policy |
| User password change form | `/admin/accounts/user/<id>/password/` | Django `AdminPasswordChangeForm` | meaningful built-in help already present | kept the built-in help (password1 = password rules list, password2 = confirm wording) with automatic `aria-describedby`; validation/hashing unchanged |
| Group permissions | `/admin/auth/group/...` | Django `GroupAdmin` | bare multiselect | help: Django site permissions only, not project/membership authorization |
| AssetTag name / slug / description | `/admin/assets/assettag/...` | yes | bare | help incl. prepopulated slug behavior |
| Asset parent / slug / name / kind | `/admin/assets/asset/...` | yes | bare | help incl. machine-has-no-parent rule, stable slug, bookable kinds |
| Asset booking mode | same | yes | bare | help: exclusive only — no overlapping bookings |
| Asset description / location / timezone | same | yes | bare | description shown to members; location staff-only (not in member UI or API); IANA display timezone |
| Asset active / reservable / verification_required | same | yes | bare | precise effects: hidden+unbookable when inactive; reserve action only when reservable; verification is a display flag with no enforced workflow yet |
| Asset capabilities / tags / physical_locator | same | yes | bare | capabilities = verified normalized JSON shown to members; tags = filter labels; locator = internal-only, never member/API visible |
| Asset legacy_* read-only | same | read-only | bare | help: legacy import provenance, read-only |
| ReservationPolicy / Reservation / MaintenanceBlackout / AuditEvent / ApiToken change pages | `/admin/...` | read-only | no explanation of protection | contextual read-only guidance banner on each change form naming the supported mutation path (management area / member token page / append-only audit) |
| Admin changelist search + filters | all changelists | built-in | Django defaults | self-evident built-in search/filter controls; unchanged |
| "Important dates" (user), timestamps | user/asset change | read-only | bare | self-evident read-only audit timestamps; unchanged |

## 4. Out of scope (unchanged)

- Token one-time plaintext display, no-store/private/no-referrer headers, history
  scrubbing, verifier/pepper handling (SAR-014/SAR-015).
- All validation, selectors, services, policy evaluation, audit, CSRF, idempotency,
  admission, permissions, wire contracts, schema, migrations, dependencies.
- Full theme and operator appearance overrides (038 scope).

## 5. Verification

- `tests/test_form_guidance.py`: rendered GET + invalid-POST assertions for
  member/management/admin/raw-filter controls (help present, IDs match,
  `aria-describedby` wired, validation unchanged).
- `tests/browser/test_form_guidance_browser.py`: Playwright seeded forms at
  1440/390 (reservation, token create, profile, policy, blackout, reservation/
  audit filters, admin user add/change/password/groups, asset add/change);
  keyboard access, nearby help, no horizontal overflow; privacy-safe
  screenshots (no tokens/passwords/verifiers/CSRF/cookies/raw traces).
- Existing negative suites (timezone/DST/duration/policy, roles, CSRF, scopes,
  protected admin, token secrecy) preserved unmodified where they assert
  behavior; label selectors adjusted semantically where text changed.
