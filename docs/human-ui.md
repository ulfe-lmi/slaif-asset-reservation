# Human UI Requirements

**Status:** internal-alpha human MVP implemented; visual polish remains deferred

## 1. UX goals

The interface should make shared-resource scheduling understandable without exposing implementation terminology. Users should answer four questions quickly:

1. What can I reserve?
2. When is it available?
3. What have I reserved?
4. Why was my request rejected?

The UI and agent API share domain operations and policy. The browser is not a privileged bypass.

## 2. Information architecture

### Public entry

Signed-out visitors see a public landing page at `/` with the SLAIF Asset
Reservation identity, the shared-lab reservation purpose, and two actions:
**Log in** (`/login/`) and **Administration** (`/admin/login/`). The page
carries no private data: no asset, user, reservation, token, audit details,
or counts. The administration area is product-branded ("SLAIF Asset
Reservation administration") and rejects inactive and service-account
identities at its login exactly as member login does; no browser surface
shows framework branding.

### Member navigation

- Dashboard
- Assets
- Availability list on asset detail/reserve pages
- My reservations
- Profile / timezone
- API tokens

API-token management is implemented in Work Order 0005 for active human owners.

### Manager/admin navigation

- Management dashboard
- Policies
- Maintenance blackouts
- Cross-user reservations
- Audit log and safe export
- Machines/assets through Django admin in this slice

Work Order 0007 implements the `/manage/` staff-only management area for the listed policy,
blackout, reservation, and audit workflows. Django admin remains available to authorized operators
but is conservative/read-only where direct editing would bypass audited services.

## 3. Core screens

### Dashboard

Implemented in Work Order 0004:

- active reservation, if any;
- next upcoming reservations;
- links to active asset browsing and own reservations;
- honest empty states.

### Asset explorer

Implemented member asset cards/rows show:

- name;
- kind;
- parent machine;
- reservable state;
- verification-required state;
- link to details and availability.

Implemented filters are URL-addressable: kind, parent, tag, reservable, and safe text search. Only
active assets are visible to member pages; inactive assets remain administrator/admin-only.

Richer public capability/location summaries, maintenance state, and next-available summaries remain
deferred until those data contracts are implemented. The member UI must not invent verified hardware
facts from imported display text.

### Asset detail

Show:

- verified inventory metadata;
- policy summary relevant to current user;
- timezone;
- availability calendar/list;
- upcoming reservations with privacy-safe visibility;
- reserve action;
- advisory textual availability.

Do not expose another user's purpose or identity unless policy explicitly permits it. A busy interval may be shown as unavailable without personal detail.

### Create reservation

Inputs:

- asset;
- date and start/end or duration;
- display timezone;
- purpose;
- explicit DST fold/occurrence fields where needed.

Behavior:

- server-side validation is authoritative;
- show local and absolute time clearly;
- explain min/max duration and horizon;
- fresh installs provide the `default` global fallback policy with these
  explicit defaults: minimum 1 minute, maximum 2880 minutes (48 hours /
  2 days), 7-day horizon by reservation START, zero lead and cancellation
  cutoff, purpose optional, no operating-hour window, and per principal
  (across assets and that principal's API tokens) 50 upcoming reservations,
  and a new booking requires fewer than 8 existing blocking records
  intersecting the proposed interval (8 or more existing intersecting
  records rejects it; the new record would be the 8th). This is a count of
  records intersecting the proposed interval, not a maximum
  simultaneous-occupancy sweep;
- on conflict, preserve input and suggest available alternatives where feasible;
- prevent accidental duplicate submit, but still rely on server correctness;
- confirmation shows asset, start, end, timezone, and reservation ID.

### My reservations

Separate active, upcoming, and past. Actions:

- cancel future reservation;
- release active reservation;
- copy stable reservation ID;
- inspect lifecycle/audit-visible facts;
- no hard delete.

The implemented member pages show only the current user's reservations. A guessed or other-user UUID
returns a non-disclosing 404. Staff users on member routes do not get a hidden cross-user bypass.
Active, upcoming, completed, cancelled, and released reservation sections are database-filtered and
bounded with independent pagination parameters rather than loading the complete reservation history
into memory.

### API tokens

Implemented in Work Order 0005. Human users can:

- create a named token within allowed scopes;
- choose expiry up to the configured maximum;
- see plaintext once with a strong warning;
- list prefix, scopes, created/expiry/last-used state;
- revoke immediately;
- never retrieve token plaintext again.

Project/resource limits, service-account issuance, administrative issuance/revocation, token API
endpoints remain deferred. Bearer-enabled `/me`, advisory availability, and owner reservation
operations are implemented in Work Order 0006, but they do not change the server-rendered human UI
paths.

### Administration

Professional workflows should avoid editing raw JSON for common actions. Build purpose-specific forms for:

- asset activation/reservability;
- maintenance blackout;
- policy settings;
- membership and resource-manager assignment;
- token/service-account revocation;
- conflict-aware administrative reservation changes.

## 4. Calendar behavior

Start with a resource/time view that works well for tens of assets, not an enterprise scheduler clone.

Required:

- day/week navigation;
- filter by machine, asset kind, tag, capability, and status;
- current-time marker;
- status legend not dependent on color alone;
- keyboard-accessible reservation links;
- timezone visible at all times;
- no 5-minute visual grid requirement merely because the legacy system used one.

The policy may allow minute-level start times or a configurable granularity. The UI should not create a salon-like list of duration services.

## 5. Accessibility

Target WCAG 2.2 AA principles:

- semantic landmarks, labels, and tables;
- complete keyboard operation;
- visible focus state;
- sufficient contrast;
- error summaries and field-linked errors;
- no color-only meaning;
- touch targets suitable for mobile;
- reduced-motion respect;
- screen-reader-friendly calendar alternatives, such as an availability list.

Work Order 0004 implements the availability list, not a drag-and-drop calendar. It is advisory.
Work Order 0007 adds maintenance blackouts as unavailable intervals, but operating hours and full
maintenance calendars remain deferred. Local-day display windows are interpreted
through the user's configured IANA timezone. If a requested local-day boundary is nonexistent or
ambiguous, the request fails closed with a safe bad-request response instead of guessing an offset or
silently substituting another timezone.

Authenticated member pages display the current "times shown in" timezone in the shared shell.
Availability sections repeat the interval display timezone, and asset detail pages label the asset's
own timezone separately.

Automated accessibility checks supplement, not replace, manual keyboard and screen-reader review.

## 6. Responsive behavior

Desktop may use a multi-resource calendar. Mobile should use:

- asset filter;
- one asset or day at a time;
- compact upcoming reservation cards;
- simple date/time fields or accessible picker;
- no horizontal calendar dependency for completing core work.

## 7. Visual system

Choose a small local design system in a dedicated UI PR. Requirements:

- no mandatory Node SPA toolchain for core pages;
- production assets are pinned and served locally;
- components support accessibility and dark/light contrast if themes are offered;
- consistent spacing, typography, forms, badges, alerts, and empty states;
- avoid vendor CDN runtime dependencies.

## 8. Content language

Initial UI language is English. Architecture should not prevent later Slovenian localization. Use Django translation functions for user-facing strings from the beginning where reasonable.

Use domain language:

- asset, machine, GPU, reservation, availability, maintenance, project;
- not employee, staff provider, service, appointment, client, or price.

## 9. Privacy in UI

- never show bearer tokens after creation;
- never render secrets into HTML data attributes;
- avoid exposing reservation owner/purpose in shared calendars unless authorized;
- show audit metadata only to permitted roles;
- use generic conflict messages for hidden reservations;
- do not require phone numbers.

## 10. Browser testing

Before internal alpha, Playwright tests cover at least:

- login and logout;
- asset browse/filter;
- create reservation;
- conflict feedback;
- cancel future reservation;
- release active reservation with controlled clock;
- create/revoke token without leaking it after creation;
- unauthorized page access;
- keyboard navigation smoke path.

Work Order 0004 adds headless Chromium tests for the implemented login/logout, member browsing,
profile, reservation creation/conflict, own detail, cancellation, release, other-user denial, and
keyboard smoke paths.
## 11. Field and choice guidance (SAR-044)

Every non-obvious form control renders meaningful help nearby, associated
through matching element IDs and `aria-describedby` (checkbox groups use an
accessible fieldset with a legend). The complete control inventory and
coverage map — bound forms, inherited and model-generated admin fields,
dynamically renamed fields and raw template filters — is
`docs/ux/form-guidance-inventory.md`.

Member surfaces: login explains that accounts are administrator-created and
self-registration is not available; profile explains the required IANA
timezone with no blank fallback; the reservation form explains start/end in
the user's timezone, and the daylight-saving occurrence pickers explain the
real rule: on a fall-back day the clock time repeats and Automatic is
rejected (choose First = the earlier or Second = the later occurrence),
while a time inside the spring-forward gap does not exist and is always
rejected; purpose is marked optional unless the asset's policy requires it; cancel and release actions warn about their
irreversible effects; the token form shows human-readable scope labels with
a one-line effect per scope (`assets:read` is reserved and grants nothing
today), and the token list and one-time display use the same human labels
while stored and wire values stay the machine strings. Raw asset filters
(search/kind/parent/tag/reservable) and the availability "latest valid
start" note are explained in place.

Staff surfaces: every policy field explains its effect in real units
(duration in minutes with day equivalents that keep remainder minutes,
horizon limits how far a booking may START, lead/cutoff semantics, upcoming
versus overlapping-record counters — the overlap cap counts existing records
intersecting the proposed interval, not simultaneous occupancy); policy
names are presented as non-unique (only the active target is constrained);
the policy detail renders humanized units (for example 2890 minutes as
"2 days, 10 minutes"); the blackout form carries the same corrected
daylight-saving occurrence rule as the member reservation form and explains
exact-asset behavior and that creating a blackout never cancels or releases
existing reservations; deactivation actions carry explicit warnings;
reservation and audit filters label and explain every selector, including
the renamed `from`/`to` start-range fields (aware ISO-8601).

Administration: user add/change explains each flag's actual effect —
entry to the management area and the administration follows the active
staff flag with an active, non-service-account session (never arbitrary
permission selections, and superuser status does not bypass that gate),
while individual/group permissions control per-model operations; the
initial password is set by the administrator because members have no
self-service password change (the profile page edits display name and
timezone only); the editable last_login/date_joined fields explain their
UTC meaning and that edits are corrections, not booking logic; the user
change page replaces the inherited password-hash summary with a safe status
("Password set" / "No password set" / "Password disabled") plus the real
per-user password-change action; that action's enable/disable choice
explains that disabling loses the current password and that this deployment
provides no alternate human login backend; asset forms explain the actual
rules (only a machine can parent children and a machine has no parent; the
slug is a stable display/search label while routes use UUIDs; the asset
timezone is display metadata, availability follows each member's profile
timezone; exclusive booking mode); protected policy/reservation/
blackout/audit/token pages are read-only with banners naming the supported
mutation path.

Guidance is presentation only: validation, permission, admission, wire and
storage behavior are unchanged, and user-visible copy uses domain language
without framework or work-order text.
