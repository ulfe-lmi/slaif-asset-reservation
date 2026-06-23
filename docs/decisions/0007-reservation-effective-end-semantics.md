# ADR 0007: Reservation Effective-End Semantics

**Status:** Accepted
**Date:** 2026-06-22

## Context

Exclusive reservations need to preserve the originally confirmed interval while allowing an early
release to free the unused future remainder. The database exclusion constraint needs one stable
blocking interval to evaluate for confirmed and released reservations.

## Decision

- `end_at` is the immutable originally confirmed end of a reservation.
- `effective_end_at` initially equals `end_at`.
- Early release sets `released_at` and `effective_end_at` to the same server-authoritative instant.
- Cancelled reservations do not block future reservations.
- Confirmed and released reservations participate in exclusivity over `[start_at, effective_end_at)`.
- A released reservation preserves its actually occupied historical interval while freeing the
  unused future remainder.
- `completed` is derived from time and is not stored as a lifecycle status.
- Release is valid only while a reservation is active: `start_at < now < effective_end_at`.
- Cancellation applies only before start and leaves `effective_end_at` equal to the original end.
- Rescheduling remains cancel-and-create.
- Duration, lifecycle, lead-time, booking-horizon, cutoff, overlap, and counter calculations use
  UTC-normalized absolute instants. Local-zone datetimes must be converted before arithmetic;
  nonexistent or ambiguous wall times are rejected by the wall-time parser rather than guessed.

## Consequences

The reservation table stores both original and effective end timestamps. The PostgreSQL exclusion
constraint uses `TSTZRANGE(start_at, effective_end_at, '[)')` for confirmed and released rows.
Adjacent ranges are valid. Any future availability or API layer must use the same effective blocking
interval and must not infer a persisted `completed` status from elapsed time. Tests cover Ljubljana
spring and autumn DST transitions so policy duration is measured by elapsed absolute time rather
than apparent wall-clock difference.
