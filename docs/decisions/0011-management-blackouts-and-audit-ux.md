# ADR 0011: Management Blackouts and Audit UX

## Status

Accepted for Work Order 0007.

## Context

Work Orders 0001 through 0006 established the executable foundation, human reservation UI, scoped
API tokens, bearer API reservation operations, idempotency, and audit evidence. Operators now need a
purpose-built management surface for policies, coarse maintenance unavailability, cross-user
reservation inspection and lifecycle actions, and audit review without turning Django admin or
ordinary member routes into privileged scheduling adapters.

## Decision

Management routes live under `/manage/` and are separate from ordinary member routes. They require
an authenticated active staff user and reject service accounts. Superusers qualify through
`is_staff`; ordinary active humans, inactive users, anonymous users, and service accounts do not.
Staff users on ordinary member routes remain owner-scoped and cannot view, cancel, or release
another user's reservation there.

Management mutations use domain services or audited management services. Policy create, update, and
deactivate continue through the audited reservation-policy services. Reservation cancellation and
release for another user call the same authoritative lifecycle services with management/admin
source attribution. Management routes use POST plus CSRF for mutations; GET does not mutate.

Maintenance blackouts are coarse operational unavailability windows, not a general
`AvailabilityRule` or operating-hours model. A blackout targets one asset, has an aware half-open
time interval, a bounded staff-visible reason, active/deactivation state, creator/deactivator
metadata, and audit evidence. Active blackouts:

- block future reservation creation through the authoritative reservation service;
- appear as unavailable intervals in human and API availability;
- merge with reservation busy intervals for presentation;
- hide the private reason from ordinary members and API callers.

Blackout creation is conservative. If confirmed or released reservations overlap the proposed
blackout, the management form must show the affected reservations and require explicit confirmation.
Creating a blackout does not automatically cancel or release those reservations in this slice.
Deactivation is audited and preserves history.

Audit browsing and export are staff-only and read-only. CSV export is bounded and
privacy-minimized. It includes fixed safe columns and existing safe metadata, not bearer tokens,
Authorization headers, cookies, CSRF values, verifiers, peppers, raw request bodies, private
physical locators, reservation purpose, or cancellation reason text. This is an operational review
surface, not a complete forensic dump.

Production rate limiting, delegated resource-manager roles, projects/groups, resource restrictions,
automatic notification, and administrative APIs remain deferred.

## Consequences

The management UX provides real operational controls without weakening the single reservation engine
invariant. Blackout checks add an application/domain invariant that complements, but does not alter,
the PostgreSQL reservation-vs-reservation exclusion constraint. Availability remains advisory, while
reservation creation treats active blackout overlap as authoritative `blackout_conflict`.

Django admin remains conservative. Where admin editing cannot prove service-backed audited
mutation, it stays read-only.
