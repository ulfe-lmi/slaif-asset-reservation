# API v1 Design Contract

**Status:** pre-alpha implementation contract. Staff asset list/detail endpoints, bearer `/me`,
bearer advisory availability, and bearer owner reservation endpoints are implemented. Token
lifecycle APIs, administrative APIs, projects, memberships, resource restrictions, and API
throttling remain deferred.

**Base path:** `/api/v1/`

The generated OpenAPI document is the mechanical schema source of truth. This document records the
intended semantics that must stay aligned with implementation.

## Principles

- Human UI and API clients use the same reservation domain services.
- Bearer-token authentication is enabled only on the implemented token-authenticated endpoints.
- Existing staff-session asset list/detail endpoints remain staff-session-only.
- IDs are opaque UUIDs.
- API timestamps are aware ISO-8601 instants and are serialized as UTC.
- Mutation endpoints require idempotency.
- Errors use privacy-safe problem-details JSON.
- Responses never expose bearer tokens, verifiers, peppers, physical locators, raw provenance, audit
  internals, or another user's identity/purpose.

## Authentication and Scopes

```http
Authorization: Bearer sar_<token_uuid_hex>_<secret>
```

The server stores only an HMAC-SHA-256 verifier using the dedicated API-token pepper. The bearer
authenticator is not registered globally.

Implemented bearer scopes:

```text
assets:read
availability:read
reservations:read
reservations:create
reservations:cancel
reservations:release
```

Work Order 0006 uses:

- `availability:read` for asset availability;
- `reservations:read` for reservation list/detail;
- `reservations:create` for reservation creation;
- `reservations:cancel` for cancellation;
- `reservations:release` for early release.

The existing `/api/v1/assets/` and `/api/v1/assets/{asset_id}/` endpoints still require a staff
session. Bearer `assets:read` does not grant those endpoints in this slice.

## Idempotency

Mutation endpoints require:

```http
Idempotency-Key: <client-generated opaque value>
```

Key rules:

- 8 through 128 printable ASCII characters;
- no whitespace or control characters;
- not a secret.

Records are scoped by owner, API token, action, and key. The server stores a SHA-256 hash of a
canonical JSON request containing action, method, path, and parsed body. It does not store bearer
tokens, Authorization headers, raw request bodies, cookies, CSRF values, token secrets, verifiers,
peppers, or passwords.

For the same owner, token, action, and key:

- same canonical request returns the stored safe response without another mutation or audit event;
- different canonical request returns `409 idempotency_conflict` without mutation.

Different owners or tokens may reuse the same key independently. Records carry a 24-hour retention
target. Until cleanup exists, stored rows remain authoritative. A matching expired row returns
`409 idempotency_expired` without replay, mutation, or another audit event. Replayed successful
reservation creation preserves the original status, safe body, original correlation ID, replay
headers, and the original safe `Location` header.

## Correlation

Clients may send `X-Request-ID` as a UUID. Invalid values are ignored and replaced. Bearer API
responses include a correlation UUID, and successful reservation mutations pass that UUID into the
domain service and audit event.

## Problem Details

Problem responses include:

```json
{
  "type": "https://slaif.local/problems/reservation_conflict",
  "title": "Reservation Conflict",
  "status": 409,
  "code": "reservation_conflict",
  "detail": "The requested time is no longer available.",
  "correlation_id": "00000000-0000-0000-0000-000000000000"
}
```

Stable codes include authentication, scope, validation, idempotency, asset, policy, and reservation
domain errors such as `authentication_required`, `invalid_token`, `insufficient_scope`,
`idempotency_required`, `invalid_idempotency_key`, `idempotency_conflict`,
`idempotency_expired`, `validation_error`, `asset_not_found`, `reservation_not_found`,
`policy_not_configured`, `policy_ambiguous`, `reservation_conflict`,
`reservation_not_cancellable`, `cancellation_cutoff`, and `reservation_not_releasable`.
Work Order 0007 adds `blackout_conflict` for reservation creation attempts that overlap an active
maintenance blackout.

Problem responses do not include ORM exception text, SQL, constraint names, stack traces, token
lookup details, or secret material.

## Endpoints

### `GET /api/v1/`

Anonymous root describing implemented endpoint families.

### `GET /api/v1/me/`

Requires bearer authentication. Returns safe principal and token context:

```json
{
  "principal": {"id": "uuid", "display_name": "Example User"},
  "token": {
    "id": "uuid",
    "display_prefix": "sar_0123456789ab...",
    "scopes": ["reservations:read"],
    "expires_at": "2026-07-01T00:00:00Z",
    "last_used_at": "2026-06-30T12:00:00Z"
  },
  "correlation_id": "uuid"
}
```

Email, staff flags, bearer plaintext, verifier, and pepper are never returned.

### `GET /api/v1/assets/`

Staff-session-only inventory list. Implemented filters are `kind`, `parent`, `tag`, `active`,
`reservable`, and `q`. Pagination is DRF limit/offset with default 50 and maximum 100. Safe fields
exclude physical locators, legacy IDs, raw provenance, and internal notes.

### `GET /api/v1/assets/{asset_id}/`

Staff-session-only inventory detail using the opaque asset UUID.

### `GET /api/v1/assets/{asset_id}/availability/`

Requires bearer authentication and `availability:read`.

Query parameters:

- `date`: ISO local date, optional;
- `days`: integer 1 through 7, optional;
- `timezone`: IANA timezone, optional; defaults to owner timezone.

The response includes an asset summary, display timezone, UTC window start/end, advisory notice,
safe policy minimum duration, privacy-safe busy intervals, and free intervals with latest valid
start. Other users and active maintenance blackouts are labelled only as unavailable; their
identities, email, purposes, cancellation reasons, reservation UUIDs, and blackout reasons are not
exposed. Availability remains advisory.
Missing asset UUIDs return `404 asset_not_found`.

### `GET /api/v1/reservations/`

Requires bearer authentication and `reservations:read`. Returns only the token owner's reservations.
Filters:

- `asset` UUID;
- `status`;
- `lifecycle`;
- `from`;
- `to`;
- `limit`;
- `offset`.

### `POST /api/v1/reservations/`

Requires bearer authentication, `reservations:create`, and `Idempotency-Key`. Request:

```json
{
  "asset_id": "uuid",
  "start_at": "2026-07-01T08:00:00Z",
  "end_at": "2026-07-01T09:00:00Z",
  "purpose": "API job"
}
```

`start_at` and `end_at` must include an explicit UTC offset. Local wall time and DST fold fields are
not accepted by the API. The view calls only `create_reservation(..., source="api")`.

Success returns `201`, `Location`, reservation representation, and `correlation_id`.

### `GET /api/v1/reservations/{reservation_id}/`

Requires bearer authentication and `reservations:read`. Returns only an owned reservation. Other-user
or guessed UUIDs return non-disclosing `404 reservation_not_found`.

### `POST /api/v1/reservations/{reservation_id}/cancel/`

Requires bearer authentication, `reservations:cancel`, owner access, and `Idempotency-Key`. Accepts
optional `reason` up to 1000 characters. Calls only `cancel_reservation(..., source="api")`.
Other-user or guessed UUIDs return non-disclosing `404 reservation_not_found`.

### `POST /api/v1/reservations/{reservation_id}/release/`

Requires bearer authentication, `reservations:release`, owner access, and `Idempotency-Key`. Calls
only `release_reservation(..., source="api")`.
Other-user or guessed UUIDs return non-disclosing `404 reservation_not_found`.

## Deferred

- `/api/v1/tokens/` creation/revocation;
- `/api/v1/me` without trailing slash;
- administrative reservation APIs;
- projects, memberships, group/resource authorization;
- availability rules, blackouts, maintenance calendar API;
- management APIs;
- service-account/admin token issuance;
- API throttling;
- execution gateway integration.
