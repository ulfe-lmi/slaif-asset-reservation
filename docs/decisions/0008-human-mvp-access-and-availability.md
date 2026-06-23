# ADR 0008: Human MVP Access and Availability

**Status:** Accepted
**Date:** 2026-06-23

## Context

Work Orders 0001-0003 established the executable Django/PostgreSQL foundation, asset inventory,
reservation policy core, authoritative reservation services, and PostgreSQL conflict enforcement.
The next internal pre-alpha slice needs ordinary human users to exercise that core through
server-rendered pages without introducing project/group authorization, availability-rule models, or
reservation API mutations prematurely.

## Decision

The human MVP uses Django sessions, CSRF protection, server-rendered templates, local static assets,
and no JavaScript framework. Only active, non-service-account users may use member routes. Accounts
are created by administrators; there is no self-registration, password reset, OIDC, social login, or
remember-me function in this slice.

Until project/group authorization is implemented, every active human account may browse active
assets and request any active, reservable, exclusive asset with an unambiguous effective policy. This
broad authenticated-member access is temporary internal-alpha behavior and must be documented
prominently. Staff users using member routes are still limited to their own reservations; staff
cross-user operations remain deferred to a management UX.

Availability is derived from reservation records, asset state, and effective policy only. It exposes
busy time without another user's identity, email, purpose, cancellation reason, or reservation UUID.
The current user's own busy intervals may be labelled and linked. Availability reads are advisory:
the authoritative create service and PostgreSQL exclusion constraint decide whether a creation
actually succeeds.

AvailabilityRule, Blackout, maintenance scheduling, operating-hour models, project authorization,
agent reservation API mutations, and API-token idempotency remain deferred. Coarse maintenance is
represented only by asset `active` and `reservable` state in this slice.

## Consequences

- The browser adapter can be useful for internal testing without weakening the single reservation
  engine invariant.
- Member access is intentionally broader than the future authorization model and must not be treated
  as production-ready.
- Availability is simple, privacy-safe, and testable, but it cannot represent maintenance windows or
  operating hours until later models are accepted.
- Login rate limiting is not implemented in Django in this slice; public deployment requires a later
  authentication hardening slice or trusted reverse-proxy rate limiting.
