# ADR 0006: UTC, Half-Open Ranges, and Idempotent Agent Mutations

- **Status:** Accepted
- **Date:** 2026-06-19

## Context

Reservations cross browser, API, database, and local time zones. Agents may retry after network failures. Ambiguous time semantics or non-idempotent mutation can produce overlap, duplicate reservations, and misleading lifecycle behavior.

## Decision

- store aware timestamps representing UTC instants;
- default display timezone is `Europe/Ljubljana`, user-selectable later;
- reservation ranges are half-open `[start_at, end_at)`;
- ambiguous/nonexistent local times are not silently guessed;
- agent mutation endpoints require `Idempotency-Key`;
- key scope includes principal and action;
- same key/same request returns prior result;
- same key/different request returns a conflict;
- correlation IDs are returned and recorded in audit events.

## Consequences

### Positive

- adjacent reservations are unambiguous;
- DST behavior is testable;
- retries do not create duplicate reservations;
- client and server evidence can be correlated.

### Negative

- idempotency storage and canonical request hashing add complexity;
- UI must clearly display timezone;
- release/effective-end semantics need explicit fields and tests.
