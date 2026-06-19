# Human UI Requirements

**Status:** product/UX baseline; visual system is selected in a later scoped PR

## 1. UX goals

The interface should make shared-resource scheduling understandable without exposing implementation terminology. Users should answer four questions quickly:

1. What can I reserve?
2. When is it available?
3. What have I reserved?
4. Why was my request rejected?

The UI and agent API share domain operations and policy. The browser is not a privileged bypass.

## 2. Information architecture

### Member navigation

- Dashboard
- Assets
- Calendar / availability
- My reservations
- API tokens
- Profile / timezone

### Manager/admin navigation

- All reservations
- Machines and assets
- Availability and maintenance
- Policies
- Users, projects, and memberships
- API tokens/service accounts
- Audit log
- System status

Django admin remains available to authorized operators but is not the primary member UX.

## 3. Core screens

### Dashboard

Show:

- active reservation, if any;
- next upcoming reservations;
- assets available now, limited to permitted assets;
- recent conflicts or actionable notices;
- clear create-reservation action.

### Asset explorer

Each asset card/row shows:

- name and parent machine;
- hardware/capability summary;
- active/reservable/maintenance status;
- next available time;
- tags/location;
- link to details and availability.

Filters must be URL-addressable where practical so views can be shared/bookmarked.

### Asset detail

Show:

- verified inventory metadata;
- policy summary relevant to current user;
- timezone;
- availability calendar/list;
- upcoming reservations with privacy-safe visibility;
- reserve action;
- maintenance notices.

Do not expose another user's purpose or identity unless policy explicitly permits it. A busy interval may be shown as unavailable without personal detail.

### Create reservation

Inputs:

- asset;
- date and start/end or duration;
- display timezone;
- purpose;
- optional project;
- policy summary before submit.

Behavior:

- server-side validation is authoritative;
- show local and absolute time clearly;
- explain min/max duration and horizon;
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

### API tokens

Human user can:

- create a named token within allowed scopes;
- choose expiry and permitted project/resource limits where policy allows;
- see plaintext once with a strong warning;
- list prefix, scopes, created/expiry/last-used state;
- revoke immediately;
- never retrieve token plaintext again.

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
