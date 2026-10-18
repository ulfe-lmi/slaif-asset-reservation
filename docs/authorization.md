# Authorization — group-based access (available now vs planned)

**Status: available now — the foundation, booking enforcement (the
`reservations.book_assets` capability and exact-asset group eligibility gate
new reservations) and management capability enforcement (the nine management
capabilities gate every /manage/ route and the shared mutation services, and
the separate All reservations browser is live); planned — the bearer
`reservations:read_all` cross-user list/detail API surface and its issuance
rules (NOT yet active).** This page records the selected M-GROUP-AUTHORIZATION
contract (ARCHITECTURE.md A-16; stable rows SAR-048–SAR-053, all UNPROVEN
until a fresh independent ICA at the exact merged revision).

## Available now

The delivered foundation and enforcement, and only this:

- **The ten documented application permissions** on the existing
  `Reservation` content type, in the `reservations` namespace
  (`book_assets`, `view_all_reservations`, `cancel_others_reservations`,
  `release_others_reservations`, `view_booking_policies`,
  `manage_booking_policies`, `view_maintenance_blackouts`,
  `manage_maintenance_blackouts`, `view_audit_history`,
  `export_audit_history`), registered through the model `Meta` and a
  forward migration. They are distinct from Administration model View
  permissions.
- **An optional opaque `User.external_identifier`** (max 128 characters,
  case-sensitive, populated values unique, unset is NULL) with a forward
  migration; existing accounts migrated to NULL with no inference or
  backfill. It is editable on the existing authorized user change page in
  the Administration only (not on the member profile, not in bearer API
  surfaces).
- **A small `accounts/authorization.py` constants/helper module**
  (`RESERVATIONS_PERMISSIONS`, `MANAGEMENT_PERMISSIONS`,
  `BOOKING_BASELINE_PERMISSION`, `has_reservation_permission`,
  `has_any_reservation_permission`, `is_management_user`) that checks
  explicit capabilities for an active authenticated non-service-account
  human through Django's permission machinery (groups combined additively
  with individual permissions; superuser semantics retained). It carries
  the active booking-eligibility enforcement (the `assets/authorization.py`
  predicate and the `create_reservation` gate build on it) and the active
  management capability enforcement (the `/manage/` route gates and the
  shared service guards). The planned bearer `reservations:read_all`
  surface will reuse the same current-permission checks. It caches nothing
  across calls.
- **A one-time baseline booking grant** in the accounts migration: existing
  non-service-account users (including inactive rows, so a later normal
  reactivation preserves their former baseline) received the direct
  `book_assets` grant. Service accounts received nothing; no group was
  created or changed; no other permission was granted.
- **`manage.py grant_management_access`**, an explicit dry-run-first setup
  command (see the deliberate upgrade section below).
- **Management capability enforcement**: the ten codenames above are
  enforced. `is_staff` alone admits `/admin/` only and confers **no**
  management-area access. Every `/manage/` route requires the documented
  reservations-namespace application permissions listed in the
  [route inventory](#management-route-inventory-enforced) for a current
  active non-service-account human session (anonymous sessions are redirected
  to login; authenticated sessions without the capability get a 403 before
  any protected record is fetched). The shared audited services recheck the
  relevant capability on the fresh row-locked principal
  (`manage_booking_policies` for policy create/update/deactivate,
  `manage_maintenance_blackouts` for blackout create/deactivate, and
  owner-or-capability for cross-user cancel/release), preserving the
  existing lock order, transaction and audit coupling and the existing
  denial codes. A mutation capability never implies read-all: a
  cancel/release-only principal that acts on a known UUID is redirected to
  the permitted management landing, never to a private detail page, and
  blackout previews without `view_all_reservations` show only the safe
  overlap count, never affected rows, UUIDs, names or free text.
  `book_assets` alone gives no management access, and Administration model
  View permissions are not sufficient (the All reservations browser needs
  `view_all_reservations` specifically). Partial-capability users receive a
  useful management landing showing only their authorized modules, counts,
  links and actions.
- **The separate All reservations browser** at the existing
  `/manage/reservations/` and detail routes, labelled "All reservations" /
  "Reservation details" (URLs and names unchanged; separate from the
  owner-scoped member pages). It requires `view_all_reservations`,
  including for staff, and reuses the existing validated asset/status/
  lifecycle/search/aware-from-to filters and the 50-per-page paginator,
  now with visible previous/next navigation that preserves all filters.
  Authorized readers see owner identity, asset, original and effective
  times, status and lifecycle with the existing half-open release/cancel
  history meaning; mutation controls appear only for the corresponding
  capability, and read-only viewers are denied even valid forged
  POSTs. The member bearer API is unchanged (owner-only) until the
  planned `reservations:read_all` surface.
- **Booking eligibility enforcement for NEW reservations**:
  `Asset.booking_restricted` (default False) and
  `Asset.allowed_booking_groups` (an M2M to the EXISTING `auth.Group`
  model; one new forward assets migration) plus a small shared
  `assets/authorization.py` predicate built on
  `has_reservation_permission(user, "book_assets")` and actual group
  membership. The predicate is enforced in the row-locked
  `create_reservation` service (after the fresh principal and asset locks,
  before any reservation/audit write), on the member browser reserve
  GET/POST surface (direct requests are denied, not only hidden buttons),
  as the bearer `POST /api/v1/reservations/` preflight BEFORE any cached
  idempotent creation response is returned, and on future legacy-import
  plans/apply (the documented completed-past historical exception is
  preserved). Every existing asset migrates unrestricted with an empty
  group list; staff, unrelated Administration permissions and
  inactive/service identities never bypass the gate, trusted active
  superusers keep global `has_perm` semantics but still need an allowed
  group on restricted assets, and owners keep list/inspect/cancel/release
  of existing bookings after losing the capability or a group.

Everything else on this page that is marked planned is still target
behavior: **the cross-user bearer list/detail routes, the
`reservations:read_all` token scope and its issuance rules are NOT
implemented yet** (the enforced application permissions are the booking
capability, exact-asset eligibility and the management capabilities
above). Endpoints and scopes named as target behavior are targets, not
published interfaces.

## Planned (enforcement NOT yet active)

- The cross-user bearer list/detail routes (the
  `reservations:read_all` scope), including token-scope issuance refusal
  for authority-exceeding read-all/create scopes and the minimal
  cross-user representation. The All reservations **browser** documented
  above is a separate web surface and is already live; this planned item
  is only the bearer API surface.
- No change to existing tokens, policies, exclusivity, lifecycle, audit or
  idempotency behavior; booking behavior already carries the active
  eligibility gate and management behavior already carries the capability
  gates documented above, and no further booking behavior change is
  planned in this target.

## Current baseline (implemented today)

- Member routes: active non-service-account human sessions; reservations
  are owner-scoped (list/detail/cancel/release of one's own records).
- Management routes (/manage/): explicit capability admission — each
  route requires the documented reservations-namespace application
  permissions (see the [route inventory](#management-route-inventory-enforced))
  for an active non-service-account human; cross-user lifecycle, policy and
  blackout operations run through the existing audited services, which
  recheck the same capability on the fresh row-locked principal.
  `is_staff` alone no longer admits /manage/.
- Administration (/admin/): staff admission with existing model
  permissions; protected records are read-only or service-backed. The user
  change page now exposes the optional external identifier.
- Bearer API: owner-only reservations:read/create/cancel/release plus
  availability:read; asset list/detail remain staff-session-only. The API
  accepts only its bounded known fields; `external_identifier` is not an
  API input.
- Booking eligibility is enforced for NEW reservations (global
  `book_assets` capability plus exact-asset group eligibility; restricted
  with no allowed groups fails closed; owners retain existing-booking
  lifecycle). The cross-user **bearer** read surface is still planned; the
  live cross-user web read surface is the All reservations browser.

## Permission matrix (enforced)

Grants combine by union across all of a user's groups and individual
permissions; there is no parallel membership, no hardcoded operator group
names and no explicit deny. Every application access still requires an
active non-service-account human.

| Application permission (reservations namespace) | Meaning (enforced) |
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

Application permissions are documented custom permissions in the
reservations namespace; they are distinct from Administration model View
permissions. A mutation capability without read-all must not incidentally
disclose another owner's record through redirects, overlap previews,
errors or audit. Partial-capability users receive a useful management
landing without unauthorized counts, data, links or actions.

## Management route inventory (enforced)

All 17 current `/manage/` routes and their required application
permissions (reservations namespace). Every route additionally requires a
current active non-service-account human session; anonymous requests are
redirected to login and authenticated requests without the capability
receive a 403 before any protected record is fetched. `manage` capabilities
include their module's read interface; no other rights are implied.

| Existing /manage/ route | Required application permission(s) |
|---|---|
| `/` (management dashboard) | Any of the nine management permissions, active human |
| `policies/` and `policies/<uuid>/` | `view_booking_policies` OR `manage_booking_policies` |
| `policies/new/`, `policies/<uuid>/edit/` (GET+POST), `policies/<uuid>/deactivate/` (POST) | `manage_booking_policies` |
| `blackouts/` and `blackouts/<uuid>/` | `view_maintenance_blackouts` OR `manage_maintenance_blackouts` |
| `blackouts/new/` (GET+POST), `blackouts/<uuid>/deactivate/` (POST) | `manage_maintenance_blackouts` |
| `reservations/` and `reservations/<uuid>/` | `view_all_reservations` ONLY (the model View permission is not sufficient) |
| `reservations/<uuid>/cancel/` (POST) | `cancel_others_reservations`; no implicit requirement or grant of read-all or release |
| `reservations/<uuid>/release/` (POST) | `release_others_reservations`; no implicit requirement or grant of read-all or cancel |
| `audit/` and `audit/<uuid>/` | `view_audit_history` ONLY |
| `audit/export.csv` | `export_audit_history` ONLY; existing filtered/bounded CSV behavior retained |

Notes: the shared services enforce the same capabilities server-side
(policy/blackout mutations and cross-user cancel/release), so hiding a
button or navigation entry never authorizes anything; a principal with a
mutation capability but without `view_all_reservations` may perform the
authorized action on a known UUID and is then redirected to the permitted
management landing, not to a private detail page; and blackout create/detail
previews for principals without `view_all_reservations` show only the safe
overlap count and the explicit confirmation requirement, never affected
rows, UUIDs, names, emails or free text.

## Admin vs staff

- **Staff** is admission to /admin/ only, with existing model permissions.
  Staff or unrelated Administration permissions confer **no** application
  management or booking bypass. The explicit capability grants from
  `grant_management_access` are direct application permissions, not
  implicit `is_staff` authority; per-model Administration access remains
  governed by the framework's model permissions.
- **Trusted active human superusers** retain Django's
  application-permission semantics and all protected-record/domain
  restrictions; they still meet exact-asset group eligibility when
  creating bookings. Administration can deliberately configure access,
  not bypass it through a reservation adapter.
- Enforcement is server-side at direct GET/POST endpoints and the shared
  services that serve them; buttons and navigation only reflect the same
  checks.

## Setting up grants: groups and individual permissions (operator procedure)

Application permissions are granted deliberately through the existing
Administration: the existing `auth.Group` model (Administration → Groups,
with its standard "Permissions" fieldset) and the user change page
(Administration → Users, with its "Groups" and "Permissions" fields).
Nothing in the application matches group names, infers flags or model
permissions from names, or enrolls users automatically: a group name
itself grants nothing, and every grant below is an explicit operator
choice.

**Group setup (reusable for many users):**

1. Administration → Groups → "Add group": choose any operator name (free
   text; an illustrative name like "Lab members" carries no application
   meaning).
2. On the group change page, tick the needed **application** permissions
   in the "Permissions" fieldset — the ten documented `reservations`
   namespace codenames (for example `reservations.book_assets`,
   `reservations.view_all_reservations`,
   `reservations.view_maintenance_blackouts`). They are listed separately
   from the per-model Add/Change/Delete/View permissions (such as
   `reservations.view_reservation` in Administration): a model View
   permission is not an application capability and never implies
   `reservations.view_all_reservations` or any other application
   permission.
3. Save the group, then assign it: Administration → Users → user change
   page → tick the group under "Groups" and save.

**Individual assignments (supported and unchanged):** the same ten
application permissions can be ticked directly under "Permissions" on a
user change page, without any group. Grants combine by union across all
of a user's groups and individual permissions: removing one group only
removes the grants that no other group or individual assignment still
provides, and a removed grant takes effect on the user's next request.
Non-staff users may receive any selected application permission,
including the nine management/read-all capabilities and the matching
/manage/ pages; the staff flag is required only for /admin/ admission
plus existing model permissions. Accounts created after the upgrade
receive no automatic application grants or group membership (the one-time
baseline grant applies only to existing humans).

**Illustrative roles (names are operator examples, never application
constants):**

| Illustrative role | Application permissions granted | Effect |
|---|---|---|
| Administrators | All ten `reservations` application permissions; staff flag plus the needed model permissions only if Administration access is intentionally configured | Full member and management capability: books (subject to exact-asset eligibility) and uses every /manage/ module; /admin/ only when deliberately staffed with model permissions. Still meets exact-asset group eligibility on restricted assets — no staff/superuser bypass. |
| Lab members | `reservations.book_assets`, `reservations.view_all_reservations` | Books (subject to exact-asset eligibility) and reads the All reservations browser; no cancel/release of other owners' reservations, no policy/blackout/audit rights unless separately granted. |
| Students | `reservations.book_assets` | Books (subject to exact-asset eligibility); the ordinary member surface already provides list/inspect/cancel/release of their own reservations. |
| Reservation readers | `reservations.view_all_reservations` | Read-only All reservations browser; no booking, no cancel/release of other owners' reservations, no policy/blackout/audit rights. |

These names are examples of what an operator might create; the
application contains no group-name constants, creates no groups, and
grants nothing by name. They exclude the three easy misreadings: no
automatic privileged membership (nothing is pre-populated for any named
group), no model View permission granting read-all (it does not), and no
administrator bypassing asset groups (it cannot — a restricted asset
still requires membership in at least one of its allowed groups in
addition to `reservations.book_assets`).

**Asset allowed-group membership** is configured separately on each
restricted asset (asset change page → "Allowed booking groups"): booking
a restricted asset additionally requires membership in at least one of
its listed existing groups, on top of `reservations.book_assets`;
unrestricted assets require only `reservations.book_assets`; there is no
implicit parent inheritance. Owners keep list/inspect/cancel/release of
already-accepted reservations after losing booking capability or group
membership. Existing tokens stay owner-only: the cross-user bearer
`reservations:read_all` scope and its issuance rules remain planned, not
implemented. This target promises no projects, deny policies, directory
or machine access.

## Exact-asset booking eligibility (implemented)

- Each asset is explicitly **unrestricted** or **group-restricted**.
- A restricted asset requires membership in **at least one** of its allowed
  existing groups; restricted with no allowed groups **fails closed**.
- Only the asset being booked is checked; there is **no implicit parent
  inheritance**.
- **All existing assets migrate unrestricted** in the upgrade.
- Allowed group names are free operator configuration (an operator might
  name a group for its bookers, for instance); the application contains no
  group-name constants and matches on the group objects themselves.
- Browser and bearer creation share the same authoritative check around
  the existing reservation service; token creation additionally requires
  the token's action scope and the owner's current capability/membership.
- Existing active/reservable/exclusive checks, UTC/DST rules, policies/
  counters, PostgreSQL exclusion/locking and atomic audit are unchanged.
- Assets remain browsable and show whether the member is eligible;
  sensitive account/group metadata is not disclosed.
- Access changes **never rewrite existing bookings**. Owners may still
  list/inspect/cancel/release accepted reservations after losing booking
  capability or asset-group membership, subject to existing lifecycle/
  cutoff rules.

## Future owner-only vs separate read-all bearer contract

- `reservations:read` remains **owner-only**, even for staff/superusers;
  existing token scope records never change automatically.
- A new explicit `reservations:read_all` scope authorizes cross-user
  list/detail routes **only when the owner also currently holds**
  `view_all_reservations`; both are rechecked per request; there is no
  process-global grant cache; group/permission removal takes effect on
  subsequent requests with the same token.
- Issuance refuses authority-exceeding read-all and create scopes;
  expiry/revocation, activity, service-account and shared abuse controls
  apply unchanged.
- There is **no cross-user bearer mutation surface** in this target.
- The cross-user representation is minimal and explicit: reservation/asset
  UUID and safe asset identity, owner UUID plus external_identifier (null
  when unset), aware original start/end, effective_end, status/lifecycle,
  release/cancellation timestamps and unambiguous blocking/effective
  interval semantics. It excludes owner email/display/profile/admin flags,
  passwords/verifiers/token secrets, private locators, unrelated metadata
  and private purpose/cancellation/blackout free text. Owner
  representations stay compatible.

## External identifier and external enforcer boundary (implemented field; target enforcement)

- Optional `external_identifier` on the existing user: opaque,
  case-sensitive, at most 128 characters, numeric strings and leading
  zeroes preserved; populated values unique; unset is NULL (multiple users
  may be unset); no inference or backfill; existing accounts remain unset.
  Available now: the field, the unique constraint and admin-only
  editing on the existing user change page.
- Only authorized account administrators edit it in existing
  Administration; the member profile and bearer API cannot modify it
  (verified by tests). It may represent an external account identifier
  (including a Linux UID), but the application treats the value as
  opaque: it is not validated as a UID, it is not a credential, it
  grants no machine access, and it does not replace the account's
  UUID, email, password or token identity.
- The **external enforcer** owns account mapping, enforcement, polling,
  caches/refresh and outages. No SSH/PAM, account synchronization,
  workload/container execution, GPU allocation or automatic machine login
  grants enter this application. Reservation entitlement is not login
  authority.

## Deliberate upgrade (implemented foundation; operator steps)

- The explicit migrations preserve users/groups/reservations/policies/
  audits/tokens and old individual permissions; the populated-upgrade test
  proves row preservation and grant scope against a real pre-upgrade
  database state.
- **Baseline booking grant scope (one-time):** the migration added ONLY
  `reservations.book_assets` as a direct individual permission to every
  existing non-service-account user (inactive rows included); service
  accounts received nothing and no management/read-all permission was
  granted. This mirrors the pre-target behavior in which any active human
  could book. It does not restore or grant anything else.
- **New users:** accounts created after the upgrade receive **no**
  automatic application grants or privileged-group membership. To let a
  new user book, grant `reservations.book_assets` (directly or via an
  operator group) deliberately; the required booking grant is explained in
  this guide and is stated in the account, group and asset Administration
  help (booking enforcement is active).
- **Explicit chosen-staff upgrade steps (dry-run first; supported Docker
  workflow):** follow [INSTALL.md](../INSTALL.md) — recover the
  installation's recorded Compose project name into
  `SAR_COMPOSE_PROJECT` and keep the same project name and database volume
  identity (never rename or adopt another project's volume).
  The one-off container form (`run --rm app`) uses the current application
  image and does NOT require the long-running app service to be up, so the
  steps can run before the public service restart:
  1. Take an operator backup of the deployed database first (INSTALL.md
     section 8; real deployments remain operator-owned; these migrations
     are tested only on owned synthetic databases).
  2. `docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app python manage.py migrate --noinput`
     (applies the permission records, the `external_identifier` column and
     the one-time baseline grant).
  3. Choose the current active human staff accounts whose management
     authority you deliberately retain; there is no mass staff grant and
     no automatic enrolment. Each account's UUID is the `<STAFF_UUID>` in
     its existing Administration user change URL
     (`/admin/accounts/user/<STAFF_UUID>/change/`).
  4. Review with the DEFAULT dry-run (pass no `--apply`; the command has
     no `--dry-run` flag), repeating `--user` for every selected account:
     `docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app python manage.py grant_management_access --user <STAFF_UUID> [--user <STAFF_UUID> ...]`
     The dry-run validates every selection (existing, active,
     non-service-account staff) before reporting what would be granted,
     and writes nothing.
  5. Grant with the explicit `--apply`: the same command plus `--apply`
     grants the nine management/read-all capabilities (all ten except
     `book_assets`, which stays separate) as direct permissions to exactly
     the selected accounts. The command validates every selection before
     any write, applies atomically and idempotently, never creates users,
     changes staff/superuser flags or groups, and never grants read-all
     from old Administration View permissions. Use this command only when
     the operator chooses to preserve the full legacy staff management
     authority; partial or non-staff grants use the existing
     Administration groups/individual permissions (see [Setting up
     grants](#setting-up-grants-groups-and-individual-permissions-operator-procedure))
     — no new flags and no expanded command.
  6. Verify the selected grants: re-run the default dry-run, which now
     reports each selected account at `9/9 direct grant(s) present` with
     `nothing (idempotent)`.
  7. Restart the application on the new image (INSTALL.md step 6) and
     access-check: a selected account sees its expected /manage/ modules;
     an unselected staff account no longer enters /manage/.
- **Backup and reverse limits (honest):** downgrading does **not**
  silently revoke the baseline booking grant or any operator-configured
  grant (removing grants is a deliberate operator action); Git rollback of
  the code does **not** restore identity data or revert an applied
  database; a real upgrade requires an operator backup/restore plan. The
  new asset booking configuration (`booking_restricted` and the
  allowed-group list) is ordinary database state: normal database backups
  include it and restoring from such a backup restores it; dropping or
  reverting that migration after the fact would delete that configuration,
  and a code rollback does not restore it.

## Deferrals unchanged by this target

Projects, organizational trees, delegated group ownership, general policy
languages, token/management admin or mutation bearer APIs, OIDC/password
reset/notifications, monitoring stack, scheduler, automatic physical
allocation, real migration/cutover and the execution gateway remain
deferred (SAR-036 as amended by A-16). This target adds no execution,
deployment or real-infrastructure authority.
