# Authorization — selected group target (NOT IMPLEMENTED BY THIS CONTRACT)

**Status: SELECTED TARGET — NOT IMPLEMENTED BY THIS CONTRACT.** This page records the
human-selected M-GROUP-AUTHORIZATION contract (ARCHITECTURE.md A-16, 2026-10-17; stable rows
SAR-048–SAR-053, all initially UNPROVEN). Nothing on this page exists in the running
application yet: no new permission records, routes, token scopes, user fields, setup
commands or migrations. Commands and endpoints named as target behavior are targets, not
published interfaces. Current behavior is described only where it is needed to understand
the change.

## Current baseline (implemented today)

- Member routes: active non-service-account human sessions; reservations are
  owner-scoped (list/detail/cancel/release of one's own records).
- Management routes (/manage/): blanket admission for active, non-service-account
  **staff** sessions; cross-user lifecycle, policy and blackout operations run through
  existing audited services.
- Administration (/admin/): staff admission with existing model permissions; protected
  records are read-only or service-backed.
- Bearer API: owner-only reservations:read/create/cancel/release plus availability:read;
  asset list/detail remain staff-session-only.
- There is no asset-group booking eligibility, no cross-user read surface and no
  external user identifier today.

## Permission matrix (selected target)

Grants combine by union across all of a user's groups and individual permissions; there is
no parallel membership, no hardcoded operator group names and no explicit deny. Every
application access still requires an active non-service-account human.

| Application permission (reservations namespace) | Target meaning |
|---|---|
| reservations.book_assets | Create new reservations; additionally subject to exact-asset eligibility and existing policy/domain checks. |
| reservations.view_all_reservations | Cross-user reservation listing/detail in the separate All reservations browser/read-only API surfaces. |
| reservations.cancel_others_reservations | Audited cancellation of another owner's reservation; no implied read-all or release permission. |
| reservations.release_others_reservations | Audited release of another owner's reservation; no implied read-all or cancellation permission. |
| reservations.view_booking_policies | Inspect policy information through management. |
| reservations.manage_booking_policies | Create/update/deactivate policies through existing audited services; includes that module's read interface. |
| reservations.view_maintenance_blackouts | Inspect blackouts and their relevant details. |
| reservations.manage_maintenance_blackouts | Create/deactivate blackouts through existing audited services; includes that module's read interface. |
| reservations.view_audit_history | Existing bounded filtered audit browser. |
| reservations.export_audit_history | Existing filtered bounded CSV export; does not implicitly grant unrelated audit/reservation UI access. |

Application permissions are documented custom permissions in the reservations namespace;
they are distinct from Administration model View permissions. A mutation capability
without read-all must not incidentally disclose another owner's record through redirects,
overlap previews, errors or audit. Partial-capability users receive a useful management
landing without unauthorized counts, data, links or actions.

## Admin vs staff (target distinction)

- **Staff** is admission to /admin/ only, with existing model permissions. Staff or
  unrelated Administration permissions confer **no** application management or booking
  bypass.
- **Trusted active human superusers** retain Django's application-permission semantics and
  all protected-record/domain restrictions; they still meet exact-asset group eligibility
  when creating bookings. Administration can deliberately configure access, not bypass it
  through a reservation adapter.
- Enforcement is server-side at direct GET/POST endpoints and the shared services that
  serve them; buttons and navigation only reflect the same checks.

## Exact-asset booking eligibility (target semantics)

- Each asset is explicitly **unrestricted** or **group-restricted**.
- A restricted asset requires membership in **at least one** of its allowed existing
  groups; restricted with no allowed groups **fails closed**.
- Only the asset being booked is checked; there is **no implicit parent inheritance**.
- **All existing assets migrate unrestricted** in the upgrade.
- Browser and bearer creation share the same authoritative check around the existing
  reservation service; token creation additionally requires the token's action scope and
  the owner's current capability/membership.
- Existing active/reservable/exclusive checks, UTC/DST rules, policies/counters,
  PostgreSQL exclusion/locking and atomic audit are unchanged.
- Assets remain browsable and show whether the member is eligible; sensitive
  account/group metadata is not disclosed.
- Access changes **never rewrite existing bookings**. Owners may still list/inspect/
  cancel/release accepted reservations after losing booking capability or asset-group
  membership, subject to existing lifecycle/cutoff rules.

## Future owner-only vs separate read-all bearer contract

- `reservations:read` remains **owner-only**, even for staff/superusers; existing token
  scope records never change automatically.
- A new explicit `reservations:read_all` scope authorizes cross-user list/detail routes
  **only when the owner also currently holds** `view_all_reservations`; both are rechecked
  per request; there is no process-global grant cache; group/permission removal takes
  effect on subsequent requests with the same token.
- Issuance refuses authority-exceeding read-all and create scopes; expiry/revocation,
  activity, service-account and shared abuse controls apply unchanged.
- There is **no cross-user bearer mutation surface** in this target.
- The cross-user representation is minimal and explicit: reservation/asset UUID and safe
  asset identity, owner UUID plus external_identifier (null when unset), aware original
  start/end, effective_end, status/lifecycle, release/cancellation timestamps and
  unambiguous blocking/effective interval semantics. It excludes owner
  email/display/profile/admin flags, passwords/verifiers/token secrets, private
  locators, unrelated metadata and private purpose/cancellation/blackout free text.
  Owner representations stay compatible.

## External identifier and external enforcer boundary (target)

- Optional `external_identifier` on the existing user: opaque, case-sensitive, at most
  128 characters, numeric strings and leading zeroes preserved; populated values unique;
  unset is NULL (multiple users may be unset); no inference or backfill; existing
  accounts remain unset; only authorized account administrators edit it in existing
  Administration; member profile and bearer input cannot modify it.
- It is neither a credential nor Linux UID validation and does not replace
  UUID/email/password/token identity.
- The **external enforcer** owns account mapping, enforcement, polling, caches/refresh and
  outages. No SSH/PAM, account synchronization, workload/container execution, GPU
  allocation or automatic machine login grants enter this application. Reservation
  entitlement is not login authority.

## Deliberate upgrade intent (target)

- Explicit migrations and setup docs preserve users/groups/reservations/policies/audits/
  tokens and old individual permissions; every current management route/action is
  inventoried and mapped to its grant.
- A one-time **baseline booking-permission assignment** to existing non-service-account
  users preserves their former booking access; its exact scope is documented and tested
  against a populated pre-upgrade database.
- Newly created accounts receive **no** automatic application grants or privileged-group
  membership; the required booking grant is explained in account administration.
- Current staff management access is **NOT** silently retained through is_staff: a
  dry-run-first, explicit, idempotent operator setup procedure grants the chosen current
  staff the management capability set. Read-all is never inferred from old Administration
  View permissions.
- Real deployed DB changes remain operator-owned, with backup/rollback guidance;
  migrations are tested only on owned synthetic databases. Example operator groups (e.g.,
  Administrators, Lab members, Students, Reservation readers) are illustrations, never
  authorization constants.

## Deferrals unchanged by this target

Projects, organizational trees, delegated group ownership, general policy languages,
token/management admin or mutation bearer APIs, OIDC/password reset/notifications,
monitoring stack, scheduler, automatic physical allocation, real migration/cutover and the
execution gateway remain deferred (SAR-036 as amended by A-16). This target adds no
execution, deployment or real-infrastructure authority.
