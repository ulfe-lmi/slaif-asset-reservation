# Browser guide

SLAIF Asset Reservation provides a public entry page, an authenticated member
workspace, staff management and a branded administration interface.

## Sign in

Open `/` and choose **Log in**. An administrator must first create your account;
your email address is the login identifier. There is no self-registration,
institutional single sign-on or password-reset/email workflow. Contact an
administrator if you need a password changed. Service accounts cannot use the
human login or administration interface.

The public **Administration** action opens `/admin/login/`. Administration
requires an active human staff account and the applicable model permissions;
superuser status does not bypass the active-human admission boundary.

Member and administration sign-in attempts share temporary PostgreSQL-backed
abuse budgets. A 429 response asks you to wait and retry; 503 means sign-in
is temporarily unavailable. There is no permanent automatic account lockout.

## Members

| Task | Where | Behavior |
| --- | --- | --- |
| See your bookings | Dashboard `/` and `/reservations/` | Active, upcoming and historical reservation sections belong to your account. |
| Find an asset | `/assets/` | Filter active assets by name/slug/description, kind, parent, tag and reservable state. |
| Check availability | `/assets/<uuid>/` | Advisory free/busy intervals; other owners' identity and purpose are not disclosed. |
| Make a booking | Asset's **Reserve this asset** action | Current policy, maintenance and PostgreSQL conflict checks decide acceptance. |
| Cancel or release | Your reservation detail | Cancel upcoming bookings; release active bookings early. Both actions are explicit and audited. |
| Set your display preferences | `/profile/` | Display name and a required valid IANA timezone, used when entering and displaying booking times. |
| Connect an API agent | `/tokens/` | Create scoped, expiring tokens, inspect their prefix/status and revoke them. |

Accounts currently have broad access to active reservable exclusive assets with
an effective policy. Site permission groups are not project memberships or
resource-access restrictions. Staff-only internal location/physical metadata
is not part of the member inventory.

### Times and reservation rules

Reservations use half-open intervals: the start is included, the end is free
again. Times are stored in UTC and shown/entered in your profile timezone.
The asset timezone is display metadata; it does not override your profile.

On a daylight-saving fall-back, a clock time can occur twice. **Start occurrence**
and **End occurrence** are only relevant to that ambiguity: choose the first
or second occurrence explicitly. Automatic is rejected for ambiguous times,
and a nonexistent spring-forward time is rejected for every choice.

The fresh-install global policy `default` permits starts within the next seven
days and durations from one minute to 48 hours. It adds no lead time, advance
cancellation cutoff, required purpose or operating-hour window. Limits also
apply per account across its assets and tokens: 50 upcoming bookings, and fewer
than eight existing blocking records may intersect a proposed booking.
Staff can configure different policies. Exact asset policy takes priority,
then parent machine, then global fallback; missing or ambiguous policy fails
closed. See [Installation](../INSTALL.md) for initialization and upgrade behavior.

Availability helps choose a time; it is not a booking guarantee or proof that
hardware is online. Accepted reservations are entitlements. The application
neither runs workloads nor enforces physical usage.

#For a short reservation, select the start in your profile timezone and choose
**1 hour**, **2 hours** or **4 hours** when the policy permits it. **Custom end time**
retains explicit end entry. Quick choices measure elapsed time from the interpreted
start, including DST changes. The picker shows current lead-time/horizon bounds;
the service checks the policy and availability again when you submit.

## API tokens

The creation form describes each scope in human language and explains token
lifetime. Machine scope values remain part of the [API contract](api-contract.md).
The reserved asset-inventory scope grants no asset discovery today: those
endpoints remain staff-session-only.

Token plaintext appears once after creation. Store it in an approved local
secret store; it cannot be recovered later. Token list and administration views
show only a prefix. Revocation takes effect immediately. The one-time page
uses private/no-store caching and clears its displayed secret on browser history
transitions; do not share or capture it.

## Staff management

Active human staff use `/manage/`; per-model administration permissions do not
by themselves grant management access.

- **Policies:** inspect effective rules, create/update policies and deactivate
  them. Global targets are fallback rules; duration units, start horizon,
  lead/cancellation effects and account limits have nearby explanations.
  Deactivation changes new booking eligibility, not existing reservations.
- **Blackouts:** stop new overlapping reservations on one selected asset.
  Existing affected bookings are shown for staff follow-up; a blackout does
  not automatically cancel them or block every child/sibling asset.
- **Reservations:** filter and inspect cross-user bookings and perform audited
  cancellation/release actions with contextual warnings.
- **Audit:** filter events and inspect correlation/source information. CSV
  export uses the current filters, with a bounded row count; without filters
  it covers the last seven days. Treat exported account/reservation data as
  private operator material.

## Administration

Administration manages user accounts, site permission groups, assets and tags
where the account has the corresponding model permissions. Account fields
explain staff/superuser/service-account effects. Password state is a safe status;
the stored password verifier is never displayed. The password-change form
explains that disabling password authentication loses the current password and
that no alternate human login backend is provided.

Policies, reservations, blackouts, audit events and API tokens are protected
read-only records in administration. Their guidance identifies the supported
management or account-owned mutation route; appearance does not relax those
boundaries.

## Navigation and appearance

Wide screens show member and staff navigation in the header. On narrow screens,
**Menu** opens it; Escape closes it and restores button focus. Forms retain
visible labels and associated help. Wide tables scroll inside their own region
without widening the page.

The default [SLAIF design](ux/visual-design.md) uses packaged fonts and images.
Operators may supply safe, read-only [branding overrides](branding.md) without
rebuilding the image. Product identity remains SLAIF Asset Reservation.

## Related documentation

[Quickstart](../QUICKSTART.md) · [Installation](../INSTALL.md) ·
[API contract](api-contract.md) · [Security model](security-model.md) ·
[Form guidance inventory](ux/form-guidance-inventory.md) · [Testing](../TESTING.md).
