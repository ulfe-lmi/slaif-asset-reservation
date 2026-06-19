# ADR 0002: PostgreSQL Enforces Reservation Integrity

- **Status:** Accepted
- **Date:** 2026-06-19

## Context

Availability reads are inherently subject to races. Application-only overlap checks can allow two concurrent clients to reserve the same exclusive asset. The initial domain requires reliable exclusive time ranges.

## Decision

Use PostgreSQL 17 as the persistence and consistency authority.

- reservation intervals use aware timestamps and half-open `[start, end)` semantics;
- active blocking reservations on one exclusive asset are protected by a PostgreSQL GiST exclusion constraint or an equivalent reviewed PostgreSQL invariant;
- application validation provides useful errors, but the database constraint is final;
- constraint violations are translated to a stable domain/API conflict;
- CI and development use PostgreSQL for invariant tests.

## Consequences

### Positive

- correctness survives multiple workers and concurrent requests;
- adjacent reservations remain possible;
- consistency does not depend on process-local locks;
- transactional audit coupling is straightforward.

### Negative

- PostgreSQL is mandatory;
- migrations require careful extension/constraint handling;
- release semantics need an explicit effective-end representation;
- concurrency tests are more complex than ordinary unit tests.

## Rejected

- SQLite as primary database;
- Redis locks as reservation truth;
- application pre-check without database enforcement;
- a single web worker as a concurrency control.
